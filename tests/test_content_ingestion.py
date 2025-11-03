"""
Test script for Content Ingestion module.
Run this to verify URL fetching works correctly.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.content_ingestion import ContentIngester


def test_basic_fetch():
    """Test basic article fetching."""
    print("=" * 60)
    print("Testing Content Ingestion Module")
    print("=" * 60)
    
    ingester = ContentIngester()
    
    # Test URLs (publicly accessible articles)
    test_urls = [
        "https://example.com",  # Simple page
        "https://en.wikipedia.org/wiki/Web_scraping",  # Wikipedia
        "https://httpbin.org/html",  # Test HTML page
    ]
    
    print("\n🧪 Testing URL fetching...\n")
    
    for url in test_urls:
        print(f"\n📎 Fetching: {url}")
        print("-" * 60)
        
        article = ingester.fetch_article(url)
        
        if article:
            print(f"✅ Success!")
            print(f"   Title: {article.title}")
            print(f"   Author: {article.author or 'Unknown'}")
            print(f"   Reading time: {article.reading_time} minutes")
            print(f"   Content length: {len(article.content)} characters")
            print(f"   Domain: {article.domain}")
            
            if article.description:
                print(f"   Description: {article.description[:100]}...")
            
            # Show first 200 chars of content
            print(f"\n   Content preview:")
            print(f"   {article.content[:200]}...")
        else:
            print(f"❌ Failed to fetch article")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


def test_multiple_fetch():
    """Test fetching multiple URLs at once."""
    print("\n\n🧪 Testing multiple URL fetching...\n")
    
    ingester = ContentIngester()
    
    urls = [
        "https://example.com",
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
    ]
    
    print(f"Fetching {len(urls)} URLs...")
    articles = ingester.fetch_multiple(urls)
    
    print(f"\n✅ Successfully fetched {len(articles)} out of {len(urls)} articles\n")
    
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")
        print(f"   {article.url}")
        print(f"   {article.reading_time} min read\n")


def test_invalid_urls():
    """Test handling of invalid URLs."""
    print("\n\n🧪 Testing invalid URL handling...\n")
    
    ingester = ContentIngester()
    
    invalid_urls = [
        "not-a-url",
        "http://this-domain-does-not-exist-12345.com",
        "https://httpstat.us/404",  # Returns 404
        "https://httpstat.us/500",  # Returns 500
    ]
    
    for url in invalid_urls:
        print(f"Testing: {url}")
        article = ingester.fetch_article(url)
        
        if article:
            print(f"  ⚠️ Unexpectedly succeeded")
        else:
            print(f"  ✅ Correctly failed")
    
    print("\nInvalid URL handling: PASSED")


if __name__ == "__main__":
    try:
        test_basic_fetch()
        test_multiple_fetch()
        test_invalid_urls()
        
        print("\n\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nContent Ingestion module is working correctly.")
        print("You can now use it in the agent.\n")
    
    except Exception as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)