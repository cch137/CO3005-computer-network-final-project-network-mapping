from typing import List, Dict
from .schemas import PageSchema, NodeSchema
from .constants import PG_USER, PG_PASSWORD
from .logger import logger
import psycopg2
from psycopg2.extras import execute_values  # Added import for execute_values


def get_pg_connection():
    return psycopg2.connect(
        host="localhost",
        database="se",
        user=PG_USER,
        password=PG_PASSWORD,
    )


def insert_nodes(nodes: List[NodeSchema]):
    """
    Insert or update multiple node records in batch.
    Args:
        nodes: List of NodeSchema instances.
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            # Using execute_values for batch insertion
            execute_values(
                cur,
                """
                INSERT INTO nodes (ip_addr, name, domains, neighbours)
                VALUES %s
                ON CONFLICT (ip_addr) DO UPDATE SET
                    name = COALESCE(EXCLUDED.name, nodes.name),
                    domains = ARRAY(
                        SELECT DISTINCT UNNEST(nodes.domains || EXCLUDED.domains)
                    ),
                    neighbours = ARRAY(
                        SELECT DISTINCT UNNEST(nodes.neighbours || EXCLUDED.neighbours)
                    )
                """,
                [
                    (
                        str(node.ip_addr),  # IPvAnyAddress to str
                        node.name,
                        node.domains,
                        node.neighbours,
                    )
                    for node in nodes
                ],
                fetch=True,
            )
        conn.commit()
        logger.info(f"Successfully inserted or updated {len(nodes)} nodes")
    except Exception as e:
        logger.error(f"Error inserting nodes: {e}")
        conn.rollback()
    finally:
        conn.close()


def insert_pages(pages: List[PageSchema]) -> Dict[str, PageSchema]:
    """
    Insert or update multiple page records in batch and return a dictionary mapping UUIDs to PageSchema instances.
    Args:
        pages: List of PageSchema instances.
    Returns:
        Dictionary with UUIDs (as strings) as keys and corresponding PageSchema instances as values.
    """
    conn = get_pg_connection()
    result = {}
    try:
        with conn.cursor() as cur:
            # Create a mapping of URLs to pages
            url_to_page = {str(page.url): page for page in pages}

            # Using execute_values with a RETURNING clause
            execute_result = execute_values(
                cur,
                """
                INSERT INTO pages (url, domain, title, description, delay_ms, links)
                VALUES %s
                ON CONFLICT (url) DO UPDATE SET
                    domain = EXCLUDED.domain,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    delay_ms = EXCLUDED.delay_ms,
                    links = EXCLUDED.links
                RETURNING uuid, url
                """,
                [
                    (
                        str(page.url),
                        page.domain,
                        page.title,
                        page.description,
                        page.delay_ms,
                        [str(link) for link in page.links],  # HttpUrl to str
                    )
                    for page in pages
                ],
                fetch=True,  # This will return the results
            )

            # Process the returned rows
            for row in execute_result:
                uuid, url = row
                if url in url_to_page:
                    result[uuid] = url_to_page[url]

        conn.commit()
        logger.info(f"Successfully inserted or updated {len(pages)} pages")
        return result
    except Exception as e:
        logger.error(f"Error inserting pages: {e}")
        conn.rollback()
        return {}
    finally:
        conn.close()


def get_top_unvisited_urls(limit: int = 10):
    """
    Retrieve top URLs that are referenced most in pages.links
    but have not been visited yet (not recorded in pages.url).

    Args:
        limit (int): Number of top URLs to return.

    Returns:
        List of URLs (not tuples).
    """
    sql = """
        WITH all_links AS (
            SELECT unnest(links) AS link_url
            FROM pages
        ), link_counts AS (
            SELECT link_url, COUNT(*) AS cnt
            FROM all_links
            GROUP BY link_url
        )
        SELECT link_url
        FROM link_counts
        WHERE link_url NOT IN (SELECT url FROM pages)
        ORDER BY cnt DESC
        LIMIT %s;
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            results = [row[0] for row in cur.fetchall()]  # Extract just the URLs
        logger.info(f"Retrieved {len(results)} top unvisited URLs")
        return results
    except Exception as e:
        logger.error(f"Error fetching top unvisited URLs: {e}")
        return []
    finally:
        conn.close()


def get_top_unvisited_domains(limit: int = 10):
    """
    Retrieve top domains that are referenced most in pages.links
    but have not been visited yet (not recorded in nodes.domains).

    Args:
        limit (int): Number of top domains to return.

    Returns:
        List of domains (not tuples).
    """
    sql = """
        WITH all_links AS (
            SELECT unnest(links) AS link_url
            FROM pages
        ), link_domains AS (
            SELECT DISTINCT link_url,
                split_part(split_part(link_url, '://', 2), '/', 1) AS domain
            FROM all_links
        ), domain_counts AS (
            SELECT domain, COUNT(*) AS cnt
            FROM link_domains
            GROUP BY domain
        )
        SELECT domain
        FROM domain_counts
        WHERE domain NOT IN (
            SELECT unnest(domains) FROM nodes
        )
        ORDER BY cnt DESC
        LIMIT %s;
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            results = [row[0] for row in cur.fetchall()]  # Extract just the domains
        logger.info(f"Retrieved {len(results)} top unvisited domains")
        return results
    except Exception as e:
        logger.error(f"Error fetching top unvisited domains: {e}")
        return []
    finally:
        conn.close()
