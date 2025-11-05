"""
Smart Read Later Organizer - Main Entry Point

An intelligent AI agent for Telex that helps manage and organize "read later" content.
Implements the A2A (Agent-to-Agent) protocol for seamless Telex integration.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from modules.a2a_server import A2AServer
from modules.message_handler import MessageHandler
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point for the Smart Read Later Organizer agent."""
    
    try:
        # Display configuration
        print("\n" + "="*60)
        Config.display()
        print("="*60 + "\n")
        
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize message handler
        message_handler = MessageHandler()
        logger.info("Message handler initialized")
        
        # Initialize A2A server
        server = A2AServer(message_handler.handle_message)
        logger.info("A2A server initialized")
        
        # Check if agent_card.json exists
        agent_card_path = Path('agent_card.json')
        if not agent_card_path.exists():
            logger.error("agent_card.json not found in project root!")
            print("\n❌ ERROR: agent_card.json not found!")
            print("Please ensure agent_card.json is in the project root directory.\n")
            sys.exit(1)
        
        # Validate agent_card.json has been configured
        import json
        with open(agent_card_path, 'r') as f:
            agent_card = json.load(f)
        
        # Check for placeholder values
        if "REPLACE_" in agent_card.get('url', ''):
            logger.error("agent_card.json not configured!")
            print("\n❌ ERROR: agent_card.json has not been configured!")
            print("\nPlease update agent_card.json with your actual values:")
            print("  • url: Your public agent URL (e.g., https://my-agent.herokuapp.com)")
            print("  • provider.organization: Your organization name")
            print("  • provider.url: Your organization website")
            print("\nSee agent_card.json for detailed instructions.\n")
            sys.exit(1)
        
        logger.info(f"Agent card found and validated at: {agent_card_path.absolute()}")
        
        # Start the server
        print("\n🚀 Starting Smart Read Later Organizer...")
        print(f"\n📍 Agent Card: http://localhost:{Config.WEBHOOK_PORT}/.well-known/agent.json")
        print(f"📍 JSON-RPC Endpoint: http://localhost:{Config.WEBHOOK_PORT}/")
        print(f"📍 Health Check: http://localhost:{Config.WEBHOOK_PORT}/health")
        print("\n✨ Agent is ready to receive messages from Telex!\n")
        print("Press Ctrl+C to stop the server\n")
        
        server.run(
            host=Config.WEBHOOK_HOST,
            port=Config.WEBHOOK_PORT,
            debug=False
        )
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        logger.info("Server stopped by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        print("Check logs/agent.log for details\n")
        sys.exit(1)


if __name__ == "__main__":
    main()