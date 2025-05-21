#!/usr/bin/env python3
import os
import sys
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from pymilvus import SearchResult

from modules.collection import ChunkCollection
from modules.embeddings import text_to_embeddings
from modules.database import get_pg_connection
from modules.logger import logger

# Number of chunks to retrieve in search
MAX_CHUNKS = 5

# Initialize the ChunkCollection with the environment variable
chunks = ChunkCollection(os.getenv("MILVUS_COLLECTION_NAME", "chunks"))


def get_page_by_uuid(page_uuid: str) -> Dict[str, Any]:
    """
    Retrieve page information from the database by UUID.

    Args:
        page_uuid: UUID of the page to retrieve

    Returns:
        Dictionary containing page information or empty dict if not found
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT uuid, url, domain, title, description
                FROM pages
                WHERE uuid = %s
                """,
                (page_uuid,),
            )
            result = cur.fetchone()

            if result:
                uuid, url, domain, title, description = result
                return {
                    "uuid": uuid,
                    "url": url,
                    "domain": domain,
                    "title": title,
                    "description": description,
                }
            return {}
    except Exception as e:
        logger.error(f"Error fetching page with UUID {page_uuid}: {e}")
        return {}
    finally:
        conn.close()


def get_pages_by_uuids(page_uuids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve multiple pages from the database by their UUIDs.

    Args:
        page_uuids: List of page UUIDs to retrieve

    Returns:
        Dictionary mapping page UUIDs to page information
    """
    if not page_uuids:
        return {}

    conn = get_pg_connection()
    result = {}

    try:
        with conn.cursor() as cur:
            placeholders = ", ".join(["%s"] * len(page_uuids))
            cur.execute(
                f"""
                SELECT uuid, url, domain, title, description
                FROM pages
                WHERE uuid IN ({placeholders})
                """,
                tuple(page_uuids),
            )

            for row in cur.fetchall():
                uuid, url, domain, title, description = row
                result[uuid] = {
                    "uuid": uuid,
                    "url": url,
                    "domain": domain,
                    "title": title,
                    "description": description,
                }

        return result
    except Exception as e:
        logger.error(f"Error fetching pages with UUIDs {page_uuids}: {e}")
        return {}
    finally:
        conn.close()


def search_chunks_and_pages(query_text: str, top_k: int = MAX_CHUNKS) -> Dict[str, Any]:
    """
    Search for chunks similar to the query text and group them by page.

    Args:
        query_text: The text to search for
        top_k: Number of top chunks to retrieve (default: MAX_CHUNKS)

    Returns:
        Dictionary containing search results grouped by page
    """
    # Generate embeddings for the query text
    query_embeddings = [i[3] for i in list(text_to_embeddings(query_text))]

    if not query_embeddings:
        logger.error("Failed to generate embeddings for query text")
        return {"pages": [], "total_chunks": 0}

    # Search for similar chunks
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

    results = chunks.collection.search(
        data=query_embeddings,
        anns_field="vector",
        param=search_params,
        limit=top_k,
        output_fields=["chunk_uuid", "page_uuid", "index", "content"],
    )

    if not isinstance(results, SearchResult):
        logger.error("Unexpected result type from search")
        return {"pages": [], "total_chunks": 0}

    # Group chunks by page
    page_chunks = defaultdict(list)
    page_uuids = set()

    # Process search results
    for i, hits in enumerate(results):
        for hit in hits:
            page_uuid = hit.entity.get("page_uuid")
            if page_uuid:
                page_uuids.add(page_uuid)
                page_chunks[page_uuid].append(
                    {
                        "chunk_uuid": hit.entity.get("chunk_uuid"),
                        "index": hit.entity.get("index"),
                        "content": hit.entity.get("content"),
                        "score": 1.0
                        - hit.distance,  # Convert distance to similarity score (0-1)
                    }
                )

    # Get page information for all found pages
    pages_info = get_pages_by_uuids(list(page_uuids))

    # Prepare the final result
    pages_result = []
    for page_uuid, chunks_list in page_chunks.items():
        page_info = pages_info.get(
            page_uuid,
            {
                "uuid": page_uuid,
                "title": "Unknown",
                "url": "Unknown",
                "domain": "Unknown",
                "description": "No description",
            },
        )

        # Sort chunks by score (highest first)
        chunks_list.sort(key=lambda x: x["score"], reverse=True)

        pages_result.append(
            {"page": page_info, "chunks": chunks_list, "chunk_count": len(chunks_list)}
        )

    # Sort pages by number of chunks (most first)
    pages_result.sort(key=lambda x: x["chunk_count"], reverse=True)

    return {
        "pages": pages_result,
        "total_chunks": sum(len(chunks_list) for chunks_list in page_chunks.values()),
    }


def format_search_results(results: Dict[str, Any]) -> str:
    """
    Format search results for display.

    Args:
        results: Search results from search_chunks_and_pages

    Returns:
        Formatted string for display
    """
    if not results["pages"]:
        return "No results found."

    output = []
    output.append(
        f"Found {results['total_chunks']} relevant chunks across {len(results['pages'])} pages.\n"
    )

    for i, page_result in enumerate(results["pages"], 1):
        page = page_result["page"]
        chunks = page_result["chunks"]

        # Page header with metadata
        output.append("=" * 80)
        output.append(f"PAGE {i}: {page['title']}")
        output.append(f"URL: {page['url']}")
        output.append(f"Domain: {page['domain']}")
        if page["description"]:
            output.append(f"Description: {page['description']}")
        output.append(f"Matching Chunks: {len(chunks)}")
        output.append("-" * 80)

        # Chunks with their scores
        for j, chunk in enumerate(chunks, 1):
            output.append(f"Chunk {j} [Score: {chunk['score']:.4f}]")
            output.append(f"{chunk['content']}")
            if j < len(chunks):
                output.append("-" * 40)

    output.append("=" * 80)
    return "\n".join(output)


def main():
    """
    Main function to handle user input and display search results.
    """
    print("Vector Search Tool")
    print("Enter your search query (Ctrl+C to exit):")

    try:
        while True:
            try:
                query = input("> ")
                if not query.strip():
                    continue

                print("Searching...")
                results = search_chunks_and_pages(query)
                print(format_search_results(results))
                print("\nEnter a new search query (Ctrl+C to exit):")

            except KeyboardInterrupt:
                print("\nExiting...")
                break

            except Exception as e:
                logger.error(f"Error during search: {e}")
                print(f"An error occurred: {e}")

    except KeyboardInterrupt:
        print("\nExiting...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
