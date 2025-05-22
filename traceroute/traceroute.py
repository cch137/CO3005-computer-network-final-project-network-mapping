import subprocess
import socket
import json
import requests
import time
import re
import logging
from datetime import datetime
from ipaddress import ip_address, IPv4Address, IPv6Address, ip_network
from concurrent.futures import ThreadPoolExecutor

# Configuration
API_BASE = "https://vector.cch137.link"
LOG_FILE = "log_nodes.jsonl"
MAX_RETRIES = 3
DNS_TIMEOUT = 3  # seconds
REQUEST_TIMEOUT = 10  # seconds
SLEEP_TIME = 60  # seconds between API calls when no domains
DOMAIN_PROCESS_TIMEOUT = 30  # Maximum seconds to spend on a single domain
DNS_RETRY_DELAY = 0.2  # seconds between DNS resolution retries

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("traceroute.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set default socket timeout
socket.setdefaulttimeout(DNS_TIMEOUT)


def extract_ips_from_line(line):
    """
    Extract IP addresses (both IPv4 and IPv6) from a line of traceroute output.

    IPv4 pattern: matches standard dotted-decimal format (e.g., 192.168.1.1)
    IPv6 pattern: matches various IPv6 formats including compressed forms
    """
    # IPv4 pattern
    ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

    # IPv6 pattern - handles various formats of IPv6 addresses
    ipv6_pattern = r"(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"

    # Find all IP addresses in the line
    ipv4_addresses = re.findall(ipv4_pattern, line)
    ipv6_addresses = re.findall(ipv6_pattern, line)

    # Combine the results
    return ipv4_addresses + ipv6_addresses


def is_ipv6(ip_str):
    """Determine if the given IP string is an IPv6 address."""
    try:
        return isinstance(ip_address(ip_str), IPv6Address)
    except ValueError:
        return False


def is_local_ip(ip_str):
    """
    Check if an IP address is a local/private IP address.

    IPv4 private ranges:
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16
    - 127.0.0.0/8 (localhost)

    IPv6 private ranges:
    - ::1/128 (localhost)
    - fc00::/7 (unique local addresses)
    - fe80::/10 (link-local addresses)
    """
    try:
        ip = ip_address(ip_str)

        # Check for IPv4 private ranges
        if isinstance(ip, IPv4Address):
            # Check for private ranges
            private_ranges = [
                ip_network("10.0.0.0/8"),
                ip_network("172.16.0.0/12"),
                ip_network("192.168.0.0/16"),
                ip_network("127.0.0.0/8"),  # localhost
            ]
            return any(ip in private_range for private_range in private_ranges)

        # Check for IPv6 private ranges
        elif isinstance(ip, IPv6Address):
            # Check for localhost
            if ip == ip_address("::1"):
                return True

            # Check for unique local addresses (fc00::/7)
            if ip.exploded.startswith(("fc", "fd")):
                return True

            # Check for link-local addresses (fe80::/10)
            if (
                ip.exploded.startswith("fe8")
                or ip.exploded.startswith("fe9")
                or ip.exploded.startswith("fea")
                or ip.exploded.startswith("feb")
            ):
                return True

        return False
    except ValueError:
        # If the IP address is invalid, assume it's not local
        return False


def should_exclude_domain(domain):
    """
    Check if a domain should be excluded.

    Excludes domains containing "_gateway" or other special keywords.
    """
    if not domain:
        return False

    exclude_keywords = ["_gateway", "localhost", "local"]
    return any(keyword in domain.lower() for keyword in exclude_keywords)


def resolve_domain_to_ips(domain, retries=MAX_RETRIES, max_time=5):
    """
    Resolve a domain to both its IPv4 and IPv6 addresses using socket with timeout and retries.
    Includes a maximum time limit for the entire resolution process.

    Args:
        domain (str): The domain name to resolve
        retries (int): Number of retries if resolution fails
        max_time (int): Maximum time in seconds for the entire resolution process

    Returns:
        tuple: (ipv4_address, ipv6_address) - either can be None if resolution fails
    """
    ipv4 = None
    ipv6 = None
    
    # Set start time to enforce max_time limit
    start_time = time.time()
    
    # Try to resolve IPv4 address with retries
    for attempt in range(retries):
        # Check if we've exceeded the maximum time
        if time.time() - start_time > max_time:
            logger.warning(f"DNS resolution for {domain} exceeded maximum time of {max_time}s")
            break
            
        try:
            ipv4 = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM, 0, socket.AI_ADDRCONFIG)[0][4][0]
            break
        except (socket.gaierror, IndexError, socket.timeout) as e:
            if attempt < retries - 1:
                logger.warning(f"IPv4 resolution attempt {attempt+1}/{retries} failed for {domain}: {e}")
                time.sleep(DNS_RETRY_DELAY)  # Use the configured retry delay
            else:
                logger.error(f"❌ Failed to resolve IPv4 for {domain} after {retries} attempts: {e}")

    # Check if we've exceeded the maximum time before trying IPv6
    if time.time() - start_time <= max_time:
        # Try to resolve IPv6 address with retries
        for attempt in range(retries):
            # Check if we've exceeded the maximum time
            if time.time() - start_time > max_time:
                logger.warning(f"DNS resolution for {domain} exceeded maximum time of {max_time}s")
                break
                
            try:
                ipv6 = socket.getaddrinfo(domain, None, socket.AF_INET6, socket.SOCK_STREAM, 0, socket.AI_ADDRCONFIG)[0][4][0]
                break
            except (socket.gaierror, IndexError, socket.timeout) as e:
                if attempt < retries - 1:
                    logger.warning(f"IPv6 resolution attempt {attempt+1}/{retries} failed for {domain}: {e}")
                    time.sleep(DNS_RETRY_DELAY)  # Use the configured retry delay
                else:
                    logger.error(f"❌ Failed to resolve IPv6 for {domain} after {retries} attempts: {e}")

    return (ipv4, ipv6)


def resolve_reverse_dns(ip, retries=MAX_RETRIES, max_time=3):
    """
    Resolve an IP address to its domain name using reverse DNS lookup with retries.
    Includes a maximum time limit for the entire resolution process.
    
    Args:
        ip (str): The IP address to resolve
        retries (int): Number of retries if resolution fails
        max_time (int): Maximum time in seconds for the entire resolution process
        
    Returns:
        str or None: The resolved domain name or None if resolution fails
    """
    # Set start time to enforce max_time limit
    start_time = time.time()
    
    for attempt in range(retries):
        # Check if we've exceeded the maximum time
        if time.time() - start_time > max_time:
            logger.debug(f"Reverse DNS resolution for {ip} exceeded maximum time of {max_time}s")
            break
            
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, socket.timeout) as e:
            if attempt < retries - 1:
                logger.debug(f"Reverse DNS attempt {attempt+1}/{retries} failed for {ip}: {e}")
                time.sleep(DNS_RETRY_DELAY)  # Use the configured retry delay
            else:
                logger.debug(f"Failed to resolve reverse DNS for {ip} after {retries} attempts")
            
    return None


def parse_traceroute_output(output, is_ipv6=False):
    """
    Parse traceroute output and extract hop information.
    
    Args:
        output (str): The output from traceroute command
        is_ipv6 (bool): Whether this is IPv6 traceroute output
        
    Returns:
        list: A list of hops, where each hop is a list of IPs (or None for timeouts)
    """
    hops = []
    
    # Skip the header line
    for line in output.splitlines()[1:]:
        # Extract hop number
        hop_match = re.match(r'^\s*(\d+)', line)
        if not hop_match:
            continue
            
        # Extract all IPs from the line
        ips = extract_ips_from_line(line)
        
        # Check if this hop has any responding IPs
        if not ips or (len(ips) == 1 and is_local_ip(ips[0])):
            # If no valid IPs found, this is a timeout hop
            hops.append(None)
        else:
            # Filter out local IPs
            valid_ips = [ip for ip in ips if not is_local_ip(ip)]
            if valid_ips:
                hops.append(valid_ips)
            else:
                hops.append(None)
    
    return hops


def run_traceroute(domain):
    """
    Run traceroute to the specified domain and extract the path of IP addresses.
    Attempts IPv4 traceroute first, falls back to IPv6 if IPv4 fails.
    Preserves hop sequence and handles timeouts ('*').
    
    Args:
        domain (str): The domain to trace
        
    Returns:
        list: A list of paths, where each path is a list of hops
    """
    paths = []
    ipv4_addr, ipv6_addr = resolve_domain_to_ips(domain)
    
    # Track if we've successfully run any traceroute
    success = False

    # Run IPv4 traceroute if we have an IPv4 address
    if ipv4_addr:
        logger.info(f"Running IPv4 traceroute to {domain} ({ipv4_addr})")
        for attempt in range(MAX_RETRIES):
            try:
                output = subprocess.check_output(
                    ["traceroute", "-n", "-q", "1", "-w", "1", domain],
                    stderr=subprocess.DEVNULL,
                    timeout=30,  # Add timeout to prevent hanging
                ).decode()

                # Parse the traceroute output
                hops = parse_traceroute_output(output, is_ipv6=False)
                
                # Only add the path if it has at least one valid hop
                if any(hop is not None for hop in hops):
                    paths.append(hops)
                    success = True
                    break  # Exit the retry loop if successful
                else:
                    logger.warning(f"IPv4 traceroute attempt {attempt+1}/{MAX_RETRIES} for {domain} returned no valid hops")
            except subprocess.TimeoutExpired:
                logger.warning(f"IPv4 traceroute attempt {attempt+1}/{MAX_RETRIES} for {domain} timed out")
            except Exception as e:
                logger.error(f"❌ IPv4 Traceroute error for {domain} (attempt {attempt+1}/{MAX_RETRIES}): {e}")
    else:
        logger.warning(f"No IPv4 address resolved for {domain}, skipping IPv4 traceroute")

    # If IPv4 traceroute failed or couldn't be run, try IPv6 if available
    if not success and ipv6_addr:
        logger.info(f"Running IPv6 traceroute to {domain} ({ipv6_addr})")
        for attempt in range(MAX_RETRIES):
            try:
                output = subprocess.check_output(
                    ["traceroute6", "-n", "-q", "1", "-w", "1", domain],
                    stderr=subprocess.DEVNULL,
                    timeout=30,  # Add timeout to prevent hanging
                ).decode()

                # Parse the traceroute output
                hops = parse_traceroute_output(output, is_ipv6=True)
                
                # Only add the path if it has at least one valid hop
                if any(hop is not None for hop in hops):
                    paths.append(hops)
                    success = True
                    break  # Exit the retry loop if successful
                else:
                    logger.warning(f"IPv6 traceroute attempt {attempt+1}/{MAX_RETRIES} for {domain} returned no valid hops")
            except subprocess.TimeoutExpired:
                logger.warning(f"IPv6 traceroute attempt {attempt+1}/{MAX_RETRIES} for {domain} timed out")
            except Exception as e:
                logger.error(f"❌ IPv6 Traceroute error for {domain} (attempt {attempt+1}/{MAX_RETRIES}): {e}")
    elif not success:
        logger.warning(f"No IPv6 address resolved for {domain}, skipping IPv6 traceroute")

    if not success:
        logger.error(f"All traceroute attempts failed for {domain}")
        
    return paths


def extract_nodes(traces, domain):
    """
    Extract nodes from traceroute paths.
    Handles timeouts ('*') correctly and preserves hop sequence.
    Works with IPv4 addresses.
    Excludes local IPs and domains with "_gateway".
    """
    node_dict = {}
    ipv4_addr, _ = resolve_domain_to_ips(domain)

    for hops in traces:
        if not hops or not any(hop is not None for hop in hops):
            continue  # Skip empty traces

        # Find the last valid hop (endpoint)
        endpoint_hop_idx = None
        for i in range(len(hops) - 1, -1, -1):
            if hops[i] is not None:
                endpoint_hop_idx = i
                break
                
        if endpoint_hop_idx is None:
            continue  # No valid hops in this trace
            
        # Process each hop in the trace
        last_valid_hop_idx = None
        last_valid_ip = None
        
        for hop_idx, hop_ips in enumerate(hops):
            if hop_ips is None:
                # This is a timeout hop, skip but remember we had a gap
                continue
                
            # Process each IP at this hop
            for ip in hop_ips:
                # Skip local IPs
                if is_local_ip(ip):
                    continue
                    
                # If this IP is not yet in our dictionary, add it
                if ip not in node_dict:
                    resolved = resolve_reverse_dns(ip)
                    
                    # Skip if the resolved domain should be excluded
                    if should_exclude_domain(resolved):
                        continue
                        
                    domains = []
                    
                    # If this is the endpoint IP (last valid hop in the trace)
                    if hop_idx == endpoint_hop_idx:
                        # Always add the input domain to the endpoint
                        domains.append(domain)
                        # Add the resolved domain if it exists and is different from the input domain
                        if (
                            resolved
                            and resolved != domain
                            and not should_exclude_domain(resolved)
                        ):
                            domains.append(resolved)
                    # For other IPs, just add the resolved domain if it exists and should not be excluded
                    elif resolved and not should_exclude_domain(resolved):
                        domains.append(resolved)
                        
                    node_dict[ip] = {
                        "ip_addr": ip,
                        "domains": domains,
                        "neighbours": set(),
                    }
                
                # Add neighbor relationships based on hop sequence
                if last_valid_hop_idx is not None and last_valid_ip is not None:
                    # Connect this IP with the last valid IP we saw
                    node_dict[ip]["neighbours"].add(last_valid_ip)
                    node_dict[last_valid_ip]["neighbours"].add(ip)
                
                # Update last valid hop info
                last_valid_hop_idx = hop_idx
                last_valid_ip = ip

    # Convert the dictionary to a list of nodes with neighbors as lists
    return [
        {
            "ip_addr": node["ip_addr"],
            "domains": node["domains"],
            "neighbours": list(node["neighbours"]),
        }
        for node in node_dict.values()
    ]


def upload_nodes(nodes, retries=MAX_RETRIES):
    """
    Upload nodes to the API endpoint with retry mechanism.
    
    Args:
        nodes (list): List of node objects to upload
        retries (int): Number of retries if upload fails
        
    Returns:
        bool: True if upload was successful, False otherwise
    """
    for attempt in range(retries):
        try:
            res = requests.post(
                f"{API_BASE}/cn-project/v2/store-nodes", 
                json=nodes, 
                timeout=REQUEST_TIMEOUT
            )
            res.raise_for_status()  # Raise exception for 4XX/5XX responses
            logger.info(f"✅ Upload successful: {res.json()}")
            return True
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Upload attempt {attempt+1}/{retries} timed out ({REQUEST_TIMEOUT}s)")
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ Upload attempt {attempt+1}/{retries} failed: {e}")
        
        # Only sleep between retries, not after the last attempt
        if attempt < retries - 1:
            time.sleep(1)  # Wait before retrying
            
    logger.error(f"❌ Upload failed after {retries} attempts")
    return False


def log_nodes_to_file(nodes):
    """
    Log nodes to a local file with error handling.
    
    Args:
        nodes (list): List of node objects to log
    """
    try:
        with open(LOG_FILE, "a") as f:
            for node in nodes:
                record = {"timestamp": datetime.utcnow().isoformat(), "data": node}
                f.write(json.dumps(record) + "\n")
        logger.debug(f"Logged {len(nodes)} nodes to {LOG_FILE}")
    except Exception as e:
        logger.error(f"Failed to log nodes to file: {e}")


def get_next_domains(retries=MAX_RETRIES):
    """
    Get the next domains to process from the API with retry mechanism.
    
    Args:
        retries (int): Number of retries if API call fails
        
    Returns:
        list: List of domain strings to process
    """
    for attempt in range(retries):
        try:
            res = requests.get(
                f"{API_BASE}/cn-project/v2/next-domains", 
                timeout=REQUEST_TIMEOUT
            )
            res.raise_for_status()  # Raise exception for 4XX/5XX responses
            domains = res.json().get("domains", [])
            if domains:
                logger.info(f"Received {len(domains)} domains to process")
            return domains
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ API request attempt {attempt+1}/{retries} timed out ({REQUEST_TIMEOUT}s)")
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ API request attempt {attempt+1}/{retries} failed: {e}")
        
        # Only sleep between retries, not after the last attempt
        if attempt < retries - 1:
            time.sleep(1)  # Wait before retrying
    
    logger.error(f"❌ Failed to get domains after {retries} attempts")
    return []


def process_domain(domain, timeout=DOMAIN_PROCESS_TIMEOUT):
    """
    Process a single domain - run traceroute, extract nodes, upload and log.
    Includes a timeout to prevent hanging on problematic domains.
    
    Args:
        domain (str): The domain to process
        timeout (int): Maximum time in seconds to spend processing this domain
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Set start time to enforce timeout
    start_time = time.time()
    
    try:
        logger.info(f"\n🌐 Processing {domain}")
        
        # Run traceroute
        traces = run_traceroute(domain)
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > timeout:
            logger.warning(f"⏰ Processing of {domain} timed out after {timeout}s during traceroute")
            return False
            
        if not traces:
            logger.warning(f"⚠️ No valid traces found for {domain}")
            return False

        # Extract nodes
        nodes = extract_nodes(traces, domain)
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > timeout:
            logger.warning(f"⏰ Processing of {domain} timed out after {timeout}s during node extraction")
            return False
            
        if not nodes:
            logger.warning(f"⚠️ No valid nodes extracted for {domain}")
            return False
            
        logger.info(f"📡 Extracted {len(nodes)} nodes for {domain}")
        
        # Upload nodes
        upload_success = upload_nodes(nodes)
        
        # Always log nodes locally even if upload fails
        log_nodes_to_file(nodes)
        
        # Calculate and log total processing time
        total_time = time.time() - start_time
        logger.info(f"⏱️ Total processing time for {domain}: {total_time:.2f}s")
        
        return upload_success
    except Exception as e:
        logger.error(f"❌ Error processing domain {domain}: {e}")
        return False

def main_loop():
    """Main processing loop with improved error handling and parallel processing."""
    logger.info("Starting traceroute network mapping")
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    while True:
        try:
            # Get domains to process
            domains = get_next_domains()
            
            if not domains:
                logger.info(f"💤 No domains received, sleeping {SLEEP_TIME} seconds...")
                time.sleep(SLEEP_TIME)
                consecutive_failures = 0  # Reset failure counter on empty domains
                continue

            # Process domains in parallel
            success_count = 0
            with ThreadPoolExecutor(max_workers=min(4, len(domains))) as executor:
                results = list(executor.map(process_domain, domains))
                success_count = sum(1 for result in results if result)
            
            # Check if we had any successes
            if success_count > 0:
                logger.info(f"✅ Successfully processed {success_count}/{len(domains)} domains")
                consecutive_failures = 0  # Reset failure counter on success
            else:
                logger.warning(f"⚠️ Failed to process any domains in this batch")
                consecutive_failures += 1
                
            # If we've had too many consecutive failures, take a longer break
            if consecutive_failures >= max_consecutive_failures:
                logger.error(f"⚠️ {consecutive_failures} consecutive failures, taking a longer break (5 minutes)")
                time.sleep(300)  # 5 minutes
                consecutive_failures = 0  # Reset after the break
            
            logger.info("⏳ Completed processing round\n")
            
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            consecutive_failures += 1
            time.sleep(10)  # Short sleep after an error


if __name__ == "__main__":
    try:
        logger.info("🚀 Starting traceroute network mapping application")
        main_loop()
    except KeyboardInterrupt:
        logger.info("👋 Application terminated by user")
    except Exception as e:
        logger.critical(f"💥 Fatal error: {e}")
        raise
