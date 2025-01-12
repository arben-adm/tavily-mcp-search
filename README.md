# Tavily Search MCP Agent

Transform your search capabilities with an intelligent Model Context Protocol (MCP) server powered by the Tavily API. Get high-quality, reliable information across business, news, finance, and politics domains, all through a robust and developer-friendly interface.

<a href="https://glama.ai/mcp/servers/p0w4whs3l4"><img width="380" height="200" src="https://glama.ai/mcp/servers/p0w4whs3l4/badge" alt="Tavily Search Agent MCP server" /></a>

## Why Choose Tavily Search MCP?

In today's fast-paced digital landscape, getting accurate information quickly is crucial. Tavily Search MCP stands out by offering:

- Lightning-fast search responses with intelligent caching
- Built-in resilience with automatic retries and health monitoring
- Smart request queuing for optimal performance
- Clean, parsed results ready for integration
- Enterprise-grade rate limiting and resource management

## Quick Start

Get up and running in minutes:

```bash
# Create your environment
uv venv && source .venv/bin/activate  # Unix/MacOS
# or
uv venv && .venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .

# Set up your config
echo "TAVILY_API_KEY=your-key-here" > .env

# Launch the server
cd mcp_tavily_search && uv run server.py
```

## Core Features

We've built Tavily Search MCP with modern development practices in mind:

### Performance Optimization
The server handles concurrent requests efficiently through:
- Intelligent request queuing (max 5 concurrent requests)
- 30-second request timeouts with automatic retries
- Exponential backoff for failed requests
- Background health checks every 30 seconds

### Topic-Specific Search Configurations

Each search domain is optimized for its specific use case:

**Business & Finance**
Experience deep insights with:
- Advanced search depth for comprehensive results
- 12 curated results per query
- Standard refresh intervals for accuracy

**News & Politics**
Stay current with:
- Streamlined search depth for quick updates
- 10 focused results per query
- 24-48 hour refresh cycles for timely information

## Developer Integration

### Prerequisites
- Python 3.11+
- UV package manager ([Installation Guide](https://github.com/astral-sh/uv))
- Tavily API key ([Get Yours](https://tavily.com))

### Claude Desktop Integration

Enhance your Claude Desktop experience by adding this to your configuration:

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
        "TAVILY_API_KEY": "your-key-here"
      }
    }
  }
}
```

Configuration path:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Unix/MacOS: `~/.config/Claude/claude_desktop_config.json`

## Project Architecture

Our clean, modular structure makes development a breeze:

```
mcp-tavily-search/
├── mcp_tavily_search/     # Core package
│   ├── server.py          # Server implementation
│   └── __init__.py        # Package initialization
├── .env                   # Environment configuration
├── README.md             # Documentation
└── pyproject.toml        # Project configuration
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

## Community and Support

We believe in the power of community:

- Report issues and contribute on GitHub
- Join discussions in the [Tavily API Forum](https://tavily.com/forum)
- Share your implementations and improvements

## Security and Best Practices

We take security seriously. The server implements:

- Secure API key handling through environment variables
- Request rate limiting to prevent API abuse
- Automatic request timeout management
- Error tracking and logging

## License

This project is licensed under MIT. See the LICENSE file for details.

## Acknowledgments

Built with support from:
- The innovative Tavily API team
- Model Context Protocol framework developers
- Claude Desktop integration team
- Our vibrant community of contributors

---
*Last Updated: January 2025*

Made with ♥️ by the Tavily Search MCP team