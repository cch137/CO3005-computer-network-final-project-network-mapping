import requests
import random
import time
import html2text
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from modules.schemas import PageSchema
from typing import List
import traceback

# API base URL (can be overridden during testing)
API_BASE_URL = "https://vector.cch137.link/cn-project"

# Common tracking parameters to remove from URLs
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid"}


def clean_url(url: str) -> str:
    """Clean URL by removing tracking parameters."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    # Remove tracking parameters
    cleaned_params = {k: v for k, v in query_params.items() if k not in TRACKING_PARAMS}
    cleaned_query = urlencode(cleaned_params, doseq=True)
    # Reconstruct the URL without tracking parameters
    cleaned_url = parsed._replace(query=cleaned_query).geturl()
    return cleaned_url


def to_absolute_url(base_url: str, link: str) -> str:
    """Convert relative URLs to absolute URLs."""
    return urljoin(base_url, link)


def fetch_next_pages() -> List[str]:
    """Fetch the next pages to crawl from the API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/next-pages", headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("links", [])
    except Exception as e:
        print(f"Error fetching next pages: {e}")
        return []


def fetch_page(url: str) -> PageSchema | None:
    """Fetch a webpage, process it, and return the required data."""
    start_time = time.time()
    # Extract domain
    domain = urlparse(url).netloc

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        end_time = time.time()
        delay_ms = int((end_time - start_time) * 1000)

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title and description
        title = soup.title.string if soup.title else ""
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and isinstance(meta_desc, Tag) and "content" in meta_desc.attrs:
            description = meta_desc["content"]

        # Convert HTML to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        markdown = h.handle(response.text)

        # Extract all links, convert to absolute URLs, clean, and deduplicate
        links = set()  # Use set for deduplication
        for a_tag in soup.find_all("a", href=True):
            if not isinstance(a_tag, Tag):
                continue
            href = a_tag.get("href")
            if not href:
                continue
            # Convert relative URL to absolute URL
            absolute_url = to_absolute_url(url, str(href))
            cleaned_url = clean_url(absolute_url)
            # Only include HTTP/HTTPS URLs
            if cleaned_url.startswith(("http://", "https://")):
                links.add(cleaned_url)  # Add to set for deduplication

        return PageSchema.model_validate(
            {
                "url": url,
                "domain": domain,
                "title": title,
                "description": description,
                "markdown": markdown,
                "delay_ms": delay_ms,
                "links": list(links),  # Convert set back to list
            }
        )
    except requests.exceptions.RequestException as e:
        # Handle HTTP errors by returning the status code and message as markdown
        end_time = time.time()
        delay_ms = int((end_time - start_time) * 1000)
        status_code = getattr(e.response, "status_code", 0)
        status_message = str(e)
        markdown_error = f"HTTP {status_code} {status_message}"
        domain = urlparse(url).netloc
        return PageSchema.model_validate(
            {
                "url": url,
                "domain": domain,
                "title": url,
                "description": "",
                "markdown": markdown_error,
                "delay_ms": delay_ms,
                "links": [],  # Convert set back to list
            }
        )
    except Exception as e:
        print(f"Error processing page {url}: {e}")
        return None


def submit_pages(pages: List[PageSchema]) -> bool:
    """Submit processed pages to the API."""
    if not pages:
        return False
    try:
        response = requests.post(
            f"{API_BASE_URL}/store-pages",
            headers={"Content-Type": "application/json"},
            json=[
                {
                    "url": str(page.url),
                    "domain": page.domain,
                    "title": page.title,
                    "description": page.description,
                    "markdown": page.markdown,
                    "delay_ms": page.delay_ms,
                    "links": [str(i) for i in page.links],
                }
                for page in pages
            ],
        )
        response.raise_for_status()
        data = response.json()
        return data.get("success", False)
    except Exception as e:
        print(f"Error submitting pages: {e}")
        return False


def main():
    """Main crawler loop."""
    cycle_count = 0
    max_cycles = 1000  # Adjust as needed for long-running execution

    while cycle_count < max_cycles:
        print(f"Starting cycle {cycle_count + 1}")
        try:
            # Fetch URLs to crawl
            urls = fetch_next_pages()

            if not urls:
                print("No pages to crawl, sleeping for 1 hour...")
                time.sleep(3600)  # Sleep for 1 hour if no pages
                continue

            # Process each page
            pages_to_submit = []
            for url in urls:
                print(f"Crawling {url}")
                page_data = fetch_page(url)
                if page_data:
                    pages_to_submit.append(page_data)
                time.sleep(1)  # Sleep between requests to avoid overloading

            # Submit processed pages
            if pages_to_submit:
                success = submit_pages(pages_to_submit)
                print(f"Submitted {len(pages_to_submit)} pages, success: {success}")
            else:
                print("No pages to submit")

            cycle_count += 1
            time.sleep(10)  # Sleep between cycles to reduce load
        except Exception as e:
            print(f"Error in main loop: {e}")
            traceback.print_exc()
            time.sleep(60)  # Sleep for 1 minute on error to prevent rapid looping


if __name__ == "__main__":
    main()
