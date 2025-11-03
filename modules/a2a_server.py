"""
A2A Protocol Server - Handles JSON-RPC requests from Telex.
"""
from flask import Flask, request, jsonify, send_file
from typing import Dict, Any, Optional, Callable
import json
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)


class A2AServer:
    """Flask server implementing A2A protocol for Telex integration."""
    
    def __init__(self, message_handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize A2A server.
        
        Args:
            message_handler: Function to handle message/send requests
        """
        self.app = Flask(__name__)
        self.message_handler = message_handler
        self._setup_routes()
        logger.info("A2A Server initialized")
    
    def _setup_routes(self):
        """Set up Flask routes for A2A protocol."""
        
        @self.app.route('/.well-known/agent.json', methods=['GET'])
        def get_agent_card():
            """
            Serve the Agent Card - Telex uses this to discover agent capabilities.
            
            Returns Agent Card JSON with skills and configuration.
            """
            try:
                agent_card_path = Path('agent_card.json')
                
                if not agent_card_path.exists():
                    logger.error("agent_card.json not found")
                    return jsonify({
                        "error": "Agent card not found"
                    }), 404
                
                logger.info("Agent card requested")
                return send_file(
                    agent_card_path,
                    mimetype='application/json'
                )
            
            except Exception as e:
                logger.error(f"Error serving agent card: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/', methods=['POST'])
        def handle_jsonrpc():
            """
            Handle JSON-RPC requests from Telex.
            
            Routes requests to appropriate handlers based on method.
            """
            try:
                body = request.get_json()
                
                if not body:
                    return self._error_response(None, -32700, "Parse error")
                
                # Validate JSON-RPC structure
                if body.get('jsonrpc') != '2.0':
                    return self._error_response(
                        body.get('id'),
                        -32600,
                        "Invalid Request: jsonrpc must be '2.0'"
                    )
                
                method = body.get('method')
                request_id = body.get('id')
                params = body.get('params', {})
                
                if not method:
                    return self._error_response(request_id, -32600, "Invalid Request: method required")
                
                logger.info(f"Received JSON-RPC request: method={method}, id={request_id}")
                logger.debug(f"Request params: {params}")
                
                # Route to appropriate handler
                if method == "message/send":
                    result = self._handle_message_send(params)
                    return self._success_response(request_id, result)
                
                elif method == "task/subscribe":
                    result = self._handle_task_subscribe(params)
                    return self._success_response(request_id, result)
                
                else:
                    return self._error_response(
                        request_id,
                        -32601,
                        f"Method not found: {method}"
                    )
            
            except Exception as e:
                logger.error(f"Error handling JSON-RPC request: {e}", exc_info=True)
                return self._error_response(
                    body.get('id') if body else None,
                    -32603,
                    f"Internal error: {str(e)}"
                )
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "service": "Smart Read Later Organizer",
                "protocol": "A2A"
            }), 200
    
    def _handle_message_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle message/send JSON-RPC method.
        
        Args:
            params: Request parameters containing message
            
        Returns:
            Message response with agent's reply
        """
        message = params.get('message', {})
        
        if not message:
            raise ValueError("message parameter required")
        
        role = message.get('role')
        parts = message.get('parts', [])
        
        logger.info(f"Processing message from {role} with {len(parts)} parts")
        
        # Extract text from parts
        user_text = ""
        for part in parts:
            if part.get('type') == 'text' or part.get('kind') == 'text':
                user_text += part.get('text', '')
        
        logger.debug(f"User message: {user_text}")
        
        # Call the message handler to process the message
        response_text = self.message_handler({
            'text': user_text,
            'role': role,
            'parts': parts,
            'message': message
        })
        
        # Build A2A response message
        return {
            "role": "agent",
            "parts": [
                {
                    "type": "text",
                    "text": response_text
                }
            ],
            "kind": "message",
            "messageId": self._generate_message_id()
        }
    
    def _handle_task_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task/subscribe JSON-RPC method.
        
        Args:
            params: Request parameters
            
        Returns:
            Task subscription response
        """
        logger.info("Task subscription requested")
        
        # For now, return a simple acknowledgment
        # This can be extended for long-running tasks
        return {
            "status": "acknowledged",
            "message": "Task subscription not yet implemented"
        }
    
    def _success_response(self, request_id: Any, result: Dict[str, Any]) -> tuple:
        """
        Build JSON-RPC success response.
        
        Args:
            request_id: ID from the request
            result: Result data to return
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        return jsonify(response), 200
    
    def _error_response(self, request_id: Any, code: int, message: str) -> tuple:
        """
        Build JSON-RPC error response.
        
        Args:
            request_id: ID from the request
            code: Error code
            message: Error message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        logger.warning(f"Returning error response: {code} - {message}")
        return jsonify(response), 200  # JSON-RPC errors still return 200
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        import uuid
        return str(uuid.uuid4())
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Start the A2A server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable Flask debug mode
        """
        logger.info(f"Starting A2A server on {host}:{port}")
        logger.info(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
        logger.info(f"JSON-RPC endpoint: http://{host}:{port}/")
        
        self.app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )