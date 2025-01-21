# 🔍 Tavily Search MCP Agent

A powerful Model Context Protocol (MCP) Server powered by the Tavily API. Get high-quality, reliable information from business, news, finance, and politics - all through a robust and developer-friendly interface.

[![Tavily Search Agent MCP Server](https://glama.ai/mcp/servers/p0w4whs3l4/badge)](https://glama.ai/mcp/servers/p0w4whs3l4)
[![CI](https://github.com/your-username/mcp-tavily-search/workflows/CI/badge.svg)](https://github.com/your-username/mcp-tavily-search/actions)
[![codecov](https://codecov.io/gh/your-username/mcp-tavily-search/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/mcp-tavily-search)

## 🌟 Why Tavily Search MCP?

In today's fast-paced digital landscape, quick access to precise information is crucial. Tavily Search MCP excels with:

⚡️ Lightning-fast async search responses  
🛡️ Built-in fault tolerance with automatic retries  
🎯 Clean, markdown-formatted results  
🔍 Smart content snippets  
🛠️ Comprehensive error handling  
🖼️ Optional image results  
📰 Specialized news search

## 🚀 Quick Start

Get up and running in minutes:

```bash
# 1. Create environment
uv venv && .venv\Scripts\activate     # Windows
# OR
uv venv && source .venv/bin/activate  # Unix/MacOS

# 2. Install dependencies
uv pip install -e .

# 3. Set up configuration
echo TAVILY_API_KEY=your-key-here > .env

# 4. Start server
cd mcp_tavily_search && uv run server.py
```

## 💡 Core Features

### ⚡️ Performance & Reliability
- Asynchronous request handling
- Built-in error handling and automatic retries
- Configurable request timeouts
- Comprehensive logging system

### 🎯 Search Configuration
- Configurable search depth (basic/advanced)
- Adjustable result limits (1-20 results)
- Clean markdown-formatted output
- Snippet previews with source URLs
- Optional image results
- Specialized news search topic

### 🛡️ Error Handling
- API authentication validation
- Rate limit detection
- Network error recovery
- Request timeout management

## 🛠️ Developer Integration

### Prerequisites
- Python 3.11 or higher
- UV Package Manager ([Installation Guide](https://github.com/astral-sh/uv))
- Tavily API key ([Get one here](https://tavily.com))

### Claude Desktop Setup

Optimize your Claude Desktop experience with this configuration:

```json
{
  "mcpServers": {
    "tavily-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-tavily-search/mcp_tavily_search",
        "run",
        "server.py"
      ],
      "env": {
        "TAVILY_API_KEY": "YOUR-API-KEY"
      }
    }
  }
}
```

📁 Configuration paths:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Unix/MacOS: `~/.config/Claude/claude_desktop_config.json`

## Project Architecture

Our clean, modular structure makes development a breeze:

```
mcp-tavily-search/
├── mcp_tavily_search/     # Core package
│   ├── server.py          # Server implementation
│   ├── client.py          # Tavily API client
│   └── __init__.py        # Package initialization
├── .env                   # Environment configuration
├── README.md              # Documentation
└── pyproject.toml         # Project configuration
```

## Key Components

### Server (server.py)
- MCP protocol implementation
- Request handling and routing
- Error recovery and health monitoring

### Client (client.py)
- Tavily API integration
- Retry mechanism with exponential backoff
- Result formatting and processing
- Error handling and logging

## Usage Examples

Here are some examples of how to use the enhanced search capabilities:

1. Basic search:
```json
{
  "name": "search",
  "arguments": {
    "query": "Latest news on artificial intelligence"
  }
}
```

2. Advanced search with images:
```json
{
  "name": "search",
  "arguments": {
    "query": "Elon Musk SpaceX achievements",
    "search_depth": "advanced",
    "include_images": true,
    "max_results": 10
  }
}
```

3. News-specific search:
```json
{
  "name": "search",
  "arguments": {
    "query": "Climate change impact on agriculture",
    "topic": "news",
    "max_results": 5
  }
}
```

4. Search with raw content:
```json
{
  "name": "search",
  "arguments": {
    "query": "Python programming best practices",
    "include_raw_content": true,
    "max_results": 3
  }
}
```

## Troubleshooting Guide

### Connection Issues
When things don't work as expected, follow these steps:

1. Verify your configuration paths
2. Check the Claude Desktop logs:
   ```bash
   # Windows
   type %APPDATA%\Claude\logs\latest.log
   # Unix/MacOS
   cat ~/.config/Claude/logs/latest.log
   ```
3. Test the server manually using the quick start commands

### API Troubleshooting
If you're experiencing API issues:

1. Validate your API key permissions
2. Check your network connection
3. Monitor the API response in the server logs

## Running Tests

To run the unit tests for this project, follow these steps:

1. Install the development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. Run the tests using pytest:
   ```bash
   pytest mcp_tavily_search
   ```

This will run all the tests in the `mcp_tavily_search` directory, including the ones we've added in `test_client.py`.

## Community and Support

- Report issues and contribute on GitHub
- Share your implementations and improvements
- Join our discussions and help others

## Security and Best Practices

Security is paramount. The server implements:

- Secure API key handling through environment variables
- Automatic request timeout management
- Comprehensive error tracking and logging

## License

This project is licensed under MIT. See the LICENSE file for details.

## Acknowledgments

Special thanks to:
- The innovative Tavily API team
- The MCP protocol community
