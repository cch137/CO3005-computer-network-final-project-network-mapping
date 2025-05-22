import os
import time
import requests
from urllib.parse import urlparse, urljoin, urlencode, urlunparse, parse_qs
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import tldextract

API_ORIGIN = os.environ.get("API_ORIGIN", "https://vector.cch137.link")
HEADERS = {"Content-Type": "application/json"}

USELESS_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid", "ref", "tracking_id"}

def clean_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    clean_query = {k: v for k, v in query.items() if k not in USELESS_PARAMS}
    new_url = parsed._replace(query=urlencode(clean_query, doseq=True))
    return urlunparse(new_url)

def get_domain(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"

def to_absolute(base_url, link):
    return urljoin(base_url, link)

def extract_links(soup, base_url):
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag.get("href")
        abs_url = to_absolute(base_url, href)
        if abs_url.startswith("http"):
            links.append(clean_url(abs_url))
    return list(set(links))

def fetch_page_data(url):
    cln_url = clean_url(url)
    try:
        print(f"Fetching: {cln_url}")
        start = time.time()
        res = requests.get(url, timeout=10)
        delay_ms = int((time.time() - start) * 1000)

        if res.status_code != 200 or "text/html" not in res.headers.get("Content-Type", ""):
            return {
                "url": cln_url,
                "domain": get_domain(url),
                "title": "HTTP Error or Unreachable",
                "description": "",
                "markdown": "",
                "delay_ms": delay_ms,
                "links": []
            }

        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""

        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        description = desc_tag["content"].strip() if desc_tag and "content" in desc_tag.attrs else ""

        markdown = md(res.text)
        links = extract_links(soup, url)

        return {
            "url": cln_url,
            "domain": get_domain(url),
            "title": title if title else cln_url,
            "description": description,
            "markdown": markdown,
            "delay_ms": delay_ms,
            "links": links
        }

    except Exception as e:
        return {
            "url": cln_url,
            "domain": get_domain(url),
            "title": str(e),
            "description": "",
            "markdown": "",
            "delay_ms": 0,
            "links": []
        }

seed_links = [
    "https://zh.wikipedia.org/wiki/網際網路",
    "https://news.ycombinator.com/",
    "https://www.producthunt.com/",
    "https://www.reddit.com/r/all/"
]

def crawl_urls(url_list):
    result = []
    for url in url_list:
        data = fetch_page_data(url)
        result.append(data)
    return result

def get_next_pages():
    try:
        res = requests.get(f"{API_ORIGIN}/cn-project/next-pages", headers=HEADERS)
        return res.json().get("links", [])
    except Exception as e:
        print("Error getting next pages:", str(e))
        return []

def post_pages(pages):
    try:
        res = requests.post(f"{API_ORIGIN}/cn-project/store-pages", headers=HEADERS, json=pages)
        print("✅ Submitted pages:", res.status_code, res.json())
        return res.ok
    except Exception as e:
        print("❌ Error posting pages:", str(e))
        return False

def run_once_from_api():
    # urls = get_next_pages()
    urls = ['https://www.ncu.edu.tw','https://ce.ncu.edu.tw','https://www.ntu.edu.tw',]
    if not urls:
        print("⚠ No URLs returned from API. Using seed links instead.")
        urls = seed_links.copy()

    results = crawl_urls(urls)
    valid_pages = [page for page in results if page["markdown"] and page["links"]]

    if valid_pages:
        post_pages(valid_pages)
    else:
        print("🛑 No valid pages to submit.")

def is_locked():
    try:
        res = requests.get(f"{API_ORIGIN}/cn-project/lock")
        return res.json().get("lock", False)
    except Exception as e:
        print("🔒 Failed to get lock status:", str(e))
        return False

if __name__ == "__main__":
    while True:
        if is_locked():
            print("⏳ Lock inactive — waiting...")
        else:
            print("🔓 Lock is active — fetching and submitting pages...")
            run_once_from_api()
            break
        time.sleep(10)
