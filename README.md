# Tavily Search MCP Agent

A sophisticated Model Context Protocol (MCP) server that provides comprehensive multi-topic search capabilities powered by the Tavily API. This agent enables intelligent information gathering across business, news, finance, and politics domains with a focus on high-quality, reliable sources.

## Features

- 🔍 **Multi-Topic Search**: Specialized search configurations for business, news, finance, and politics
- 📊 **Quality Assurance**: Minimum of 8 high-quality sources per search
- 🤖 **AI-Powered Summaries**: Intelligent summarization of search results
- 🔄 **Deduplication**: Smart filtering of duplicate sources
- ⚡ **Parallel Processing**: Concurrent search execution across topics

## Prerequisites

- Python 3.11 or higher
- UV package manager ([Install Guide](https://github.com/astral-sh/uv))
- Tavily API key ([Get one here](https://tavily.com))

## Project Structure

```
mcp-tavily-search/
├── mcp_tavily_search/
│   ├── server.py
│   └── __init__.py
├── .env
├── README.md
└── pyproject.toml
```

## Quick Start

1. **Set Up Project**
   ```bash
   # Create and activate virtual environment
   uv venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Unix
   
   # Install package and dependencies
   uv pip install -e .
   ```

2. **Configure API Key**
   Create `.env` in project root (optional):
   ```
   TAVILY_API_KEY=your-api-key-here
   ```

## Claude Desktop Integration

Add to your Claude Desktop configuration (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "tavily-search": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\your\\mcp-tavily-search\\mcp_tavily_search",
        "run",
        "server.py"
      ],
      "env": {
        "TAVILY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Development

Test the server manually:
```bash
cd mcp_tavily_search
uv run server.py
```

## Troubleshooting

Common issues:

- **Server Connection Issues**
  - Verify paths in claude_desktop_config.json
  - Check Claude Desktop logs: `%APPDATA%\Claude\logs`
  - Test manual server start

- **API Errors**
  - Verify Tavily API key 
  - Check API key permissions

## Search Configurations

| Topic | Depth | Update Frequency | Results |
|-------|-------|-----------------|----------|
| Business | Advanced | Standard | 12 |
| News | Basic | 24 hours | 10 |
| Finance | Advanced | Standard | 12 |
| Politics | Basic | 48 hours | 10 |

## License

MIT License

## Acknowledgments

- Tavily API team
- Model Context Protocol framework
- Claude Desktop team