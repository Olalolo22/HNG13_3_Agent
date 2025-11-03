"""
Configuration management for Smart Read Later Organizer.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # Agent Configuration
    AGENT_BASE_URL: str = os.getenv("AGENT_BASE_URL", "http://localhost:5000")
    AGENT_NAME: str = "Smart Read Later Organizer"
    AGENT_VERSION: str = "1.0.0"
    
    # Server Configuration
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "5000"))
    
    # Storage Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/read_later.db")
    
    # Content Processing Configuration
    MAX_CONTENT_LENGTH: int = 50000  # characters
    DEFAULT_CATEGORY: str = "Uncategorized"
    MIN_READING_TIME: int = 1  # minutes
    
    # Scheduling Configuration
    DEFAULT_DELIVERY_HOUR: int = 9  # 9 AM
    MAX_ITEMS_PER_DELIVERY: int = 5
    DELIVERY_FREQUENCY_HOURS: int = 24
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/agent.log"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        # No required external API keys for A2A protocol
        # Agent is self-contained
        return True
    
    @classmethod
    def display(cls) -> None:
        """Display current configuration (excluding sensitive data)."""
        print(f"=== {cls.AGENT_NAME} v{cls.AGENT_VERSION} ===")
        print(f"Base URL: {cls.AGENT_BASE_URL}")
        print(f"Server: {cls.WEBHOOK_HOST}:{cls.WEBHOOK_PORT}")
        print(f"Database: {cls.DATABASE_PATH}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("=" * 50)