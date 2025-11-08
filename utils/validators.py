"""
Input validation utilities.
"""
import re
from typing import Optional
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: String to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_url(url: str) -> Optional[str]:
    """
    Clean and validate URL, adding scheme if missing.
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Optional[str]: Sanitized URL or None if invalid
    """
    url = url.strip()
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url if is_valid_url(url) else None


def extract_urls_from_text(text: str) -> list[str]:
    """
    Extract all URLs from a text string.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        list[str]: List of valid URLs found
    """
    # URL pattern - matches http(s) URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return [url for url in urls if is_valid_url(url)]


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        bool: True if valid UUID, False otherwise
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_string.lower()))


def sanitize_content(content: str, max_length: int = 50000) -> str:
    """
    Sanitize content by removing excessive whitespace and truncating.
    
    Args:
        content: Content to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        str: Sanitized content
    """
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    return content