"""
Comprehensive Test Suite - Tests all stages of the agent.
Run this to verify everything works before deployment.
"""
import sys
from pathlib import Path
import json
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root directory
os.chdir(project_root)

print("\n" + "="*80)
print("SMART READ LATER ORGANIZER - COMPREHENSIVE TEST SUITE")
print("="*80)

# Track test results
tests_passed = 0
tests_failed = 0
test_results = []

def test_section(name):
    """Decorator for test sections."""
    print("\n" + "="*80)
    print(f"TESTING: {name}")
    print("="*80)

def test_result(test_name, passed, error=None):
    """Record and display test result."""
    global tests_passed, tests_failed, test_results
    
    if passed:
        tests_passed += 1
        print(f"✅ {test_name}")
        test_results.append(("✅", test_name))
    else:
        tests_failed += 1
        print(f"❌ {test_name}")
        if error:
            print(f"   Error: {error}")
        test_results.append(("❌", test_name, error))


# ============================================================================
# STAGE 1 TESTS - Configuration & A2A Server
# ============================================================================

test_section("STAGE 1: Configuration & A2A Server")

try:
    from config.config import Config
    test_result("Import Config", True)
    
    # Test configuration loading
    try:
        assert Config.AGENT_NAME == "Smart Read Later Organizer"
        assert Config.AGENT_VERSION == "1.0.0"
        test_result("Configuration values", True)
    except AssertionError as e:
        test_result("Configuration values", False, str(e))
    
except Exception as e:
    test_result("Import Config", False, str(e))

try:
    from utils.logger import setup_logger
    logger = setup_logger("test")
    test_result("Logger initialization", True)
except Exception as e:
    test_result("Logger initialization", False, str(e))

try:
    from utils.validators import is_valid_url, extract_urls_from_text, sanitize_url
    
    # Test URL validation
    assert is_valid_url("https://example.com") == True
    assert is_valid_url("not-a-url") == False
    test_result("URL validation", True)
    
    # Test URL extraction
    urls = extract_urls_from_text("Check out https://example.com and https://test.com")
    assert len(urls) == 2
    test_result("URL extraction", True)
    
    # Test URL sanitization
    sanitized = sanitize_url("example.com")
    assert sanitized == "https://example.com"
    test_result("URL sanitization", True)
    
except Exception as e:
    test_result("Validators", False, str(e))

try:
    from modules.a2a_server import A2AServer
    
    def dummy_handler(msg):
        return "test response"
    
    server = A2AServer(dummy_handler)
    test_result("A2A Server initialization", True)
except Exception as e:
    test_result("A2A Server initialization", False, str(e))

try:
    # Check agent_card.json exists and is valid JSON
    agent_card_path = Path("agent_card.json")
    if agent_card_path.exists():
        with open(agent_card_path) as f:
            agent_card = json.load(f)
        
        required_fields = ["name", "url", "version", "provider", "skills"]
        missing = [f for f in required_fields if f not in agent_card]
        
        if missing:
            test_result("Agent Card structure", False, f"Missing fields: {missing}")
        else:
            test_result("Agent Card structure", True)
    else:
        test_result("Agent Card exists", False, "agent_card.json not found")
except Exception as e:
    test_result("Agent Card validation", False, str(e))


# ============================================================================
# STAGE 2 TESTS - Content Ingestion
# ============================================================================

test_section("STAGE 2: Content Ingestion")

try:
    from modules.content_ingestion import ContentIngester, Article
    ingester = ContentIngester()
    test_result("ContentIngester initialization", True)
except Exception as e:
    test_result("ContentIngester initialization", False, str(e))

try:
    # Test fetching a simple page
    print("\n   Fetching test URL (this may take a few seconds)...")
    article = ingester.fetch_article("https://example.com")
    
    if article:
        assert article.url == "https://example.com"
        assert len(article.title) > 0
        assert len(article.content) > 0
        assert article.reading_time > 0
        test_result("Article fetching", True)
        print(f"   Title: {article.title}")
        print(f"   Reading time: {article.reading_time} min")
        print(f"   Content length: {len(article.content)} chars")
    else:
        test_result("Article fetching", False, "Failed to fetch article")
        
except Exception as e:
    test_result("Article fetching", False, str(e))

try:
    # Test Article object
    test_article = Article(
        url="https://test.com",
        title="Test Article",
        content="Test content " * 100,
        reading_time=5
    )
    
    article_dict = test_article.to_dict()
    assert "url" in article_dict
    assert "title" in article_dict
    assert "content" in article_dict
    test_result("Article object conversion", True)
except Exception as e:
    test_result("Article object conversion", False, str(e))

try:
    # Test invalid URL handling
    bad_article = ingester.fetch_article("not-a-url")
    assert bad_article is None
    test_result("Invalid URL handling", True)
except Exception as e:
    test_result("Invalid URL handling", False, str(e))


# ============================================================================
# STAGE 3 TESTS - Storage
# ============================================================================

test_section("STAGE 3: Storage & Database")

try:
    from modules.storage import Storage
    import os
    
    # Use test database
    test_db = "test_integration.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    storage = Storage(db_path=test_db)
    test_result("Storage initialization", True)
except Exception as e:
    test_result("Storage initialization", False, str(e))
    storage = None

if storage:
    try:
        # Test saving article
        test_article_data = {
            'url': 'https://example.com/test1',
            'title': 'Integration Test Article',
            'content': 'Test content for integration testing.',
            'author': 'Test Author',
            'published_date': None,
            'description': 'Test description',
            'reading_time': 3,
            'domain': 'example.com',
            'fetched_at': '2024-01-01T00:00:00'
        }
        
        article_id = storage.save_article(test_article_data)
        assert article_id is not None
        test_result("Save article to database", True)
        
        # Test retrieving article
        retrieved = storage.get_article(article_id)
        assert retrieved is not None
        assert retrieved['title'] == 'Integration Test Article'
        test_result("Retrieve article from database", True)
        
        # Test reading queue
        queue = storage.get_reading_queue()
        assert len(queue) > 0
        test_result("Get reading queue", True)
        
        # Test statistics
        stats = storage.get_statistics()
        assert stats['total_articles'] > 0
        test_result("Get statistics", True)
        print(f"   Total articles: {stats['total_articles']}")
        print(f"   Unread: {stats['unread']}")
        
        # Test categories
        storage.update_article_category(article_id, 'Testing')
        categories = storage.get_all_categories()
        assert len(categories) > 0
        test_result("Category management", True)
        
        # Test mark as read
        storage.mark_as_read(article_id)
        article = storage.get_article(article_id)
        assert article['status'] == 'read'
        test_result("Mark article as read", True)
        
        # Cleanup
        os.remove(test_db)
        
    except Exception as e:
        test_result("Database operations", False, str(e))


# ============================================================================
# INTEGRATION TESTS - Full Agent
# ============================================================================

test_section("INTEGRATION: Full Agent Flow")

try:
    from modules.message_handler import MessageHandler
    handler = MessageHandler()
    test_result("MessageHandler initialization", True)
except Exception as e:
    test_result("MessageHandler initialization", False, str(e))
    handler = None

if handler:
    try:
        # Test help command
        response = handler.handle_message({'text': 'help'})
        assert 'Smart Read Later Organizer' in response
        test_result("Help command", True)
    except Exception as e:
        test_result("Help command", False, str(e))
    
    try:
        # Test URL detection
        response = handler.handle_message({'text': 'https://example.com'})
        assert '✅' in response or 'saved' in response.lower()
        test_result("URL handling integration", True)
        print(f"   Response preview: {response[:100]}...")
    except Exception as e:
        test_result("URL handling integration", False, str(e))
    
    try:
        # Test list command
        response = handler.handle_message({'text': 'list'})
        assert 'Reading Queue' in response or 'empty' in response.lower()
        test_result("List command integration", True)
    except Exception as e:
        test_result("List command integration", False, str(e))
    
    try:
        # Test stats command
        response = handler.handle_message({'text': 'stats'})
        assert 'Stats' in response or 'statistics' in response.lower()
        test_result("Stats command integration", True)
    except Exception as e:
        test_result("Stats command integration", False, str(e))
    
    try:
        # Test categories command
        response = handler.handle_message({'text': 'categories'})
        assert 'Categories' in response or 'categories' in response.lower()
        test_result("Categories command integration", True)
    except Exception as e:
        test_result("Categories command integration", False, str(e))


# ============================================================================
# FINAL RESULTS
# ============================================================================

print("\n" + "="*80)
print("TEST RESULTS SUMMARY")
print("="*80)

print(f"\n✅ Tests Passed: {tests_passed}")
print(f"❌ Tests Failed: {tests_failed}")
print(f"📊 Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")

print("\n" + "-"*80)
print("Detailed Results:")
print("-"*80)

for result in test_results:
    if len(result) == 2:
        status, name = result
        print(f"{status} {name}")
    else:
        status, name, error = result
        print(f"{status} {name}")
        if error:
            print(f"    └─ {error}")

print("\n" + "="*80)

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! The agent is working perfectly!")
    print("="*80)
    print("\n✨ Ready for:")
    print("   • Stage 4: Content Processing (NLP)")
    print("   • Deployment to production")
    print("   • Integration with Telex")
    sys.exit(0)
else:
    print("⚠️  SOME TESTS FAILED - Review errors above")
    print("="*80)
    sys.exit(1)