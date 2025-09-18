import asyncio
import re
import urllib.parse
from dataclasses import dataclass
from typing import Iterable, List, Set, Dict

import httpx
import tldextract
from bs4 import BeautifulSoup
import feedparser


CRAWL_TIMEOUT_SECONDS = 20
DEFAULT_HEADERS = {
    "User-Agent": "AlineScraper/0.1 (+https://example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@dataclass
class CrawlContext:
    root: str
    root_host: str
    allowed_hosts: Set[str]


def normalize_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme:
            return url
        # Drop fragments
        parsed = parsed._replace(fragment="")
        # Normalize scheme/host
        netloc = parsed.netloc.lower()
        scheme = parsed.scheme.lower()
        return urllib.parse.urlunparse((scheme, netloc, parsed.path or "/", parsed.params, parsed.query, ""))
    except Exception:
        return url


def same_site(url: str, ctx: CrawlContext) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    return host in ctx.allowed_hosts or host.endswith("." + ctx.root_host)


async def fetch(client: httpx.AsyncClient, url: str) -> httpx.Response | None:
    try:
        resp = await client.get(url, timeout=CRAWL_TIMEOUT_SECONDS, follow_redirects=True)
        if resp.status_code >= 400:
            return None
        return resp
    except Exception:
        return None


def guess_feeds(base_url: str) -> List[str]:
    # common feed endpoints
    candidates = [
        "/feed",
        "/rss",
        "/rss.xml",
        "/index.xml",
        "/atom.xml",
        "/blog/rss.xml",
        "/blog/index.xml",
    ]
    root = base_url.rstrip('/')
    return [urllib.parse.urljoin(root + '/', c.lstrip('/')) for c in candidates]


def guess_sitemaps(base_url: str) -> List[str]:
    candidates = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap/sitemap.xml",
        "/sitemap-index.xml",
    ]
    root = base_url.rstrip('/')
    return [urllib.parse.urljoin(root + '/', c.lstrip('/')) for c in candidates]


def extract_domain(url: str) -> str:
    ext = tldextract.extract(url)
    parts = [p for p in [ext.domain, ext.suffix] if p]
    return ".".join(parts)


def build_ctx(root_url: str) -> CrawlContext:
    parsed = urllib.parse.urlparse(root_url)
    host = parsed.netloc.lower()
    root_host = extract_domain(root_url)
    allowed_hosts = {host, root_host, f"www.{root_host}"}
    return CrawlContext(root=normalize_url(root_url), root_host=root_host, allowed_hosts=allowed_hosts)


def discover_from_sitemap(base_url: str) -> Set[str]:
    discovered: Set[str] = set()
    try:
        for sm_url in guess_sitemaps(base_url):
            try:
                resp = httpx.get(sm_url, headers=DEFAULT_HEADERS, timeout=10)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "xml")
                # Handle both sitemap and sitemapindex
                for loc in soup.find_all("loc"):
                    if loc.text:
                        discovered.add(normalize_url(loc.text))
            except Exception:
                continue
    except Exception:
        pass
    return discovered


def discover_from_feeds(base_url: str) -> Set[str]:
    urls: Set[str] = set()
    for feed_url in guess_feeds(base_url):
        try:
            parsed = feedparser.parse(feed_url)
            if parsed.bozo:
                continue
            for entry in parsed.entries:
                link = entry.get('link') or entry.get('id')
                if link:
                    urls.add(normalize_url(urllib.parse.urljoin(feed_url, link)))
        except Exception:
            continue
    return urls


def looks_like_article_url(url: str) -> bool:
    # Heuristics for typical content URLs
    patterns = [
        r"/blog/",
        r"/posts?/",
        r"/articles?/",
        r"/guides?/",
        r"/learn/",
        r"/topics",
        r"/news/",
        r"/insights/",
        r"/stories/",
        r"/resources?/",
        r"/case-studies?/",
    ]
    return any(re.search(p, url, flags=re.IGNORECASE) for p in patterns)


def inpage_discover(html: str, base_url: str) -> Set[str]:
    soup = BeautifulSoup(html, "lxml")
    found: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if href.startswith("mailto:") or href.startswith("tel:"):
            continue
        joined = urllib.parse.urljoin(base_url, href)
        found.add(normalize_url(joined))
    return found


async def crawl_bfs(root_url: str, max_pages: int, concurrency: int, include_patterns: List[str], exclude_patterns: List[str]) -> Set[str]:
    ctx = build_ctx(root_url)
    to_visit: asyncio.Queue[str] = asyncio.Queue()
    seen: Set[str] = set()
    results: Set[str] = set()

    # Seed with root
    await to_visit.put(ctx.root)

    # Also seed with sitemap and feed discoveries for depth
    seed_urls = set()
    seed_urls |= discover_from_sitemap(ctx.root)
    seed_urls |= discover_from_feeds(ctx.root)
    for u in list(seed_urls)[:max(100, max_pages // 2)]:
        await to_visit.put(u)

    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True) as client:
        async def worker():
            nonlocal results
            while len(results) < max_pages:
                try:
                    current = await asyncio.wait_for(to_visit.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    break
                if current in seen:
                    to_visit.task_done()
                    continue
                seen.add(current)

                if not same_site(current, ctx):
                    to_visit.task_done()
                    continue

                if any(re.search(p, current) for p in exclude_patterns or []):
                    to_visit.task_done()
                    continue
                
                # Only apply include patterns to URLs we're considering for results
                # Don't filter out URLs during discovery phase

                async with sem:
                    resp = await fetch(client, current)
                if not resp:
                    to_visit.task_done()
                    continue

                ctype = resp.headers.get("content-type", "")
                if "text/html" not in ctype:
                    to_visit.task_done()
                    continue

                html = resp.text
                results.add(current)

                if len(results) >= max_pages:
                    to_visit.task_done()
                    break

                # Enqueue children
                discovered_links = inpage_discover(html, current)
                print(f"Discovered {len(discovered_links)} links from {current}")
                for link in discovered_links:
                    if same_site(link, ctx) and link not in seen:
                        await to_visit.put(link)
                        print(f"  Added to queue: {link}")
                    else:
                        print(f"  Skipped: {link} (same_site={same_site(link, ctx)}, seen={link in seen})")
                to_visit.task_done()

        tasks = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    return results


def crawl_site(root_url: str, max_pages: int, concurrency: int, include_patterns: List[str], exclude_patterns: List[str]) -> List[str]:
    # Build context
    ctx = build_ctx(root_url)
    
    urls_from_sitemap = discover_from_sitemap(root_url)
    urls_from_feeds = discover_from_feeds(root_url)
    seed = list(urls_from_sitemap | urls_from_feeds)

    # BFS crawl to augment
    all_urls: Set[str] = set()
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        crawled = loop.run_until_complete(crawl_bfs(root_url, max_pages, concurrency, include_patterns, exclude_patterns))
        all_urls |= crawled
    finally:
        loop.close()

    # Ensure seed candidates are included, but cap to max_pages
    for u in seed:
        if len(all_urls) >= max_pages:
            break
        all_urls.add(u)

    # If no URLs found, at least try the root URL
    if not all_urls:
        all_urls.add(root_url)

    return sorted(all_urls)
