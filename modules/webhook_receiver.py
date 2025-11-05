"""
Webhook Receiver - Flask server to receive webhook events from Telex.
"""
from flask import Flask, request, jsonify
from typing import Callable, Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WebhookReceiver:
    """Flask server to receive and process webhook events from Telex."""
    
    def __init__(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize webhook receiver.
        
        Args:
            callback: Function to call when webhook is triggered with event data
        """
        self.app = Flask(__name__)
        self.callback = callback
        self._setup_routes()
        logger.info("WebhookReceiver initialized")
    
    def _setup_routes(self):
        """Set up Flask routes for webhook endpoints."""
        
        @self.app.route('/webhook', methods=['POST'])
        def handle_webhook():
            """
            Handle incoming webhook POST from Telex.
            
            Expected payload structure (update based on actual Telex webhook):
            {
                "event_name": "message.received",
                "channel_id": "uuid",
                "user": {
                    "id": "uuid",
                    "username": "John Doe"
                },
                "message": {
                    "id": "uuid",
                    "content": "https://example.com/article",
                    "created_at": "2023-01-01T00:00:00Z"
                }
            }
            """
            try:
                data = request.get_json()
                
                if not data:
                    logger.warning("Received empty webhook payload")
                    return jsonify({"error": "Empty payload"}), 400
                
                event_name = data.get('event_name', 'unknown')
                logger.info(f"Received webhook event: {event_name}")
                logger.debug(f"Webhook payload: {data}")
                
                # Call the callback to process the webhook data
                self.callback(data)
                
                return jsonify({
                    "status": "success",
                    "message": "Webhook received and processed"
                }), 200
            
            except Exception as e:
                logger.error(f"Error processing webhook: {e}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint to verify server is running."""
            return jsonify({
                "status": "healthy",
                "service": "Smart Read Later Organizer"
            }), 200
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Root endpoint with basic info."""
            return jsonify({
                "service": "Smart Read Later Organizer",
                "version": "1.0.0",
                "endpoints": {
                    "webhook": "/webhook (POST)",
                    "health": "/health (GET)"
                }
            }), 200
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Start the Flask webhook server.
        
        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to listen on (default: 5000)
            debug: Enable Flask debug mode (default: False for production)
        """
        logger.info(f"Starting webhook server on {host}:{port}")
        logger.info(f"Webhook endpoint: http://{host}:{port}/webhook")
        
        self.app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False  # Avoid double initialization
        )