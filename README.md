# Smart Read Later Organizer API

## Overview
This project is an intelligent AI agent built with Python and Flask, designed to manage and organize "read later" content. It implements the Agent-to-Agent (A2A) protocol via a JSON-RPC server, using spaCy for NLP-driven content analysis and SQLite for persistent storage.

## Features
- **Flask**: Powers the lightweight JSON-RPC server for handling A2A protocol requests.
- **SQLite**: Provides persistent, file-based storage for articles, user preferences, and reading statistics.
- **spaCy**: Enables Natural Language Processing (NLP) for intelligent content categorization and keyword extraction.
- **BeautifulSoup4**: Facilitates robust HTML parsing to extract core article content from web pages.
- **JSON-RPC**: Implements the core A2A communication protocol for agent integration.

## Getting Started
### Installation
Follow these steps to set up the project locally.

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/HNG13_3_Agent.git
    cd HNG13_3_Agent
    ```

2.  **Create and Activate Virtual Environment**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download NLP Model**
    The agent uses spaCy for content processing. Download the required model:
    ```bash
    python -m spacy download en_core_web_sm
    ```

5.  **Configure Environment**
    Create a `.env` file in the project root and add the necessary variables (see below).

6.  **Configure Agent Card**
    Open `agent_card.json` and replace all placeholder values (e.g., `REPLACE_WITH_YOUR_PUBLIC_URL`) with your actual agent information. This is critical for the agent to be discoverable.

7.  **Run the Agent**
    ```bash
    python agent.py
    ```
    The server will start, and the agent will be ready to receive requests.

### Environment Variables
Create a `.env` file in the root directory and configure the following variables.

| Variable         | Description                                    | Example                          |
| ---------------- | ---------------------------------------------- | -------------------------------- |
| `WEBHOOK_HOST`   | The host address for the server.               | `0.0.0.0`                        |
| `WEBHOOK_PORT`   | The port for the server to listen on.          | `5000`                           |
| `DATABASE_PATH`  | The file path for the SQLite database.         | `data/read_later.db`             |
| `LOG_LEVEL`      | The logging level for the application.         | `INFO`                           |
| `AGENT_BASE_URL` | The public base URL where the agent is hosted. | `http://localhost:5000`          |

## API Documentation
### Base URL
`http://localhost:5000`

### Endpoints
#### GET /.well-known/agent.json
Serves the agent's capability card, which allows other services (like Telex) to discover its name, skills, and endpoint URL.

**Request**:
No request body required.

**Response**:
*Success (200 OK)*
```json
{
  "name": "Smart Read Later Organizer",
  "description": "An intelligent AI agent that helps you manage and organize your 'read later' content...",
  "url": "https://your-public-agent-url.com",
  "version": "1.0.0",
  "provider": {
    "organization": "Your Organization Name",
    "url": "https://your-organization-url.com"
  },
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "save_article",
      "name": "Save Article for Later",
      "description": "Saves a URL to your reading queue...",
      "...": "..."
    }
  ]
}
```

**Errors**:
- `404 Not Found`: `agent_card.json` file could not be found in the project root.
- `500 Internal Server Error`: An unexpected error occurred while trying to serve the file.

#### GET /health
Provides a simple health check to confirm that the agent's server is running and responsive.

**Request**:
No request body required.

**Response**:
*Success (200 OK)*
```json
{
  "status": "healthy",
  "service": "Smart Read Later Organizer",
  "protocol": "A2A"
}
```

**Errors**:
- `503 Service Unavailable`: The service is down or experiencing issues.

#### POST /
This is the main JSON-RPC endpoint for all agent interactions, such as sending messages or subscribing to tasks.

**Request**:
The primary method is `message/send`, used to send content or commands to the agent.

*Body Example for saving a URL:*
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "https://www.example.com/some-interesting-article-to-read"
        }
      ]
    }
  },
  "id": "b7e4f2a0-c8d9-4b1a-9f0e-3d2c1b0a9e8d"
}
```
*Body Example for listing saved articles:*
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "list"
        }
      ]
    }
  },
  "id": "c9e5g3b1-d8d9-4b1a-9f0e-3d2c1b0a9e8d"
}
```

**Response**:
The response is a JSON-RPC object containing the agent's reply within the `result` field.

*Success (200 OK) - Article Saved:*
```json
{
  "jsonrpc": "2.0",
  "id": "b7e4f2a0-c8d9-4b1a-9f0e-3d2c1b0a9e8d",
  "result": {
    "role": "agent",
    "parts": [
      {
        "type": "text",
        "text": "✅ Article saved!\n\n**Example Article Title**\n📖 5 min read\n📂 Category: Technology\n🔗 https://www.example.com/some-interesting-article-to-read\n\nAdded to your reading queue!"
      }
    ],
    "kind": "message",
    "messageId": "generated-uuid-v4"
  }
}
```

**Errors**:
All JSON-RPC errors are returned with an HTTP status of `200 OK` but contain an `error` object in the JSON payload.
- `-32700 Parse error`: Invalid JSON was received by the server.
- `-32600 Invalid Request`: The JSON sent is not a valid Request object (e.g., missing `method` or `jsonrpc` version is not '2.0').
- `-32601 Method not found`: The specified method (e.g., `message/nonexistent`) does not exist.
- `-32603 Internal error`: An unexpected error occurred on the server while processing the request. Check server logs for details.