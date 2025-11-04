# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository implements a FastAPI-based service that exposes Tushare financial data APIs through both HTTP endpoints and Model Context Protocol (MCP) tools. The main entry point is `server.py` which defines all API routes and MCP tools.

Key technologies used:
- FastAPI for HTTP API implementation
- Tushare for financial data access
- MCP (Model Context Protocol) for IDE integration
- Pandas for data processing
- Python-dotenv for configuration management

## Architecture

### Main Components

1. **FastAPI Application** (`server.py`)
   - Root endpoint (`/`) for health checks
   - HTTP API endpoints under `/tools/` namespace
   - SSE endpoint (`/sse`) for MCP communication

2. **MCP Integration** (`server.py`)
   - Tools decorated with `@mcp.tool()` for IDE compatibility
   - Custom SSE transport implementation for MCP communication

3. **Tushare Integration** (`server.py`)
   - Token management functions (`setup_tushare_token`, `check_token_status`)
   - Data retrieval functions (`get_daily_prices`, `get_weekly_prices`, `get_monthly_prices`)
   - Utility functions (`search_stocks`, `get_trade_calendar`, `get_start_date_for_n_days`)

4. **Configuration Management**
   - Environment variables via python-dotenv
   - Token stored in `~/.tushare_mcp/.env`

### Data Flow

1. **Token Setup**
   - User provides Tushare token via API or MCP tool
   - Token is validated by querying Tushare's `stock_basic` API
   - Token is stored in environment variables and `.env` file

2. **Data Retrieval**
   - User requests stock data with parameters (ts_code, dates, etc.)
   - Server authenticates with Tushare using stored token
   - Data is fetched, processed, and formatted for response

3. **Response Formatting**
   - Data is formatted as human-readable strings with appropriate units
   - Error conditions are handled gracefully with informative messages

## Common Development Tasks

### Running the Service
```bash
python server.py
```

The service will start on `http://127.0.0.1:8000` by default.

### Setting Up Tushare Token
Before using any data APIs, configure your Tushare token:
```bash
# Using curl
curl -X POST http://127.0.0.1:8000/tools/setup_tushare_token \
     -H "Content-Type: application/json" \
     -d '{"token":"<your_token_here>"}'
```

### Testing API Endpoints
Example of fetching daily prices:
```bash
# Using curl
curl -G http://127.0.0.1:8000/tools/get_daily_prices \
     --data-urlencode "ts_code=600519.SH" \
     --data-urlencode "trade_date=20250301"
```

### Connecting via MCP
In MCP-compatible IDEs:
1. Add server with SSE Endpoint: `http://127.0.0.1:8000/sse`
2. Use tools like `get_daily_prices`, `search_stocks`, etc.

## Dependencies
See `requirements.txt` for complete list. Key dependencies include:
- fastapi
- tushare
- pandas
- mcp
- python-dotenv
- uvicorn