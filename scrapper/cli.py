import json
import sys
import argparse
from typing import Optional, List
from rich import print
from .crawler import crawl_site
from .extractor import extract_markdown_items


def main():
    parser = argparse.ArgumentParser(description="Scrape a website into knowledgebase JSON with markdown content.")
    parser.add_argument("url", help="Root URL or a specific section URL, e.g., https://interviewing.io/blog")
    parser.add_argument("--max-pages", type=int, default=200, help="Maximum pages to fetch")
    parser.add_argument("--concurrency", type=int, default=16, help="Concurrent HTTP requests")
    parser.add_argument("--include-patterns", type=str, default="", help="Comma-separated patterns to include")
    parser.add_argument("--exclude-patterns", type=str, default="", help="Comma-separated patterns to exclude")
    parser.add_argument("--output", type=str, help="Output file path for JSON. If omitted, prints to stdout.")
    
    args = parser.parse_args()
    
    # Parse comma-separated patterns
    include_list = [p.strip() for p in args.include_patterns.split(",") if p.strip()] if args.include_patterns else []
    exclude_list = [p.strip() for p in args.exclude_patterns.split(",") if p.strip()] if args.exclude_patterns else []
    
    discovered_urls = crawl_site(
        root_url=args.url,
        max_pages=args.max_pages,
        concurrency=args.concurrency,
        include_patterns=include_list,
        exclude_patterns=exclude_list,
    )
    items = extract_markdown_items(discovered_urls)

    result = {
        "site": args.url,
        "items": items,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[green]Saved[/green] {len(items)} items to {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
