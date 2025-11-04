import os
import sys
import functools
import traceback
import logging
from pathlib import Path
from typing import Optional, Callable

import tushare as ts
import pandas as pd
import uvicorn
from dotenv import load_dotenv, set_key
from fastapi import FastAPI, HTTPException, Body
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from mcp.server.sse import SseServerTransport

# --- 1. 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# --- 2. 错误处理装饰器 ---
def tushare_tool_handler(func: Callable) -> Callable:
    """统一处理 Tushare 工具的错误、日志和 Token 检查"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"调用工具: {func.__name__}，参数: {kwargs}")
        token = get_tushare_token()
        if not token:
            return "错误：Tushare token 未配置或无法获取。请先使用 setup_tushare_token 配置。"
        
        try:
            # 将 pro_api 实例作为第一个参数注入
            pro_api = ts.pro_api(token)
            return func(pro_api, *args, **kwargs)
        except Exception as e:
            logging.error(f"工具 {func.__name__} 执行出错: {e}", exc_info=True)
            return f"执行失败: {str(e)}"
    return wrapper

# --- 3. 初始化 ---
ENV_FILE = Path.home() / ".tushare_mcp" / ".env"
mcp = FastMCP("Tushare Tools")
app = FastAPI(
    title="Tushare MCP API",
    description="Remote API for Tushare MCP tools via FastAPI.",
    version="1.0.1"
)

# --- 4. 核心 Token 管理 ---
def init_env_file():
    """初始化环境变量文件"""
    try:
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not ENV_FILE.exists():
            ENV_FILE.touch()
        load_dotenv(ENV_FILE)
    except Exception as e:
        logging.error(f"初始化 .env 文件失败: {e}", exc_info=True)

def get_tushare_token() -> Optional[str]:
    """获取Tushare token"""
    init_env_file()
    return os.getenv("TUSHARE_TOKEN")

def set_tushare_token(token: str):
    """设置Tushare token"""
    init_env_file()
    try:
        set_key(ENV_FILE, "TUSHARE_TOKEN", token)
        ts.set_token(token)
    except Exception as e:
        logging.error(f"设置 token 失败: {e}", exc_info=True)

# --- 5. MCP 工具定义 ---
@mcp.tool()
def setup_tushare_token(token: str) -> str:
    """
    配置并验证 Tushare API Token。

    参数:
        token: 你的 Tushare API Token。
    """
    if not token or not isinstance(token, str):
        return "错误：必须提供有效的 Tushare API Token 字符串。"
    
    try:
        set_tushare_token(token)
        pro = ts.pro_api(token)
        df = pro.stock_basic(limit=1)
        if not df.empty:
            logging.info("Tushare token 设置并验证成功。")
            return "Tushare API Token 配置成功！"
        else:
            logging.warning("Tushare token 已设置，但验证失败。")
            return "警告：Token 已设置，但可能无效。请检查 Token 是否正确。"
    except Exception as e:
        logging.error(f"设置 Token 过程中发生异常: {e}", exc_info=True)
        return f"设置 Token 失败: {str(e)}"

@mcp.tool()
def check_token_status() -> str:
    """
    检查 Tushare API Token 的当前状态和有效性。
    """
    token = get_tushare_token()
    if not token:
        return "未配置 Tushare API Token。请使用 setup_tushare_token 工具进行配置。"
    
    try:
        pro = ts.pro_api(token)
        df = pro.stock_basic(limit=1)
        if not df.empty:
            masked_token = f"{'*' * (len(token) - 4)}{token[-4:]}" if len(token) > 4 else "****"
            return f"Tushare API Token 状态正常，可以使用。Token: {masked_token}"
        else:
            return "警告：Token 已配置，但验证失败，可能无效。"
    except Exception as e:
        logging.error(f"检查 Token 状态时发生异常: {e}", exc_info=True)
        return f"检查 Token 状态失败: {str(e)}"

@mcp.tool()
@tushare_tool_handler
def search_stocks(keyword: str) -> str:
    """
    Search for stock information by keyword.
    
    :param keyword: The keyword to search for (stock code or name).
    :return: A formatted string of stock information.
    """
    try:
        logging.info(f"Searching for stock with keyword: {keyword}")
        df = g.pro_api.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,list_date'
        )

        if keyword:
            df = df[
                df['ts_code'].str.contains(keyword, case=False, na=False) |
                df['name'].str.contains(keyword, case=False, na=False)
            ]

        if df.empty:
            return f"No stock found with keyword: {keyword}"

        return df.to_string(index=False)
    except Exception as e:
        logging.error(f"Error searching stocks for keyword '{keyword}': {e}", exc_info=True)
        return f"An error occurred while searching for stocks: {e}"

@mcp_tool(
    name="usage_guide",
    description="Provide usage guide for this toolset."
)
def usage_guide() -> str:
    """提供此工具集的使用指南。"""
    return """欢迎使用 Tushare 股票查询工具！

可用工具:
1. setup_tushare_token(token: str)
   - 功能: 设置你的 Tushare API token。这是第一步。
   - 示例: > setup_tushare_token("你的真实token字符串")

2. check_token_status()
   - 功能: 检查当前 token 是否配置好并且有效。
   - 示例: > check_token_status()

3. search_stocks(keyword: str)
   - 功能: 根据股票代码或名称的关键词搜索股票。
   - 示例: > search_stocks("茅台")
   - 示例: > search_stocks("600519")
"""

# --- 6. FastAPI & MCP 服务集成 ---
@app.get("/")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "Tushare MCP API is running!"}

# HTTP 接口，用于设置 Token（可选）
@app.post("/tools/setup_tushare_token")
async def api_setup_tushare_token(payload: dict = Body(...)):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Payload must include a 'token' key.")
    try:
        result = setup_tushare_token(token=token)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MCP SSE 集成 ---
MCP_BASE_PATH = "/sse"
try:
    messages_full_path = f"{MCP_BASE_PATH}/messages/"
    sse_transport = SseServerTransport(messages_full_path)

    async def handle_mcp_sse_handshake(request: Request) -> None:
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await mcp._mcp_server.run(
                read_stream, write_stream, mcp._mcp_server.create_initialization_options()
            )

    app.add_route(MCP_BASE_PATH, handle_mcp_sse_handshake, methods=["GET"])
    app.mount(messages_full_path, sse_transport.handle_post_message)
    logging.info("MCP SSE 集成设置完成。")

except Exception as e:
    logging.critical(f"应用 MCP SSE 设置时发生严重错误: {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logging.info(f"启动服务器，监听端口: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)