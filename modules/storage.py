"""
Storage Module - SQLite database management for articles and user data.
"""
import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from utils.logger import setup_logger
from config.config import Config

logger = setup_logger(__name__)


class Storage:
    """Manages SQLite database for storing articles and user preferences."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize storage with database connection.
        
        Args:
            db_path: Path to SQLite database file (default from config)
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_database_directory()
        self._init_database()
        logger.info(f"Storage initialized with database: {self.db_path}")
    
    def _ensure_database_directory(self):
        """Create database directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)  # 30 second timeout
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    author TEXT,
                    published_date TEXT,
                    description TEXT,
                    reading_time INTEGER NOT NULL,
                    domain TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    saved_at TEXT NOT NULL,
                    status TEXT DEFAULT 'unread',
                    category TEXT DEFAULT 'Uncategorized',
                    tags TEXT,
                    read_at TEXT,
                    notes TEXT
                )
            ''')
            
            # Create indexes for common queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_articles_status 
                ON articles(status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_articles_category 
                ON articles(category)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_articles_saved_at 
                ON articles(saved_at DESC)
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Reading statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
            ''')
            
            logger.info("Database schema initialized")
    
    def save_article(self, article_data: Dict[str, Any]) -> Optional[int]:
        """
        Save an article to the database.
        
        Args:
            article_data: Dictionary containing article data
            
        Returns:
            Article ID if saved successfully, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if article already exists
                cursor.execute('SELECT id FROM articles WHERE url = ?', 
                             (article_data['url'],))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"Article already exists: {article_data['url']}")
                    return existing['id']
                
                # Insert new article
                cursor.execute('''
                    INSERT INTO articles (
                        url, title, content, author, published_date,
                        description, reading_time, domain, fetched_at, saved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data['url'],
                    article_data['title'],
                    article_data['content'],
                    article_data.get('author'),
                    article_data.get('published_date'),
                    article_data.get('description'),
                    article_data['reading_time'],
                    article_data['domain'],
                    article_data['fetched_at'],
                    datetime.now().isoformat()
                ))
                
                article_id = cursor.lastrowid
                logger.info(f"Article saved with ID {article_id}: {article_data['title']}")
                
                # Log save event (in same transaction)
                cursor.execute('''
                    INSERT INTO reading_stats (article_id, event_type, timestamp, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (article_id, 'saved', datetime.now().isoformat(), None))
                
                return article_id
        
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error saving article: {e}")
            return None
        except Exception as e:
            logger.error(f"Error saving article: {e}", exc_info=True)
            return None
    
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an article by ID.
        
        Args:
            article_id: Article ID
            
        Returns:
            Article dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get an article by URL.
        
        Args:
            url: Article URL
            
        Returns:
            Article dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles WHERE url = ?', (url,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_reading_queue(self, limit: int = 50, status: str = 'unread') -> List[Dict[str, Any]]:
        """
        Get articles in reading queue.
        
        Args:
            limit: Maximum number of articles to return
            status: Article status filter (default: 'unread')
            
        Returns:
            List of article dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM articles 
                WHERE status = ? 
                ORDER BY saved_at DESC 
                LIMIT ?
            ''', (status, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_articles_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get articles by category.
        
        Args:
            category: Category name
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM articles 
                WHERE category = ? 
                ORDER BY saved_at DESC 
                LIMIT ?
            ''', (category, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories with article counts.
        
        Returns:
            List of dictionaries with category and count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM articles 
                GROUP BY category 
                ORDER BY count DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_as_read(self, article_id: int) -> bool:
        """
        Mark an article as read.
        
        Args:
            article_id: Article ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE articles 
                    SET status = 'read', read_at = ? 
                    WHERE id = ?
                ''', (datetime.now().isoformat(), article_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Article {article_id} marked as read")
                    self._log_event(article_id, 'read')
                    return True
                return False
        
        except Exception as e:
            logger.error(f"Error marking article as read: {e}")
            return False
    
    def update_article_category(self, article_id: int, category: str) -> bool:
        """
        Update article category.
        
        Args:
            article_id: Article ID
            category: New category name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE articles 
                    SET category = ? 
                    WHERE id = ?
                ''', (category, article_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Article {article_id} category updated to: {category}")
                    return True
                return False
        
        except Exception as e:
            logger.error(f"Error updating article category: {e}")
            return False
    
    def delete_article(self, article_id: int) -> bool:
        """
        Delete an article.
        
        Args:
            article_id: Article ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Article {article_id} deleted")
                    return True
                return False
        
        except Exception as e:
            logger.error(f"Error deleting article: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get reading statistics.
        
        Returns:
            Dictionary with various statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute('SELECT COUNT(*) as total FROM articles')
            total = cursor.fetchone()['total']
            
            # Articles by status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM articles 
                GROUP BY status
            ''')
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Total reading time
            cursor.execute('SELECT SUM(reading_time) as total_time FROM articles')
            total_time = cursor.fetchone()['total_time'] or 0
            
            # Read articles reading time
            cursor.execute('''
                SELECT SUM(reading_time) as read_time 
                FROM articles 
                WHERE status = 'read'
            ''')
            read_time = cursor.fetchone()['read_time'] or 0
            
            # Most common category
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM articles 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 1
            ''')
            top_category_row = cursor.fetchone()
            top_category = top_category_row['category'] if top_category_row else None
            
            # Average reading time
            avg_reading_time = total_time / total if total > 0 else 0
            
            return {
                'total_articles': total,
                'unread': by_status.get('unread', 0),
                'read': by_status.get('read', 0),
                'total_reading_time': total_time,
                'read_reading_time': read_time,
                'average_reading_time': round(avg_reading_time, 1),
                'top_category': top_category,
                'read_percentage': round((by_status.get('read', 0) / total * 100), 1) if total > 0 else 0
            }
    
    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search articles by title or content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching article dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT * FROM articles 
                WHERE title LIKE ? OR content LIKE ? 
                ORDER BY saved_at DESC 
                LIMIT ?
            ''', (search_pattern, search_pattern, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_preference(self, key: str) -> Optional[str]:
        """
        Get a user preference value.
        
        Args:
            key: Preference key
            
        Returns:
            Preference value or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                return row['value']
            return None
    
    def set_user_preference(self, key: str, value: str) -> bool:
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value, datetime.now().isoformat()))
                
                logger.info(f"User preference set: {key} = {value}")
                return True
        
        except Exception as e:
            logger.error(f"Error setting user preference: {e}")
            return False
    
    def _log_event(self, article_id: int, event_type: str, metadata: Optional[str] = None):
        """
        Log a reading event for statistics.
        
        Args:
            article_id: Article ID
            event_type: Type of event (saved, read, etc.)
            metadata: Optional JSON metadata
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reading_stats (article_id, event_type, timestamp, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (article_id, event_type, datetime.now().isoformat(), metadata))
        
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent reading activity.
        
        Args:
            limit: Maximum number of events
            
        Returns:
            List of activity events
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rs.*, a.title, a.url 
                FROM reading_stats rs
                JOIN articles a ON rs.article_id = a.id
                ORDER BY rs.timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_articles(self, days: int = 90) -> int:
        """
        Delete read articles older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of articles deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
                cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
                
                cursor.execute('''
                    DELETE FROM articles 
                    WHERE status = 'read' AND read_at < ?
                ''', (cutoff_iso,))
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old articles")
                return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up old articles: {e}")
            return 0