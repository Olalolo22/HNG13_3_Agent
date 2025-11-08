"""
Message Handler - Processes incoming messages and coordinates agent actions.
"""
from typing import Dict, Any
from utils.logger import setup_logger
from utils.validators import extract_urls_from_text
from modules.content_ingestion import ContentIngester
from modules.storage import Storage
from modules.content_processing import ContentProcessor
from modules.scheduler import Scheduler

logger = setup_logger(__name__)


class MessageHandler:
    """Handles incoming messages from Telex and coordinates agent responses."""
    
    def __init__(self):
        """Initialize message handler with required modules."""
        self.ingester = ContentIngester()
        self.storage = Storage()
        self.processor = ContentProcessor()
        self.scheduler = Scheduler(self.storage)
        logger.info("MessageHandler initialized")
    
    def handle_message(self, message_data: Dict[str, Any]) -> str:
        """Process incoming message and return appropriate response."""
        user_text = message_data.get("text", "").strip()
        if not user_text:
            return (
                "👋 Hi! Send me URLs to save for later, or use commands like "
                "'list', 'categories', or 'stats'."
            )

        logger.info(f"Processing message: {user_text}")
        command = user_text.lower()

        # Commands
        if command in ["list", "queue", "show"]:
            return self._handle_list_command()
        elif command in ["categories", "cats"]:
            return self._handle_categories_command()
        elif command in ["stats", "statistics"]:
            return self._handle_stats_command()
        elif command in ["digest", "summary"]:
            return self._handle_digest_command()
        elif command.startswith("suggest"):
            parts = command.split()
            minutes = 30
            if len(parts) > 1 and parts[1].isdigit():
                minutes = int(parts[1])
            return self._handle_suggest_command(minutes)
        elif command in ["help", "?"]:
            return self._handle_help_command()

        # URL handling
        urls = extract_urls_from_text(user_text) or []
        if urls:
            return self._handle_url_save(urls)

        return self._handle_unknown_input(user_text)

    def _handle_url_save(self, urls: list[str]) -> str:
        """Handle saving URLs to reading queue."""
        if not urls:
            return "❌ No valid URLs found."

        logger.info(f"Saving {len(urls)} URL(s)")
        articles = self.ingester.fetch_multiple(urls) or []

        if not articles:
            return (
                "❌ Sorry, I couldn't fetch any of those articles. They might be:\n"
                "• Behind a paywall\n• Requiring login\n• Temporarily unavailable\n\n"
                "Please try a different URL."
            )

        saved_count = 0
        for article in articles:
            analysis = self.processor.analyze_article(article.to_dict())
            article_dict = article.to_dict()
            article_dict["category"] = analysis.get("category", "Uncategorized")
            article_id = self.storage.save_article(article_dict)
            if article_id:
                saved_count += 1
                logger.info(f"Article saved with category: {article_dict['category']}")

        # Single article save
        if len(urls) == 1:
            article = articles[0] if articles else None
            if article and saved_count > 0:
                analysis = self.processor.analyze_article(article.to_dict())
                response = f"✅ Article saved!\n\n"
                response += f"**{article.title}**\n"
                response += f"📖 {article.reading_time} min read\n"
                if article.author:
                    response += f"✍️ By {article.author}\n"
                response += f"📂 Category: {analysis.get('category', 'Uncategorized')}\n"
                response += f"🔗 {article.url}\n\n"
                response += "Added to your reading queue!"
                return response
            else:
                return f"❌ Couldn't fetch or save the article from:\n📎 {urls[0]}"

        # Multiple article save
        response = f"✅ Saved {saved_count} out of {len(urls)} articles!\n\n"
        for i, article in enumerate(articles, 1):
            if i <= 3:
                analysis = self.processor.analyze_article(article.to_dict())
                response += f"{i}. **{article.title}** ({article.reading_time} min)\n"
                response += f"   📂 {analysis.get('category', 'Uncategorized')}\n"
                response += f"   🔗 {article.url}\n"
        if len(articles) > 3:
            response += f"\n...and {len(articles) - 3} more\n"
        if saved_count < len(urls):
            failed = len(urls) - saved_count
            response += f"\n⚠️ {failed} article(s) couldn't be fetched."
        return response

    def _handle_list_command(self) -> str:
        """Handle 'list' command to show reading queue."""
        logger.info("Handling list command")

        try:
            articles = self.scheduler.prioritize_queue(limit=10)

            # Defensive guard
            if not articles:
                logger.warning("Scheduler returned None or empty list.")
                return "📚 Your reading queue is empty!\n\nSend me URLs to get started."

            # Safe len() usage
            response = f"📚 Your Prioritized Reading Queue ({len(articles)} articles):\n\n"

            for i, article in enumerate(articles, 1):
                title = article.get("title", "Untitled")
                reading_time = article.get("reading_time", "?")
                category = article.get("category", "Uncategorized")
                url = article.get("url", "No URL")

                response += f"{i}. **{title}** ({reading_time} min)\n"
                response += f"   📂 {category}\n"

                suggestion = self.scheduler.get_recommended_reading_time(article)
                if suggestion:
                    response += f"   💡 {suggestion}\n"
                response += f"   🔗 {url}\n\n"

            next_delivery = self.scheduler.get_next_delivery_time()
            if next_delivery:
                response += (
                    f"_Next digest scheduled for: "
                    f"{next_delivery.strftime('%I:%M %p, %A')}_"
                )
            return response

        except Exception as e:
            logger.exception("Error handling list command")
            return f"❌ List command integration\n   Error: {e}"

    def _handle_categories_command(self) -> str:
        """Handle 'categories' command."""
        logger.info("Handling categories command")
        categories = self.storage.get_all_categories() or []

        if not categories:
            return (
                "📁 No categories yet!\n\nSave some articles to see them organized by category."
            )

        response = "📁 Your Categories:\n\n"
        for cat in categories:
            response += (
                f"**{cat.get('category', 'Uncategorized')}** "
                f"({cat.get('count', 0)} articles)\n"
            )
        response += f"\n_Total: {sum(c.get('count', 0) for c in categories)} articles_"
        return response

    def _handle_stats_command(self) -> str:
        """Handle 'stats' command."""
        logger.info("Handling stats command")
        stats = self.storage.get_statistics() or {}

        if not stats.get("total_articles", 0):
            return (
                "📊 No statistics yet!\n\nStart saving articles to see your reading stats."
            )

        response = "📊 Your Reading Stats:\n\n"
        response += f"• Articles saved: {stats.get('total_articles', 0)}\n"
        response += (
            f"• Articles read: {stats.get('read', 0)} "
            f"({stats.get('read_percentage', 0)}%)\n"
        )
        response += f"• Unread articles: {stats.get('unread', 0)}\n"
        if stats.get("top_category"):
            response += f"• Favorite category: {stats['top_category']}\n"
        response += (
            f"• Average reading time: {stats.get('average_reading_time', 0)} minutes\n"
        )
        response += f"• Total reading time: {stats.get('total_reading_time', 0)} minutes\n"
        if stats.get("read", 0) > 0:
            response += (
                f"\n_You've spent {stats.get('read_reading_time', 0)} minutes reading! 📚_"
            )
        return response

    def _handle_digest_command(self) -> str:
        """Handle 'digest' command."""
        logger.info("Handling digest command")
        batch_size = self.scheduler.get_optimal_batch_size() or 5
        digest = self.scheduler.create_digest(num_items=batch_size) or []
        return self.scheduler.format_digest_message(digest)

    def _handle_suggest_command(self, minutes: int) -> str:
        """Handle 'suggest' command."""
        logger.info(f"Handling suggest command for {minutes} minutes")
        articles = self.scheduler.suggest_reading_session(available_minutes=minutes) or []

        if not articles:
            return f"📚 No articles fit in {minutes} minutes.\n\nTry a longer time slot!"

        total_time = sum(a.get("reading_time", 0) for a in articles)
        response = f"📚 **Reading Suggestions for {minutes} minutes**\n\n"
        response += f"I found {len(articles)} articles ({total_time} min total):\n\n"
        for i, article in enumerate(articles, 1):
            response += (
                f"{i}. **{article.get('title', 'Untitled')}** "
                f"({article.get('reading_time', '?')} min)\n"
            )
            response += f"   🔗 {article.get('url', 'No URL')}\n"
        return response

    def _handle_help_command(self) -> str:
        """Handle 'help' command."""
        return """🤖 **Smart Read Later Organizer**

**How to use me:**
• Send me any URL to save it for later
• I'll fetch, categorize, and organize it for you

**Commands:**
• `list` - Show your prioritized reading queue
• `digest` - Get a curated reading digest
• `suggest 30` - Suggest articles for 30 minutes
• `categories` - Show content by category
• `stats` - Show your reading statistics
• `help` - Show this help message

**Examples:**
• "https://example.com/article"
• "list"
• "digest"
• "suggest 15"

I learn from your reading patterns to deliver content at the best times! 📚"""

    def _handle_unknown_input(self, text: str) -> str:
        """Handle unrecognized input."""
        logger.info(f"Unrecognized input: {text}")
        return (
            f"I'm not sure what to do with: \"{text}\"\n\n"
            "💡 **I can help you with:**\n"
            "• Saving URLs for later reading\n"
            "• Organizing your reading queue\n"
            "• Showing your reading statistics\n\n"
            "Try sending me a URL or use commands like 'list', 'categories', or 'help'."
        )
