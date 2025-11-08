"""
Scheduler Module - Smart delivery timing and queue management.
Analyzes reading patterns and schedules optimal content delivery.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Scheduler:
    """
    Manages intelligent scheduling and delivery of reading content.
    Learns user reading patterns and optimizes delivery timing.
    """
    
    # Default delivery preferences (can be overridden by user preferences)
    DEFAULT_DELIVERY_HOURS = [9, 12, 18, 21]  # 9am, 12pm, 6pm, 9pm
    DEFAULT_MAX_ITEMS_PER_DELIVERY = 5
    DEFAULT_MIN_HOURS_BETWEEN_DELIVERIES = 4
    
    def __init__(self, storage):
        """
        Initialize scheduler with storage backend.
        
        Args:
            storage: Storage instance for database access
        """
        self.storage = storage
        logger.info("Scheduler initialized")
    
    def analyze_reading_patterns(self) -> Dict[str, Any]:
        """
        Analyze user's reading patterns from history.
        
        Returns:
            Dictionary with reading pattern analysis
        """
        logger.info("Analyzing reading patterns")
        
        # Get reading activity
        activity = self.storage.get_recent_activity(limit=100)
        
        if not activity:
            logger.info("No reading activity yet")
            return self._get_default_patterns()
        
        # Extract read events
        read_events = [a for a in activity if a['event_type'] == 'read']
        
        if not read_events:
            return self._get_default_patterns()
        
        # Analyze by hour
        hours = []
        days_of_week = []
        
        for event in read_events:
            try:
                timestamp = datetime.fromisoformat(event['timestamp'])
                hours.append(timestamp.hour)
                days_of_week.append(timestamp.weekday())  # 0=Monday, 6=Sunday
            except Exception as e:
                logger.warning(f"Error parsing timestamp: {e}")
                continue
        
        # Find most common reading hours
        hour_counts = Counter(hours)
        top_hours = [hour for hour, count in hour_counts.most_common(5)]
        
        # Find most common reading days
        day_counts = Counter(days_of_week)
        top_days = [day for day, count in day_counts.most_common(3)]
        
        # Categorize reading times
        reading_times = self._categorize_reading_times(hours)
        
        patterns = {
            'preferred_hours': top_hours or self.DEFAULT_DELIVERY_HOURS,
            'preferred_days': top_days,
            'reading_times': reading_times,
            'total_reads': len(read_events),
            'has_data': True
        }
        
        logger.info(f"Patterns detected: preferred hours={top_hours}, "
                   f"times={reading_times}")
        
        return patterns
    
    def _categorize_reading_times(self, hours: List[int]) -> List[str]:
        """
        Categorize hours into time periods.
        
        Args:
            hours: List of hours (0-23)
            
        Returns:
            List of time period strings
        """
        time_categories = {
            'morning': (6, 11),    # 6am - 11am
            'afternoon': (12, 17),  # 12pm - 5pm
            'evening': (18, 22),    # 6pm - 10pm
            'night': (23, 5)        # 11pm - 5am (wraps around)
        }
        
        category_counts = defaultdict(int)
        
        for hour in hours:
            for category, (start, end) in time_categories.items():
                if category == 'night':
                    if hour >= 23 or hour <= 5:
                        category_counts[category] += 1
                else:
                    if start <= hour <= end:
                        category_counts[category] += 1
        
        # Return categories sorted by frequency
        sorted_categories = sorted(category_counts.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)
        
        return [cat for cat, count in sorted_categories if count > 0]
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """
        Get default reading patterns when no data available.
        
        Returns:
            Default pattern dictionary
        """
        return {
            'preferred_hours': self.DEFAULT_DELIVERY_HOURS,
            'preferred_days': list(range(7)),  # All days
            'reading_times': ['morning', 'evening'],
            'total_reads': 0,
            'has_data': False
        }
    
    def get_next_delivery_time(self) -> datetime:
        """
        Calculate next optimal delivery time based on patterns.
        
        Returns:
            Next delivery datetime
        """
        patterns = self.analyze_reading_patterns()
        preferred_hours = patterns['preferred_hours']
        
        now = datetime.now()
        current_hour = now.hour
        
        # Find next preferred hour
        next_hour = None
        for hour in sorted(preferred_hours):
            if hour > current_hour:
                next_hour = hour
                break
        
        # If no hour today, use first hour tomorrow
        if next_hour is None:
            next_hour = preferred_hours[0]
            next_date = now + timedelta(days=1)
        else:
            next_date = now
        
        # Create datetime for next delivery
        next_delivery = next_date.replace(
            hour=next_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        
        logger.info(f"Next delivery scheduled for: {next_delivery}")
        return next_delivery
    
    def prioritize_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get prioritized reading queue based on multiple factors.
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of prioritized articles (empty list if none)
        """
        logger.info(f"Prioritizing queue (limit={limit})")
        
        # Get all unread articles
        articles = self.storage.get_reading_queue(limit=50)
        
        if not articles:
            return []  # Return empty list instead of None
        
        # Score each article
        scored_articles = []
        for article in articles:
            score = self._calculate_priority_score(article)
            scored_articles.append((score, article))
        
        # Sort by score (highest first)
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N articles
        prioritized = [article for score, article in scored_articles[:limit]]
        
        logger.info(f"Prioritized {len(prioritized)} articles")
        return prioritized
    
    def _calculate_priority_score(self, article: Dict[str, Any]) -> float:
        """
        Calculate priority score for an article.
        
        Args:
            article: Article dictionary
            
        Returns:
            Priority score (higher = more important)
        """
        score = 0.0
        
        # Factor 1: Recency (newer = higher priority)
        try:
            saved_at = datetime.fromisoformat(article['saved_at'])
            days_old = (datetime.now() - saved_at).days
            recency_score = max(0, 10 - days_old)  # Max 10 points, decreases over time
            score += recency_score
        except Exception:
            pass
        
        # Factor 2: Reading time (shorter = higher priority)
        reading_time = article.get('reading_time', 5)
        if reading_time <= 3:
            score += 5  # Quick reads get bonus
        elif reading_time <= 5:
            score += 3
        elif reading_time >= 15:
            score -= 2  # Long reads get penalty (may be intimidating)
        
        # Factor 3: Category preferences (get from user stats)
        stats = self.storage.get_statistics()
        top_category = stats.get('top_category')
        if top_category and article.get('category') == top_category:
            score += 5  # Bonus for favorite category
        
        # Factor 4: Presence of author
        if article.get('author'):
            score += 2  # Slight bonus for articles with author info
        
        # Factor 5: Description quality (longer description = more curated)
        description = article.get('description') or ""
        if len(description) > 100:
            score += 2
        
        return score
    
    def create_digest(self, num_items: int = 5) -> Dict[str, Any]:
        """
        Create a reading digest with prioritized content.
        
        Args:
            num_items: Number of items to include
            
        Returns:
            Digest dictionary with articles grouped by category
        """
        logger.info(f"Creating digest with {num_items} items")
        
        # Get prioritized articles
        articles = self.prioritize_queue(limit=num_items)
        
        if not articles:
            return {
                'items': [],
                'total_reading_time': 0,
                'categories': [],
                'created_at': datetime.now().isoformat()
            }
        
        # Group by category
        by_category = defaultdict(list)
        total_time = 0
        
        for article in articles:
            category = article.get('category', 'Uncategorized')
            by_category[category].append(article)
            total_time += article.get('reading_time', 0)
        
        # Create digest
        digest = {
            'items': articles,
            'total_reading_time': total_time,
            'categories': list(by_category.keys()),
            'by_category': dict(by_category),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Digest created: {len(articles)} items, "
                   f"{total_time} min, {len(by_category)} categories")
        
        return digest
    
    def should_send_digest_now(self) -> bool:
        """
        Check if it's a good time to send a reading digest.
        
        Returns:
            True if should send now, False otherwise
        """
        patterns = self.analyze_reading_patterns()
        preferred_hours = patterns['preferred_hours']
        
        current_hour = datetime.now().hour
        
        # Check if current hour is a preferred reading time
        is_preferred_time = current_hour in preferred_hours
        
        # Check if we haven't sent recently (prevent spam)
        # TODO: Implement last_sent tracking in storage
        # For now, just check preferred hours
        
        logger.info(f"Should send digest now? {is_preferred_time} "
                   f"(current_hour={current_hour}, preferred={preferred_hours})")
        
        return is_preferred_time
    
    def get_recommended_reading_time(self, article: Dict[str, Any]) -> str:
        """
        Recommend best time to read an article based on its characteristics.
        
        Args:
            article: Article dictionary
            
        Returns:
            Recommended time string
        """
        reading_time = article.get('reading_time', 5)
        
        if reading_time <= 2:
            return "Perfect for a quick break"
        elif reading_time <= 5:
            return "Good for coffee break"
        elif reading_time <= 10:
            return "Ideal for lunch break"
        elif reading_time <= 20:
            return "Great for evening reading"
        else:
            return "Weekend deep dive"
    
    def suggest_reading_session(self, available_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Suggest articles that fit within available time.
        
        Args:
            available_minutes: Minutes available for reading
            
        Returns:
            List of articles that fit in the time slot
        """
        logger.info(f"Suggesting reading session for {available_minutes} minutes")
        
        # Get prioritized queue
        articles = self.prioritize_queue(limit=20)
        
        # Select articles that fit in time
        selected = []
        time_used = 0
        
        for article in articles:
            reading_time = article.get('reading_time', 5)
            if time_used + reading_time <= available_minutes:
                selected.append(article)
                time_used += reading_time
        
        logger.info(f"Suggested {len(selected)} articles for {time_used}/{available_minutes} min")
        
        return selected
    
    def get_delivery_schedule(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Generate a delivery schedule for upcoming days.
        
        Args:
            days_ahead: Number of days to schedule
            
        Returns:
            List of scheduled delivery times with content suggestions
        """
        logger.info(f"Generating delivery schedule for {days_ahead} days")
        
        patterns = self.analyze_reading_patterns()
        preferred_hours = patterns['preferred_hours']
        
        schedule = []
        current_date = datetime.now()
        
        for day in range(days_ahead):
            date = current_date + timedelta(days=day)
            
            for hour in preferred_hours[:2]:  # Top 2 preferred hours per day
                delivery_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                if delivery_time > datetime.now():
                    schedule.append({
                        'delivery_time': delivery_time.isoformat(),
                        'hour': hour,
                        'day_of_week': delivery_time.strftime('%A'),
                        'recommended_items': self.DEFAULT_MAX_ITEMS_PER_DELIVERY
                    })
        
        logger.info(f"Generated {len(schedule)} scheduled deliveries")
        return schedule
    
    def get_optimal_batch_size(self) -> int:
        """
        Determine optimal number of articles per delivery based on reading patterns.
        
        Returns:
            Recommended batch size
        """
        stats = self.storage.get_statistics()
        
        # If user reads a lot, increase batch size
        read_percentage = stats.get('read_percentage', 0)
        
        if read_percentage >= 80:
            return 7  # Heavy reader
        elif read_percentage >= 50:
            return 5  # Moderate reader
        elif read_percentage >= 20:
            return 3  # Light reader
        else:
            return 2  # Very light reader
    
    def format_digest_message(self, digest: Dict[str, Any]) -> str:
        """
        Format digest into a user-friendly message.
        
        Args:
            digest: Digest dictionary
            
        Returns:
            Formatted message string
        """
        items = digest['items']
        total_time = digest['total_reading_time']
        
        if not items:
            return "📚 Your reading queue is empty! Add some articles to get started."
        
        message = f"📚 **Your Reading Digest** ({len(items)} articles, {total_time} min)\n\n"
        
        # Group by category
        by_category = digest.get('by_category', {})
        
        for category, articles in by_category.items():
            message += f"**{category}**\n"
            for article in articles:
                message += f"• {article['title']} ({article['reading_time']} min)\n"
                message += f"  {article['url']}\n"
            message += "\n"
        
        # Add reading time suggestion
        if total_time <= 15:
            message += "💡 Perfect for a quick session!"
        elif total_time <= 30:
            message += "💡 Great for your lunch break!"
        else:
            message += "💡 Set aside some time for this one!"
        
        return message
    
    # ==================================================================
    # CALENDAR INTEGRATION (OPTIONAL)
    # ==================================================================
    # If you want to integrate with Google Calendar, you'll need:
    # 1. Google Calendar API credentials
    # 2. OAuth 2.0 setup
    # 3. google-auth and google-api-python-client packages
    #
    # To enable calendar integration:
    # 1. Create a Google Cloud project
    # 2. Enable Google Calendar API
    # 3. Create OAuth 2.0 credentials
    # 4. Download credentials.json
    # 5. Set GOOGLE_CALENDAR_CREDENTIALS_PATH in .env
    # 6. Uncomment and implement the methods below
    # ==================================================================
    
    def check_calendar_availability(self, date: datetime) -> bool:
        """
        Check if user has free time in calendar (optional feature).
        
        NOTE: Requires Google Calendar API setup
        See comments above for setup instructions
        
        Args:
            date: Date to check
            
        Returns:
            True if time is available, False if busy
        """
        # TODO: Implement calendar integration if needed
        # from google.oauth2.credentials import Credentials
        # from googleapiclient.discovery import build
        #
        # CALENDAR_CREDENTIALS_PATH = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH')
        # if not CALENDAR_CREDENTIALS_PATH:
        #     logger.warning("Calendar credentials not configured")
        #     return True  # Assume available
        #
        # # Load credentials and check calendar
        # creds = Credentials.from_authorized_user_file(CALENDAR_CREDENTIALS_PATH)
        # service = build('calendar', 'v3', credentials=creds)
        # events = service.events().list(...).execute()
        # # Check if busy...
        
        logger.debug("Calendar integration not implemented, assuming available")
        return True  # Default: assume time is available