import requests
import json
import time
from typing import List, Dict, Any, Optional

# Update this if your server runs on a different port
BASE_URL = "https://vector-dev.cch137.link"

# Mock data for testing
mock_pages = [
    {
        "url": "https://example.com",
        "domain": "example.com",
        "title": "Example Domain",
        "description": "This domain is for use in illustrative examples in documents.",
        "markdown": "# Example Domain\n\nThis domain is for use in illustrative examples in documents.",
        "delay_ms": 150,
        "links": ["https://example.org", "https://test.com"],
    },
    {
        "url": "https://example.org",
        "domain": "example.org",
        "title": "Example Organization",
        "description": "This is an example organization website.",
        "markdown": "# Example Organization\n\nWelcome to our organization's website.",
        "delay_ms": 120,
        "links": [
            "https://example.com",
            "https://test.com",
            "https://blog.example.org",
        ],
    },
    {
        "url": "https://test.com",
        "domain": "test.com",
        "title": "Test Website",
        "description": "A website for testing purposes.",
        "markdown": "# Test Website\n\nThis is a website created for testing purposes.",
        "delay_ms": 200,
        "links": ["https://example.com", "https://blog.test.com"],
    },
    {
        "url": "https://blog.example.org",
        "domain": "example.org",
        "title": "Blog | Example Organization",
        "description": "The official blog of Example Organization.",
        "markdown": "# Blog\n\nLatest news and updates from Example Organization.",
        "delay_ms": 180,
        "links": ["https://example.org", "https://example.com"],
    },
    {
        "url": "https://blog.test.com",
        "domain": "test.com",
        "title": "Test Blog",
        "description": "A blog for the Test Website.",
        "markdown": "# Test Blog\n\nArticles and updates related to testing.",
        "delay_ms": 160,
        "links": ["https://test.com", "https://tech.blog.test.com"],
    },
    {
        "url": "https://tech.blog.test.com",
        "domain": "test.com",
        "title": "Tech Blog | Test",
        "description": "Technical articles and tutorials.",
        "markdown": "# Tech Blog\n\nDeep dives into technology and programming.",
        "delay_ms": 210,
        "links": ["https://blog.test.com", "https://test.com"],
    },
    {
        "url": "https://docs.example.com",
        "domain": "example.com",
        "title": "Documentation | Example",
        "description": "Official documentation for Example.",
        "markdown": "# Documentation\n\nComprehensive guides and references.",
        "delay_ms": 230,
        "links": ["https://example.com", "https://api.example.com"],
    },
    {
        "url": "https://api.example.com",
        "domain": "example.com",
        "title": "API Reference | Example",
        "description": "API documentation for developers.",
        "markdown": "# API Reference\n\nEndpoints and usage examples for our API.",
        "delay_ms": 140,
        "links": ["https://docs.example.com", "https://example.com"],
    },
    {
        "url": "https://forum.example.org",
        "domain": "example.org",
        "title": "Community Forum | Example Organization",
        "description": "Discuss and share with the community.",
        "markdown": "# Community Forum\n\nConnect with other users and developers.",
        "delay_ms": 190,
        "links": ["https://example.org", "https://blog.example.org"],
    },
    {
        "url": "https://shop.test.com",
        "domain": "test.com",
        "title": "Shop | Test",
        "description": "Purchase test products and services.",
        "markdown": "# Shop\n\nBrowse our collection of test products.",
        "delay_ms": 170,
        "links": ["https://test.com", "https://support.test.com"],
    },
    {
        "url": "https://support.test.com",
        "domain": "test.com",
        "title": "Support | Test",
        "description": "Get help with Test products and services.",
        "markdown": "# Support Center\n\nFind answers to your questions.",
        "delay_ms": 130,
        "links": [
            "https://test.com/1",
            "https://test.com/2",
            "https://test.com/3",
            "https://test.com",
            "https://shop.test.com",
        ],
    },
]

mock_nodes = [
    {
        "ip_addr": "192.168.1.1",
        "name": "Gateway Router",
        "domains": ["router.local", "blog.test.com"],
        "neighbours": ["192.168.1.2", "192.168.1.3", "8.8.8.8"],
    },
    {
        "ip_addr": "192.168.1.2",
        "name": "Web Server",
        "domains": ["webserver.local", "example.com", "example.org"],
        "neighbours": ["192.168.1.1", "192.168.1.4"],
    },
    {
        "ip_addr": "192.168.1.3",
        "name": "Database Server",
        "domains": ["db.local"],
        "neighbours": ["192.168.1.1", "192.168.1.2"],
    },
    {
        "ip_addr": "192.168.1.4",
        "domains": ["fileserver.local"],
        "neighbours": ["192.168.1.2"],
    },
    {
        "ip_addr": "8.8.8.8",
        "name": "Google DNS",
        "domains": ["dns.google.com"],
        "neighbours": ["192.168.1.1", "8.8.4.4"],
    },
    {
        "ip_addr": "8.8.4.4",
        "name": "Google DNS Backup",
        "domains": ["dns.google.com"],
        "neighbours": ["8.8.8.8"],
    },
]


def test_get_next_pages() -> Dict[str, Any]:
    """
    Tests the GET /cn-project/next-pages endpoint.

    Returns:
        Dict containing the response data or error information.
    """
    try:
        response = requests.get(f"{BASE_URL}/cn-project/next-pages")
        response.raise_for_status()
        result = response.json()
        print(f"Retrieved {len(result.get('links', []))} unvisited URLs")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error in test_get_next_pages: {str(e)}")
        return {"error": str(e)}


def test_get_next_domains() -> Dict[str, Any]:
    """
    Tests the GET /cn-project/next-domains endpoint.

    Returns:
        Dict containing the response data or error information.
    """
    try:
        response = requests.get(f"{BASE_URL}/cn-project/next-domains")
        response.raise_for_status()
        result = response.json()
        print(f"Retrieved {len(result.get('domains', []))} unvisited domains")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error in test_get_next_domains: {str(e)}")
        return {"error": str(e)}


def test_store_pages(pages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Tests the POST /cn-project/store-pages endpoint.

    Args:
        pages: Optional list of page objects to store. If None, uses mock data.

    Returns:
        Dict containing the response data or error information.
    """
    if pages is None:
        pages = mock_pages

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{BASE_URL}/cn-project/store-pages",
            headers=headers,
            data=json.dumps(pages),
        )
        response.raise_for_status()
        result = response.json()
        print(f"Stored {len(pages)} pages successfully")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error in test_store_pages: {str(e)}")
        if hasattr(e.response, "text"):
            if e.response:
                print(f"Response text: {e.response.text}")
            else:
                print("Response text is empty")
        return {"error": str(e)}


def test_store_nodes(nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Tests the POST /cn-project/store-nodes endpoint.

    Args:
        nodes: Optional list of node objects to store. If None, uses mock data.

    Returns:
        Dict containing the response data or error information.
    """
    if nodes is None:
        nodes = mock_nodes

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{BASE_URL}/cn-project/store-nodes",
            headers=headers,
            data=json.dumps(nodes),
        )
        response.raise_for_status()
        result = response.json()
        print(f"Stored {len(nodes)} nodes successfully")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error in test_store_nodes: {str(e)}")
        if hasattr(e.response, "text"):
            if e.response:
                print(f"Response text: {e.response.text}")
            else:
                print("Response text is empty")
        return {"error": str(e)}


def test_full_workflow():
    """
    Tests the complete workflow:
    1. Store nodes
    2. Store pages
    3. Get next domains
    4. Get next pages

    This simulates a full cycle of the application.
    """
    print("============ Testing Full Workflow ============")

    print("\n1. Storing nodes...")
    test_store_nodes()

    print("\n2. Storing pages...")
    test_store_pages()

    print("\n3. Getting next domains...")
    test_get_next_domains()

    print("\n4. Getting next pages...")
    test_get_next_pages()

    print("\n============ Full Workflow Test Complete ============")


def test_sequential_page_retrieval(iterations: int = 3, delay: int = 2):
    """
    Tests sequential retrieval of pages over multiple iterations.

    Args:
        iterations: Number of times to request next pages
        delay: Seconds to wait between requests
    """
    print(
        f"============ Testing Sequential Page Retrieval ({iterations} iterations) ============"
    )

    for i in range(iterations):
        print(f"\nIteration {i+1}:")
        result = test_get_next_pages()

        links = result.get("links", [])
        if not links:
            print("No more pages to retrieve")

        if i < iterations - 1:
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)

    print("\n============ Sequential Page Retrieval Test Complete ============")


def test_content_variations():
    """
    Tests the store_pages endpoint with various content types and edge cases.
    """
    print("============ Testing Content Variations ============")

    # Test with minimum required fields
    minimal_pages = [
        {
            "url": "https://minimal.example.com",
            "domain": "minimal.example.com",
            "title": "Minimal Page",
            "description": "",
            "markdown": "",
            "delay_ms": 100,
            "links": [],
        }
    ]

    # Test with very long content
    long_content = "# " + "Very Long Title\n\n" + ("Lorem ipsum " * 500)
    long_pages = [
        {
            "url": "https://long.example.com",
            "domain": "long.example.com",
            "title": "Very Long Page",
            "description": "This page has extremely long content.",
            "markdown": long_content,
            "delay_ms": 300,
            "links": ["https://example.com"],
        }
    ]

    # Test with special characters
    special_pages = [
        {
            "url": "https://special.example.com",
            "domain": "special.example.com",
            "title": "Special Characters: 汉字 • ñ • こんにちは • 😀",
            "description": "This page contains special characters and emojis 🌟",
            "markdown": "# Special Characters\n\n日本語とChinese和English混合。\n\n* Item 1 ✅\n* Item 2 🔍\n* Item 3 🌍",
            "delay_ms": 120,
            "links": ["https://example.com"],
        }
    ]

    print("\n1. Testing with minimal content...")
    test_store_pages(minimal_pages)

    print("\n2. Testing with very long content...")
    test_store_pages(long_pages)

    print("\n3. Testing with special characters...")
    test_store_pages(special_pages)

    print("\n============ Content Variations Test Complete ============")


def test_error_handling():
    """
    Tests error handling by sending invalid requests to the API endpoints.
    """
    print("============ Testing Error Handling ============")

    # Test invalid content type
    try:
        print("\n1. Testing invalid content type...")
        response = requests.post(
            f"{BASE_URL}/cn-project/store-pages",
            headers={"Content-Type": "text/plain"},
            data="This is not JSON",
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

    # Test invalid JSON format
    try:
        print("\n2. Testing invalid JSON format...")
        response = requests.post(
            f"{BASE_URL}/cn-project/store-pages",
            headers={"Content-Type": "application/json"},
            data="This is not valid JSON",
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

    # Test missing required fields
    try:
        print("\n3. Testing missing required fields...")
        invalid_pages = [
            {"url": "https://missing.example.com"}
        ]  # Missing other required fields
        response = requests.post(
            f"{BASE_URL}/cn-project/store-pages",
            headers={"Content-Type": "application/json"},
            data=json.dumps(invalid_pages),
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

    print("\n============ Error Handling Test Complete ============")


if __name__ == "__main__":
    # Uncomment the functions you want to test

    # Basic endpoint tests
    # test_get_next_pages()
    # test_get_next_domains()
    # test_store_pages()
    # test_store_nodes()

    # Advanced tests
    # test_full_workflow()
    # test_sequential_page_retrieval()
    # test_content_variations()
    # test_error_handling()

    # Or run all tests
    print("Running all tests...")
    # test_store_nodes()
    # test_store_pages()
    # test_get_next_domains()
    # test_get_next_pages()
    # test_full_workflow()
    # test_sequential_page_retrieval(iterations=2)
    # test_content_variations()
    # test_error_handling()
