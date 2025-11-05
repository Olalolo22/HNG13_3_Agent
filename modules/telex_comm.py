"""
Telex Communication Layer - handles all API interactions with Telex platform.
"""
import requests
import json
from typing import Optional, Dict, Any
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TelexCommunicator:
    """Handles all communication with Telex platform."""
    
    def __init__(self):
        """Initialize Telex communicator with API credentials."""
        self.base_url = Config.TELEX_API_BASE_URL
        self.api_key = Config.TELEX_AGENT_API_KEY
        self.channel_id = Config.TELEX_CHANNEL_ID
        self.webhook_slug = Config.TELEX_WEBHOOK_SLUG
        self.headers = {
            "X-AGENT-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        logger.info("TelexCommunicator initialized")
    
    def send_message(self, content: str, thread_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Send a message to the configured Telex channel.
        
        Args:
            content: Message content to send
            thread_id: Optional thread ID if replying in a thread
            
        Returns:
            Response from Telex API or None on failure
        """
        endpoint = f"{self.base_url}/channels/{self.channel_id}/messages"
        payload = {"content": content}
        
        if thread_id:
            payload["thread_id"] = thread_id
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Message sent to channel successfully")
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error sending message: {e}")
            self._handle_http_error(e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending message: {e}")
            return None
    
    def send_formatted_reading_list(self, items: list[Dict[str, str]], 
                                   title: str = "📚 Your Reading List") -> Optional[Dict[str, Any]]:
        """
        Send a formatted reading list to the channel.
        
        Args:
            items: List of items with 'title' and 'url' keys
            title: Title for the reading list
            
        Returns:
            Response from Telex API or None on failure
        """
        if not items:
            logger.warning("Attempted to send empty reading list")
            return None
        
        message = f"{title}\n\n"
        for i, item in enumerate(items, 1):
            item_title = item.get('title', 'Untitled')
            item_url = item.get('url', '')
            message += f"{i}. {item_title}\n   {item_url}\n\n"
        
        return self.send_message(message)
    
    def get_messages(self, limit: int = 50) -> Optional[Dict[str, Any]]:
        """
        Retrieve recent messages from the channel.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages or None on failure
        """
        endpoint = f"{self.base_url}/channels/{self.channel_id}/messages"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving messages: {e}")
            return None
    
    def create_webhook(self, webhook_name: str, webhook_url: str,
                      event_name: str = "message.received") -> Optional[Dict[str, Any]]:
        """
        Create a new webhook for the channel.
        
        Args:
            webhook_name: Name for the webhook
            webhook_url: Your server URL to receive webhook POSTs
            event_name: Event this webhook listens for
            
        Returns:
            Created webhook data including webhook_slug or None on failure
        """
        endpoint = f"{self.base_url}/webhooks/{self.channel_id}"
        payload = {
            "webhook_name": webhook_name,
            "event_name": event_name,
            "webhook_url": webhook_url
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            webhook_slug = data.get('data', {}).get('webhook_slug')
            logger.info(f"Webhook created successfully: {webhook_slug}")
            return data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating webhook: {e}")
            return None
    
    def get_webhook(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the channel's webhook configuration.
        
        Returns:
            Webhook data or None on failure
        """
        endpoint = f"{self.base_url}/webhooks/{self.channel_id}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving webhook: {e}")
            return None
    
    def update_webhook_status(self, webhook_id: str, 
                            status: str = "active") -> Optional[Dict[str, Any]]:
        """
        Update webhook status (active, inactive, or paused).
        
        Args:
            webhook_id: ID of the webhook to update
            status: New status (active, inactive, or paused)
            
        Returns:
            Updated webhook data or None on failure
        """
        endpoint = f"{self.base_url}/webhooks/{self.channel_id}/{webhook_id}/change-status"
        payload = {"webhook_status": status}
        
        try:
            response = requests.put(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook status updated to: {status}")
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating webhook status: {e}")
            return None
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError) -> None:
        """
        Handle and log specific HTTP errors.
        
        Args:
            error: HTTP error from requests
        """
        status_code = error.response.status_code
        
        if status_code == 401:
            logger.error("Authentication failed - check X-AGENT-API-KEY")
        elif status_code == 403:
            logger.error("Access forbidden - check API key permissions")
        elif status_code == 404:
            logger.error("Resource not found - check channel_id")
        elif status_code == 422:
            logger.error("Validation error - check request payload")
        elif status_code == 429:
            logger.warning("Rate limit exceeded - implement backoff")
        else:
            logger.error(f"HTTP {status_code} error occurred")