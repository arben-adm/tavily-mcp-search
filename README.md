# Tavily Search MCP Agent

A sophisticated Model Context Protocol (MCP) server that provides comprehensive multi-topic search capabilities powered by the Tavily API. This agent enables intelligent information gathering across business, news, finance, and politics domains with a focus on high-quality, reliable sources.

<a href="https://glama.ai/mcp/servers/p0w4whs3l4"><img width="380" height="200" src="https://glama.ai/mcp/servers/p0w4whs3l4/badge" alt="Tavily Search Agent MCP server" /></a>

## Features

- 🔍 **Multi-Topic Search**: Specialized search configurations for business, news, finance, and politics
- 📊 **Quality Assurance**: Minimum of 8 high-quality sources per search
- 🤖 **AI-Powered Summaries**: Intelligent summarization of search results
- 🔄 **Deduplication**: Smart filtering of duplicate sources
- ⚡ **Parallel Processing**: Concurrent search execution across topics

## Prerequisites

- Python 3.8 or higher
- UV package installer
- A Tavily API key ([Get one here](https://tavily.com))
- Claude Desktop (optional, for GUI interface)

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/tavily-mcp-search.git
   cd tavily-mcp-search
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   # Create virtual environment
   uv venv
   
   # Windows
   .venv\Scripts\Activate.ps1
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   uv pip install mcp>=1.2.0 httpx python-dotenv
   uv pip install -e .
   ```

4. **Configure Environment**
   ```bash
   # Windows
   Set-Content -Path ".env" -Value "TAVILY_API_KEY=your-api-key-here" -Encoding UTF8
   
   # macOS/Linux
   echo "TAVILY_API_KEY=your-api-key-here" > .env
   ```

## Usage

### As a Standalone Server

1. Start the server:
   ```bash
   mcp-tavily-search
   ```

2. The server exposes the following tool:
   - `comprehensive_search`: Performs multi-topic research with a single query

### Integration with Claude Desktop

1. Add the following to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):
   ```json
   {
     "mcpServers": {
       "tavily-search": {
         "command": "PATH_TO_YOUR_VENV\\Scripts\\mcp-tavily-search.exe",
         "env": {
           "TAVILY_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

2. Replace `PATH_TO_YOUR_VENV` with your actual virtual environment path
3. Replace `your-api-key-here` with your Tavily API key
4. Restart Claude Desktop

## Search Topics and Configurations

The agent uses specialized configurations for different topics:

| Topic | Depth | Update Frequency | Results |
|-------|-------|-----------------|----------|
| Business | Advanced | Standard | 12 |
| News | Basic | 24 hours | 10 |
| Finance | Advanced | Standard | 12 |
| Politics | Basic | 48 hours | 10 |

## Development

### Modifying Search Configurations

Search configurations can be customized in `server.py`:

```python
TOPIC_CONFIGS = {
    "business": SearchConfig("advanced", "general", max_results=12),
    "news": SearchConfig("basic", "news", days=1, max_results=10),
    # Add or modify configurations
}
```

### Adding New Features

1. Clone the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

Common issues and solutions:

- **Server won't start**: Check if the virtual environment is activated
- **API errors**: Verify your Tavily API key in the .env file
- **Claude Desktop integration**: Ensure the path in config.json is correct

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the [MIT License](https://mit-license.org/).

## Acknowledgments

- Tavily API for providing the search capabilities
- Model Context Protocol for the server framework
- Claude Desktop for the GUI integration capabilities
