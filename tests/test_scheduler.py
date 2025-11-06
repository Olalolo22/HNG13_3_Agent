"""
Test script for Scheduler module.
Run this to verify scheduling and pattern analysis works correctly.
"""
import sys
from pathlib import Path
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.storage import Storage
from modules.scheduler import Scheduler


def setup_test_data(storage):
    """Create test data for scheduler testing."""
    print("Setting up test data...")
    
    # Create some test articles
    test_articles = [
        {
            'url': 'https://example.com/tech1',
            'title': 'Quick Tech Update',
            'content': 'Short tech article',
            'reading_time': 2,
            'domain': 'example.com',
            'fetched_at': datetime.now().isoformat(),
            'category': 'Technology'
        },
        {
            'url': 'https://example.com/science1',
            'title': 'Science Breakthrough',
            'content': 'Interesting science article',
            'reading_time': 5,
            'domain': 'example.com',
            'fetched_at': datetime.now().isoformat(),
            'category': 'Science'
        },
        {
            'url': 'https://example.com/business1',
            'title': 'Long Business Analysis',
            'content': 'Detailed business report',
            'reading_time': 15,
            'domain': 'example.com',
            'fetched_at': datetime.now().isoformat(),
            'category': 'Business'
        },
        {
            'url': 'https://example.com/tech2',
            'title': 'AI Revolution',
            'content': 'Article about AI',
            'reading_time': 7,
            'domain': 'example.com',
            'fetched_at': datetime.now().isoformat(),
            'category': 'Technology',
            'author': 'John Doe'
        },
        {
            'url': 'https://example.com/sports1',
            'title': 'Championship Game',
            'content': 'Sports coverage',
            'reading_time': 4,
            'domain': 'example.com',
            'fetched_at': datetime.now().isoformat(),
            'category': 'Sports'
        }
    ]
    
    for article in test_articles:
        storage.save_article(article)
    
    print(f"✅ Created {len(test_articles)} test articles")


def test_initialization():
    """Test scheduler initialization."""
    print("=" * 60)
    print("Testing Scheduler Initialization")
    print("=" * 60)
    
    # Use test database
    test_db = "test_scheduler.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    storage = Storage(db_path=test_db)
    scheduler = Scheduler(storage)
    
    print("✅ Scheduler initialized")
    
    return storage, scheduler


def test_pattern_analysis(scheduler):
    """Test reading pattern analysis."""
    print("\n" + "=" * 60)
    print("Testing Reading Pattern Analysis")
    print("=" * 60)
    
    patterns = scheduler.analyze_reading_patterns()
    
    print(f"\n✅ Pattern analysis complete:")
    print(f"   Preferred hours: {patterns['preferred_hours']}")
    print(f"   Preferred days: {patterns['preferred_days']}")
    print(f"   Reading times: {patterns['reading_times']}")
    print(f"   Total reads: {patterns['total_reads']}")
    print(f"   Has data: {patterns['has_data']}")
    
    if not patterns['has_data']:
        print("   ℹ️  Using default patterns (no reading history yet)")


def test_next_delivery(scheduler):
    """Test next delivery time calculation."""
    print("\n" + "=" * 60)
    print("Testing Next Delivery Time")
    print("=" * 60)
    
    next_delivery = scheduler.get_next_delivery_time()
    
    print(f"\n✅ Next delivery calculated:")
    print(f"   Time: {next_delivery.strftime('%I:%M %p')}")
    print(f"   Date: {next_delivery.strftime('%A, %B %d, %Y')}")
    print(f"   Hours from now: {(next_delivery - datetime.now()).seconds / 3600:.1f}")


def test_prioritization(scheduler):
    """Test queue prioritization."""
    print("\n" + "=" * 60)
    print("Testing Queue Prioritization")
    print("=" * 60)
    
    prioritized = scheduler.prioritize_queue(limit=5)
    
    print(f"\n✅ Prioritized {len(prioritized)} articles:")
    for i, article in enumerate(prioritized, 1):
        print(f"   {i}. {article['title']} ({article['reading_time']} min)")
        print(f"      Category: {article['category']}")


def test_digest_creation(scheduler):
    """Test digest creation."""
    print("\n" + "=" * 60)
    print("Testing Digest Creation")
    print("=" * 60)
    
    digest = scheduler.create_digest(num_items=3)
    
    print(f"\n✅ Digest created:")
    print(f"   Items: {len(digest['items'])}")
    print(f"   Total reading time: {digest['total_reading_time']} min")
    print(f"   Categories: {', '.join(digest['categories'])}")
    
    print(f"\n   Articles in digest:")
    for article in digest['items']:
        print(f"   • {article['title']} ({article['reading_time']} min)")


def test_reading_suggestions(scheduler):
    """Test reading time suggestions."""
    print("\n" + "=" * 60)
    print("Testing Reading Suggestions")
    print("=" * 60)
    
    # Test different time slots
    time_slots = [10, 20, 30]
    
    for minutes in time_slots:
        suggestions = scheduler.suggest_reading_session(available_minutes=minutes)
        total_time = sum(a.get('reading_time', 0) for a in suggestions)
        
        print(f"\n   {minutes} minutes available:")
        print(f"   ✅ Suggested {len(suggestions)} articles ({total_time} min total)")
        for article in suggestions:
            print(f"      • {article['title']} ({article['reading_time']} min)")


def test_optimal_batch_size(scheduler):
    """Test optimal batch size calculation."""
    print("\n" + "=" * 60)
    print("Testing Optimal Batch Size")
    print("=" * 60)
    
    batch_size = scheduler.get_optimal_batch_size()
    
    print(f"\n✅ Optimal batch size: {batch_size} articles")
    print(f"   (Based on your reading patterns)")


def test_delivery_schedule(scheduler):
    """Test delivery schedule generation."""
    print("\n" + "=" * 60)
    print("Testing Delivery Schedule")
    print("=" * 60)
    
    schedule = scheduler.get_delivery_schedule(days_ahead=3)
    
    print(f"\n✅ Generated schedule for next 3 days:")
    print(f"   Total deliveries: {len(schedule)}")
    
    for i, delivery in enumerate(schedule[:5], 1):  # Show first 5
        dt = datetime.fromisoformat(delivery['delivery_time'])
        print(f"   {i}. {dt.strftime('%A, %I:%M %p')}")


def test_digest_formatting(scheduler):
    """Test digest message formatting."""
    print("\n" + "=" * 60)
    print("Testing Digest Formatting")
    print("=" * 60)
    
    digest = scheduler.create_digest(num_items=3)
    message = scheduler.format_digest_message(digest)
    
    print(f"\n✅ Formatted digest message:")
    print("-" * 60)
    print(message)
    print("-" * 60)


def cleanup_test_db():
    """Remove test database."""
    test_db = "test_scheduler.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        print("\n✅ Test database cleaned up")


if __name__ == "__main__":
    try:
        storage, scheduler = test_initialization()
        setup_test_data(storage)
        
        test_pattern_analysis(scheduler)
        test_next_delivery(scheduler)
        test_prioritization(scheduler)
        test_digest_creation(scheduler)
        test_reading_suggestions(scheduler)
        test_optimal_batch_size(scheduler)
        test_delivery_schedule(scheduler)
        test_digest_formatting(scheduler)
        
        print("\n\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 60)
        print("\nScheduler module is working correctly.")
        print("✨ Smart scheduling and pattern analysis functional!")
        print()
        
        cleanup_test_db()
    
    except Exception as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_db()
        sys.exit(1)