"""
Content Ingestion Module - Fetches and parses content from URLs.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import re
from utils.logger import setup_logger
from utils.validators import is_valid_url, sanitize_content
from config.config import Config

logger = setup_logger(__name__)


class Article:
    """Represents a fetched article with metadata."""
    
    def __init__(self, url: str, title: str, content: str, 
                 author: Optional[str] = None, published_date: Optional[str] = None,
                 description: Optional[str] = None, reading_time: Optional[int] = None):
        """
        Initialize Article object.
        
        Args:
            url: Article URL
            title: Article title
            content: Main article content
            author: Article author (optional)
            published_date: Publication date (optional)
            description: Article description/summary (optional)
            reading_time: Estimated reading time in minutes (optional)
        """
        self.url = url
        self.title = title
        self.content = content
        self.author = author
        self.published_date = published_date
        self.description = description
        self.reading_time = reading_time or self._estimate_reading_time(content)
        self.fetched_at = datetime.now().isoformat()
        self.domain = urlparse(url).netloc
    
    def _estimate_reading_time(self, content: str) -> int:
        """
        Estimate reading time based on word count.
        Average reading speed: 200-250 words per minute.
        
        Args:
            content: Article content
            
        Returns:
            Estimated reading time in minutes
        """
        if not content:
            return 1
        
        word_count = len(content.split())
        reading_time = max(1, round(word_count / 225))  # 225 words per minute
        return reading_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary for storage."""
        return {
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'published_date': self.published_date,
            'description': self.description,
            'reading_time': self.reading_time,
            'fetched_at': self.fetched_at,
            'domain': self.domain
        }
    
    def __repr__(self) -> str:
        return f"Article(title='{self.title}', url='{self.url}', reading_time={self.reading_time}min)"


class ContentIngester:
    """Fetches and parses content from URLs."""
    
    def __init__(self, timeout: int = 10, user_agent: Optional[str] = None):
        """
        Initialize content ingester.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        logger.info("ContentIngester initialized")
    
    def fetch_article(self, url: str) -> Optional[Article]:
        """
        Fetch and parse an article from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Article object or None if fetch/parse fails
        """
        if not is_valid_url(url):
            logger.error(f"Invalid URL: {url}")
            return None
        
        logger.info(f"Fetching article: {url}")
        
        try:
            # Fetch HTML content
            html = self._fetch_html(url)
            if not html:
                return None
            
            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract article data
            title = self._extract_title(soup, url)
            content = self._extract_content(soup)
            author = self._extract_author(soup)
            published_date = self._extract_published_date(soup)
            description = self._extract_description(soup)
            
            # Sanitize content
            content = sanitize_content(content, Config.MAX_CONTENT_LENGTH)
            
            if not content or len(content) < 100:
                logger.warning(f"Insufficient content extracted from {url}")
                return None
            
            article = Article(
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                description=description
            )
            
            logger.info(f"Successfully fetched: {article.title} ({article.reading_time} min read)")
            return article
        
        except Exception as e:
            logger.error(f"Error fetching article from {url}: {e}", exc_info=True)
            return None
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML string or None on failure
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                logger.warning(f"Non-HTML content type: {content_type}")
                return None
            
            return response.text
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.exceptions.TooManyRedirects:
            logger.error(f"Too many redirects for {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract article title from HTML.
        
        Args:
            soup: BeautifulSoup object
            url: Original URL (fallback)
            
        Returns:
            Article title
        """
        # Try common title selectors in order of preference
        title = None
        
        # Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
        
        # Twitter title
        if not title:
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title:
                title = twitter_title.get('content')
        
        # Article heading
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        # HTML title tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # Fallback to URL
        if not title:
            title = urlparse(url).path.split('/')[-1] or url
        
        # Clean title
        title = title.strip()
        
        # Remove common suffixes
        for suffix in [' - ', ' | ', ' :: ']:
            if suffix in title:
                title = title.split(suffix)[0]
        
        return title[:200]  # Limit length
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main article content from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Article content text
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'iframe', 'noscript', 'form']):
            element.decompose()
        
        # Try to find article content using common selectors
        content_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            'main',
            '#content',
            '.story-body'
        ]
        
        content = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(separator='\n', strip=True)
                if len(content) > 200:  # Minimum content threshold
                    break
        
        # Fallback to body
        if not content or len(content) < 200:
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        if content:
            content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove excessive newlines
            content = re.sub(r' +', ' ', content)  # Remove excessive spaces
        
        return content or ""
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract article author from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Author name or None
        """
        # Try meta tags
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            return author_meta.get('content', '').strip()
        
        # Try Open Graph
        og_author = soup.find('meta', property='article:author')
        if og_author:
            return og_author.get('content', '').strip()
        
        # Try common class names
        author_selectors = [
            '.author',
            '.author-name',
            '.by-author',
            '[rel="author"]',
            '.post-author'
        ]
        
        for selector in author_selectors:
            author = soup.select_one(selector)
            if author:
                return author.get_text(strip=True)
        
        return None
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract publication date from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Publication date string or None
        """
        # Try meta tags
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            return date_meta.get('content', '').strip()
        
        # Try time tags
        time_tag = soup.find('time')
        if time_tag:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                return datetime_attr.strip()
            return time_tag.get_text(strip=True)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract article description/summary from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Description text or None
        """
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '').strip()
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Try Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc:
            return twitter_desc.get('content', '').strip()
        
        return None
    
    def fetch_multiple(self, urls: list[str]) -> list[Article]:
        """
        Fetch multiple articles from a list of URLs.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of successfully fetched Article objects
        """
        articles = []
        
        for url in urls:
            article = self.fetch_article(url)
            if article:
                articles.append(article)
        
        logger.info(f"Fetched {len(articles)} out of {len(urls)} articles")
        return articles