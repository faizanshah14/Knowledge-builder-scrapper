from __future__ import annotations
import re
import urllib.parse
from typing import List, Dict, Any

import trafilatura
from readability import Document
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import httpx

HEADERS = {
    "User-Agent": "AlineScraper/0.1 (+https://example.com)",
}


def fetch_html(url: str) -> str | None:
    try:
        resp = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=20)
        if resp.status_code >= 400:
            return None
        if "text/html" not in resp.headers.get("content-type", ""):
            return None
        return resp.text
    except Exception:
        return None


def extract_title_from_html(html: str) -> str | None:
    try:
        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)
    except Exception:
        return None
    return None


def html_to_markdown(html: str) -> str:
    # Prefer readability main content, fall back to markdownify of full body
    try:
        doc = Document(html)
        content_html = doc.summary(html_partial=True)
        if content_html:
            return md(content_html, heading_style="ATX").strip()
    except Exception:
        pass
    try:
        soup = BeautifulSoup(html, "lxml")
        body = soup.body or soup
        return md(str(body), heading_style="ATX").strip()
    except Exception:
        return ""


def extract_with_trafilatura(url: str, html: str) -> tuple[str | None, str | None]:
    try:
        downloaded = trafilatura.extract(
            html,
            include_comments=False,
            include_links=False,
            output_format="markdown",
            favor_recall=True,
            with_metadata=True,
            url=url,
        )
        if downloaded:
            # Trafilatura returns markdown already, but keep title detection separate
            title = extract_title_from_html(html) or trafilatura.bare_extraction(html).get("title") if trafilatura.bare_extraction(html) else None
            return title, downloaded.strip()
    except Exception:
        pass
    return None, None


def guess_content_type(url: str, html: str) -> str:
    # Heuristics across technical content types
    url_l = url.lower()
    if any(x in url_l for x in ["/blog/", "/post/", "/posts/", "/article", "/insights", "/news/"]):
        return "blog"
    if any(x in url_l for x in ["/learn/", "/guide", "/guides", "/topics", "/tutorial"]):
        return "other"
    # Could add detectors for substack/anchor/transcripts etc.
    return "other"


def extract_markdown_items(urls: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for url in urls:
        html = fetch_html(url)
        if not html:
            continue
        title, content_md = extract_with_trafilatura(url, html)
        if not content_md:
            # fallback to readability → markdownify
            content_md = html_to_markdown(html)
        title = title or extract_title_from_html(html) or url
        content_type = guess_content_type(url, html)
        if content_md and len(content_md.strip()) > 0:
            items.append({
                "title": title,
                "content": content_md,
                "content_type": content_type,
                "source_url": url,
            })
    return items
