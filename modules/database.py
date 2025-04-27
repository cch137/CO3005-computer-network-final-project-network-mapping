from typing import List, Dict
from psycopg2.extras import execute_values
from .schemas import PageSchema, NodeSchema
from .constants import PG_USER, PG_PASSWORD
import psycopg2


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
            sql = """
            INSERT INTO nodes (ip_addr, name, domains, neighbours)
            VALUES %s
            ON CONFLICT (ip_addr) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, nodes.name),
                domains = ARRAY(
                    SELECT DISTINCT UNNEST(nodes.domains || EXCLUDED.domains)
                ),
                neighbours = ARRAY(
                    SELECT DISTINCT UNNEST(nodes.neighbours || EXCLUDED.neighbours)
                );
            """
            values = [
                (
                    str(node.ip_addr),  # IPvAnyAddress 轉成 str
                    node.name,
                    node.domains,
                    node.neighbours,
                )
                for node in nodes
            ]
            execute_values(cur, sql, values)
        conn.commit()
    except Exception as e:
        print("Error inserting nodes:", e)
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
            sql = """
            INSERT INTO pages (url, domain, title, description,
                               markdown, delay_time, links)
            VALUES %s
            ON CONFLICT (url) DO UPDATE SET
                domain = EXCLUDED.domain,
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                markdown = EXCLUDED.markdown,
                delay_time = EXCLUDED.delay_time,
                links = EXCLUDED.links
            RETURNING uuid, url;
            """
            values = [
                (
                    str(page.url),
                    page.domain,
                    page.title,
                    page.description,
                    page.markdown,
                    page.delay_time,
                    [str(link) for link in page.links],  # HttpUrl 轉成 str
                )
                for page in pages
            ]
            # 執行批量插入並獲取回傳的 UUID 和 URL
            execute_values(cur, sql, values, fetch=True)
            # 從 cursor 中提取 UUID 和 URL
            for uuid, url in cur.fetchall():
                # 找到對應的 PageSchema 物件
                for page in pages:
                    if str(page.url) == url:
                        result[uuid] = page
                        break
        conn.commit()
        return result
    except Exception as e:
        print("Error inserting pages:", e)
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
        List of tuples: [(url, count), ...]
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
        SELECT link_url, cnt
        FROM link_counts
        WHERE link_url NOT IN (SELECT url FROM pages)
        ORDER BY cnt DESC
        LIMIT %s;
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            results = cur.fetchall()
        return results
    except Exception as e:
        print("Error fetching top unvisited URLs:", e)
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
        List of tuples: [(domain, count), ...]
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
        SELECT domain, cnt
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
            results = cur.fetchall()
        return results
    except Exception as e:
        print("Error fetching top unvisited domains:", e)
        return []
    finally:
        conn.close()
