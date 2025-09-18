#!/usr/bin/env python3
"""
Simple test script to verify the scraper works with various websites.
"""

import sys
from pathlib import Path
from scrapper.crawler import crawl_site
from scrapper.extractor import extract_markdown_items

def test_site(url: str, max_pages: int = 10) -> dict:
    """Test scraping a single site."""
    print(f"Testing: {url}")
    
    try:
        # Discover URLs
        urls = crawl_site(url, max_pages=max_pages, concurrency=4, include_patterns=[], exclude_patterns=[])
        print(f"  Found {len(urls)} URLs")
        
        # Extract content
        items = extract_markdown_items(urls)
        print(f"  Extracted {len(items)} items")
        
        # Calculate success rate
        success_rate = len(items) / len(urls) if urls else 0
        
        return {
            "url": url,
            "urls_found": len(urls),
            "items_extracted": len(items),
            "success_rate": success_rate,
            "status": "success"
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        return {
            "url": url,
            "urls_found": 0,
            "items_extracted": 0,
            "success_rate": 0,
            "status": "error",
            "error": str(e)
        }

def main():
    """Test multiple sites."""
    test_sites = [
        "https://quill.co/blog",
        "https://interviewing.io/blog",
        "https://nilmamano.com/blog",
    ]
    
    print("🧪 Testing Knowledge Builder Scraper\n")
    
    results = []
    for site in test_sites:
        result = test_site(site, max_pages=5)
        results.append(result)
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    total_sites = len(results)
    successful_sites = len([r for r in results if r["status"] == "success"])
    avg_success_rate = sum(r["success_rate"] for r in results) / total_sites
    
    print(f"Total sites tested: {total_sites}")
    print(f"Successful sites: {successful_sites}")
    print(f"Average success rate: {avg_success_rate:.2%}")
    print()
    
    for result in results:
        status_emoji = "✅" if result["status"] == "success" else "❌"
        print(f"{status_emoji} {result['url']}")
        print(f"   URLs: {result['urls_found']}, Items: {result['items_extracted']}, Success: {result['success_rate']:.1%}")
        if result["status"] == "error":
            print(f"   Error: {result['error']}")
        print()

if __name__ == "__main__":
    main()
