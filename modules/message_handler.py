"""
Message Handler - Processes incoming messages and coordinates agent actions.
"""
from typing import Dict, Any
from utils.logger import setup_logger
from utils.validators import extract_urls_from_text
from modules.content_ingestion import ContentIngester
from modules.storage import Storage
from modules.content_processing import ContentProcessor

# TODO: Import other modules as we build them
# from modules.scheduler import Scheduler

logger = setup_logger(__name__)


class MessageHandler:
    """Handles incoming messages from Telex and coordinates agent responses."""
    
    def __init__(self):
        """Initialize message handler with required modules."""
        self.ingester = ContentIngester()
        self.storage = Storage()
        self.processor = ContentProcessor()
        
        # TODO: Initialize modules as we build them
        # self.scheduler = Scheduler()
        
        logger.info("MessageHandler initialized")
    
    def handle_message(self, message_data: Dict[str, Any]) -> str:
        """
        Process incoming message and return appropriate response.
        
        Args:
            message_data: Dictionary containing message text and metadata
            
        Returns:
            str: Response text to send back to user
        """
        user_text = message_data.get('text', '').strip()
        
        if not user_text:
            return "👋 Hi! Send me URLs to save for later, or use commands like 'list', 'categories', or 'stats'."
        
        logger.info(f"Processing message: {user_text}")
        
        # Check for commands
        command = user_text.lower()
        
        if command in ['list', 'queue', 'show']:
            return self._handle_list_command()
        
        elif command in ['categories', 'cats']:
            return self._handle_categories_command()
        
        elif command in ['stats', 'statistics']:
            return self._handle_stats_command()
        
        elif command in ['help', '?']:
            return self._handle_help_command()
        
        # Check if message contains URLs
        urls = extract_urls_from_text(user_text)
        
        if urls:
            return self._handle_url_save(urls)
        
        # Default response for unrecognized input
        return self._handle_unknown_input(user_text)
    
    def _handle_url_save(self, urls: list[str]) -> str:
        """
        Handle saving URLs to reading queue.
        
        Args:
            urls: List of URLs to save
            
        Returns:
            str: Confirmation message
        """
        logger.info(f"Saving {len(urls)} URL(s)")
        
        # Fetch articles
        articles = self.ingester.fetch_multiple(urls)
        
        if not articles:
            return "❌ Sorry, I couldn't fetch any of those articles. They might be:\n• Behind a paywall\n• Requiring login\n• Temporarily unavailable\n\nPlease try a different URL."
        
        # Process and save articles
        saved_count = 0
        for article in articles:
            # Analyze article content
            analysis = self.processor.analyze_article(article.to_dict())
            
            # Update article data with analysis
            article_dict = article.to_dict()
            article_dict['category'] = analysis['category']
            
            # Save to database with auto-detected category
            article_id = self.storage.save_article(article_dict)
            if article_id:
                saved_count += 1
                logger.info(f"Article saved with category: {analysis['category']}")
        
        # Build response
        if len(urls) == 1:
            article = articles[0] if articles else None
            if article and saved_count > 0:
                # Get analysis for the article
                analysis = self.processor.analyze_article(article.to_dict())
                
                response = f"✅ Article saved!\n\n"
                response += f"**{article.title}**\n"
                response += f"📖 {article.reading_time} min read\n"
                if article.author:
                    response += f"✍️ By {article.author}\n"
                response += f"📂 Category: {analysis['category']}\n"
                response += f"🔗 {article.url}\n\n"
                response += f"Added to your reading queue!"
                return response
            else:
                return f"❌ Couldn't fetch or save the article from:\n📎 {urls[0]}"
        else:
            response = f"✅ Saved {saved_count} out of {len(urls)} articles!\n\n"
            
            for i, article in enumerate(articles, 1):
                if i <= 3:  # Show first 3
                    analysis = self.processor.analyze_article(article.to_dict())
                    response += f"{i}. **{article.title}** ({article.reading_time} min)\n"
                    response += f"   📂 {analysis['category']}\n"
                    response += f"   🔗 {article.url}\n"
            
            if len(articles) > 3:
                response += f"\n...and {len(articles) - 3} more\n"
            
            if saved_count < len(urls):
                failed = len(urls) - saved_count
                response += f"\n⚠️ {failed} article(s) couldn't be fetched."
            
            return response
    
    def _handle_list_command(self) -> str:
        """
        Handle 'list' command to show reading queue.
        
        Returns:
            str: Formatted reading queue
        """
        logger.info("Handling list command")
        
        # Get articles from database
        articles = self.storage.get_reading_queue(limit=10)
        
        if not articles:
            return "📚 Your reading queue is empty!\n\nSend me URLs to get started."
        
        response = f"📚 Your Reading Queue ({len(articles)} articles):\n\n"
        
        for i, article in enumerate(articles, 1):
            response += f"{i}. **{article['title']}** ({article['reading_time']} min read)\n"
            if article.get('category'):
                response += f"   📂 {article['category']}\n"
            response += f"   🔗 {article['url']}\n\n"
        
        if len(articles) >= 10:
            response += "_Showing latest 10 articles_"
        
        return response
    
    def _handle_categories_command(self) -> str:
        """
        Handle 'categories' command to show content grouped by category.
        
        Returns:
            str: Formatted categories
        """
        logger.info("Handling categories command")
        
        # Get categories from database
        categories = self.storage.get_all_categories()
        
        if not categories:
            return "📁 No categories yet!\n\nSave some articles to see them organized by category."
        
        response = "📁 Your Categories:\n\n"
        
        for cat in categories:
            response += f"**{cat['category']}** ({cat['count']} articles)\n"
        
        response += f"\n_Total: {sum(c['count'] for c in categories)} articles_"
        
        return response
    
    def _handle_stats_command(self) -> str:
        """
        Handle 'stats' command to show reading statistics.
        
        Returns:
            str: Formatted statistics
        """
        logger.info("Handling stats command")
        
        # Get statistics from database
        stats = self.storage.get_statistics()
        
        if stats['total_articles'] == 0:
            return "📊 No statistics yet!\n\nStart saving articles to see your reading stats."
        
        response = "📊 Your Reading Stats:\n\n"
        response += f"• Articles saved: {stats['total_articles']}\n"
        response += f"• Articles read: {stats['read']} ({stats['read_percentage']}%)\n"
        response += f"• Unread articles: {stats['unread']}\n"
        
        if stats['top_category']:
            response += f"• Favorite category: {stats['top_category']}\n"
        
        response += f"• Average reading time: {stats['average_reading_time']} minutes\n"
        response += f"• Total reading time: {stats['total_reading_time']} minutes\n"
        
        if stats['read'] > 0:
            response += f"\n_You've spent {stats['read_reading_time']} minutes reading! 📚_"
        
        return response
    
    def _handle_help_command(self) -> str:
        """
        Handle 'help' command to show available commands.
        
        Returns:
            str: Help text
        """
        return """🤖 **Smart Read Later Organizer**

**How to use me:**
• Send me any URL to save it for later
• I'll fetch, categorize, and organize it for you

**Commands:**
• `list` - Show your reading queue
• `categories` - Show content by category
• `stats` - Show your reading statistics
• `help` - Show this help message

**Examples:**
• "https://example.com/article"
• "list"
• "categories"

I learn from your reading patterns to deliver content when you're most likely to read it! 📚"""
    
    def _handle_unknown_input(self, text: str) -> str:
        """
        Handle unrecognized input.
        
        Args:
            text: User's text input
            
        Returns:
            str: Helpful response
        """
        logger.info(f"Unrecognized input: {text}")
        
        return f"""I'm not sure what to do with: "{text}"

💡 **I can help you with:**
• Saving URLs for later reading
• Organizing your reading queue
• Showing your reading statistics

Try sending me a URL or use commands like 'list', 'categories', or 'help'."""