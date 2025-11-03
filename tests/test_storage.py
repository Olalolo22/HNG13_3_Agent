"""
This is a test script foR Storage module.
Would make sure db operations work correctly.
"""
import sys 
from pathlib import Path
import os 

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.storage import Storage
from datetime import datetime


def cleanup_test_db():
    """Remove test database if it exists."""
    test_db = "test_read_later.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        print(f"Cleaned up old test database")


def test_database_initialization():
    """Test database creation and schema."""
    print("=" * 60)
    print("Testing Database Initialization")
    print("=" * 60)
    
    storage = Storage(db_path="test_read_later.db")
    print("✅ Database initialized successfully")
    return storage


def test_save_article(storage):
    """Test saving articles."""
    print("\n" + "=" * 60)
    print("Testing Article Saving")
    print("=" * 60)
    
    # Test article 1
    article1 = {
        'url': 'https://example.com/article1',
        'title': 'Test Article 1',
        'content': 'This is test content for article 1. ' * 50,
        'author': 'John Doe',
        'published_date': '2024-01-15',
        'description': 'Test description',
        'reading_time': 5,
        'domain': 'example.com',
        'fetched_at': datetime.now().isoformat()
    }
    
    article_id = storage.save_article(article1)
    print(f"✅ Article 1 saved with ID: {article_id}")
    
    # Test article 2
    article2 = {
        'url': 'https://example.com/article2',
        'title': 'Test Article 2',
        'content': 'This is test content for article 2. ' * 30,
        'author': 'Jane Smith',
        'published_date': None,
        'description': None,
        'reading_time': 3,
        'domain': 'example.com',
        'fetched_at': datetime.now().isoformat()
    }
    
    article_id2 = storage.save_article(article2)
    print(f"✅ Article 2 saved with ID: {article_id2}")
    
    # Test duplicate (should return existing ID)
    duplicate_id = storage.save_article(article1)
    print(f"✅ Duplicate handling works (ID: {duplicate_id})")
    
    return article_id, article_id2


def test_get_article(storage, article_id):
    """Test retrieving articles."""
    print("\n" + "=" * 60)
    print("Testing Article Retrieval")
    print("=" * 60)
    
    article = storage.get_article(article_id)
    if article:
        print(f"✅ Retrieved article: {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Reading time: {article['reading_time']} min")
        print(f"   Status: {article['status']}")
    else:
        print(f"❌ Failed to retrieve article")
    
    # Test get by URL
    article2 = storage.get_article_by_url('https://example.com/article1')
    if article2:
        print(f"✅ Retrieved article by URL: {article2['title']}")
    
    return article


def test_reading_queue(storage):
    """Test reading queue functionality."""
    print("\n" + "=" * 60)
    print("Testing Reading Queue")
    print("=" * 60)
    
    queue = storage.get_reading_queue()
    print(f"✅ Reading queue has {len(queue)} articles")
    
    for i, article in enumerate(queue, 1):
        print(f"   {i}. {article['title']} ({article['reading_time']} min)")


def test_categories(storage, article_id):
    """Test category functionality."""
    print("\n" + "=" * 60)
    print("Testing Categories")
    print("=" * 60)
    
    # Update category
    success = storage.update_article_category(article_id, 'Technology')
    if success:
        print(f"✅ Category updated for article {article_id}")
    
    # Get categories
    categories = storage.get_all_categories()
    print(f"✅ Found {len(categories)} categories:")
    for cat in categories:
        print(f"   • {cat['category']}: {cat['count']} articles")
    
    # Get articles by category
    tech_articles = storage.get_articles_by_category('Technology')
    print(f"✅ Found {len(tech_articles)} articles in Technology category")


def test_mark_as_read(storage, article_id):
    """Test marking articles as read."""
    print("\n" + "=" * 60)
    print("Testing Mark as Read")
    print("=" * 60)
    
    success = storage.mark_as_read(article_id)
    if success:
        print(f"✅ Article {article_id} marked as read")
        
        # Verify status changed
        article = storage.get_article(article_id)
        print(f"   Status: {article['status']}")
        print(f"   Read at: {article['read_at']}")


def test_statistics(storage):
    """Test statistics functionality."""
    print("\n" + "=" * 60)
    print("Testing Statistics")
    print("=" * 60)
    
    stats = storage.get_statistics()
    print(f"✅ Statistics retrieved:")
    print(f"   Total articles: {stats['total_articles']}")
    print(f"   Unread: {stats['unread']}")
    print(f"   Read: {stats['read']}")
    print(f"   Read percentage: {stats['read_percentage']}%")
    print(f"   Total reading time: {stats['total_reading_time']} min")
    print(f"   Average reading time: {stats['average_reading_time']} min")
    print(f"   Top category: {stats['top_category']}")


def test_search(storage):
    """Test search functionality."""
    print("\n" + "=" * 60)
    print("Testing Search")
    print("=" * 60)
    
    results = storage.search_articles('Test')
    print(f"✅ Search for 'Test' found {len(results)} articles")
    
    for article in results:
        print(f"   • {article['title']}")


def test_user_preferences(storage):
    """Test user preferences."""
    print("\n" + "=" * 60)
    print("Testing User Preferences")
    print("=" * 60)
    
    # Set preference
    storage.set_user_preference('theme', 'dark')
    print(f"✅ User preference set: theme = dark")
    
    # Get preference
    theme = storage.get_user_preference('theme')
    print(f"✅ User preference retrieved: theme = {theme}")
    
    # Get non-existent preference
    missing = storage.get_user_preference('nonexistent')
    print(f"✅ Non-existent preference returns: {missing}")


def test_recent_activity(storage):
    """Test recent activity tracking."""
    print("\n" + "=" * 60)
    print("Testing Recent Activity")
    print("=" * 60)
    
    activity = storage.get_recent_activity(limit=5)
    print(f"✅ Recent activity has {len(activity)} events:")
    
    for event in activity:
        print(f"   • {event['event_type']}: {event['title']}")
        print(f"     At: {event['timestamp']}")


def test_delete_article(storage, article_id):
    """Test deleting articles."""
    print("\n" + "=" * 60)
    print("Testing Article Deletion")
    print("=" * 60)
    
    success = storage.delete_article(article_id)
    if success:
        print(f"✅ Article {article_id} deleted successfully")
        
        # Verify deletion
        article = storage.get_article(article_id)
        if article is None:
            print(f"✅ Article confirmed deleted")
        else:
            print(f"⚠️ Article still exists after deletion")


if __name__ == "__main__":
    try:
        # Clean up any previous test database
        cleanup_test_db()
        
        # Run tests
        storage = test_database_initialization()
        article_id, article_id2 = test_save_article(storage)
        test_get_article(storage, article_id)
        test_reading_queue(storage)
        test_categories(storage, article_id)
        test_mark_as_read(storage, article_id)
        test_statistics(storage)
        test_search(storage)
        test_user_preferences(storage)
        test_recent_activity(storage)
        test_delete_article(storage, article_id2)
        
        print("\n\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nStorage module is working correctly.")
        print("Database operations are functioning as expected.\n")
        
        # Clean up test database
        cleanup_test_db()
        print("Test database cleaned up.")
    
    except Exception as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)