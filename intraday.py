import sys
from pathlib import Path
from typing import Optional
import tushare as ts
from dotenv import load_dotenv, set_key
import pandas as pd
from datetime import datetime, timedelta
import traceback
import os

from fastapi import FastAPI, HTTPException, Body
import uvicorn
from starlette.requests import Request
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

print("DEBUG: intraday.py starting...", file=sys.stderr, flush=True)

# --- Environment File Configuration ---
# 首先尝试从项目根目录加载 .env 文件
PROJECT_ENV_FILE = Path(__file__).parent / ".env"
# 如果项目根目录没有 .env 文件，则使用用户目录下的 .env 文件
USER_ENV_FILE = Path.home() / ".tushare_intraday" / ".env"

# 优先使用项目根目录的 .env 文件
if PROJECT_ENV_FILE.exists():
    ENV_FILE = PROJECT_ENV_FILE
    print(f"DEBUG: Using project .env file: {ENV_FILE}", file=sys.stderr, flush=True)
    load_dotenv(ENV_FILE)
else:
    ENV_FILE = USER_ENV_FILE
    print(f"DEBUG: Using user home .env file: {ENV_FILE}", file=sys.stderr, flush=True)


# --- Helper Functions ---
def _get_stock_name(pro_api_instance, ts_code: str) -> str:
    """Helper function to get stock name from ts_code."""
    print(f"DEBUG: _get_stock_name called for ts_code: {ts_code}", file=sys.stderr, flush=True)
    if not pro_api_instance:
        print("DEBUG: _get_stock_name received no pro_api_instance. Cannot fetch name.", file=sys.stderr, flush=True)
        return ts_code
    try:
        df_basic = pro_api_instance.stock_basic(ts_code=ts_code, fields='ts_code,name')
        if not df_basic.empty:
            return df_basic.iloc[0]['name']
    except Exception as e:
        print(f"Warning: Failed to get stock name for {ts_code}: {e}", file=sys.stderr, flush=True)
    return ts_code

# --- Token Management Functions ---
def init_env_file():
    """初始化环境变量文件"""
    print("DEBUG: init_env_file called.", file=sys.stderr, flush=True)
    try:
        # 如果使用的是项目根目录的 .env 文件，且该文件已存在，则直接加载
        if ENV_FILE == PROJECT_ENV_FILE and ENV_FILE.exists():
            print(f"DEBUG: Project .env file already exists: {ENV_FILE}", file=sys.stderr, flush=True)
            load_dotenv(ENV_FILE)
            print("DEBUG: load_dotenv(PROJECT_ENV_FILE) called.", file=sys.stderr, flush=True)
            return
        
        # 否则，确保用户目录下的 .env 文件存在
        print(f"DEBUG: Attempting to create directory: {ENV_FILE.parent}", file=sys.stderr, flush=True)
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        print(f"DEBUG: Directory {ENV_FILE.parent} ensured.", file=sys.stderr, flush=True)
        if not ENV_FILE.exists():
            print(f"DEBUG: ENV_FILE {ENV_FILE} does not exist, attempting to touch.", file=sys.stderr, flush=True)
            ENV_FILE.touch()
            print(f"DEBUG: ENV_FILE {ENV_FILE} touched.", file=sys.stderr, flush=True)
        else:
            print(f"DEBUG: ENV_FILE {ENV_FILE} already exists.", file=sys.stderr, flush=True)
        load_dotenv(ENV_FILE)
        print("DEBUG: load_dotenv(ENV_FILE) called.", file=sys.stderr, flush=True)
    except Exception as e_fs:
        print(f"DEBUG: ERROR in init_env_file filesystem operations: {str(e_fs)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)

def get_tushare_token() -> Optional[str]:
    """获取Tushare token"""
    print("DEBUG: get_tushare_token called.", file=sys.stderr, flush=True)
    init_env_file()
    token = os.getenv("TUSHARE_TOKEN")
    print(f"DEBUG: get_tushare_token: os.getenv result: {'TOKEN_FOUND' if token else 'NOT_FOUND'}", file=sys.stderr, flush=True)
    return token

def set_tushare_token(token: str):
    """设置Tushare token"""
    print(f"DEBUG: set_tushare_token called with token: {'********' if token else 'None'}", file=sys.stderr, flush=True)
    init_env_file()
    try:
        set_key(ENV_FILE, "TUSHARE_TOKEN", token)
        print(f"DEBUG: set_key executed for ENV_FILE: {ENV_FILE}", file=sys.stderr, flush=True)
        ts.set_token(token)
        print("DEBUG: ts.set_token(token) executed.", file=sys.stderr, flush=True)
    except Exception as e_set_token:
        print(f"DEBUG: ERROR in set_tushare_token during set_key or ts.set_token: {str(e_set_token)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)

# --- MCP Instance Creation ---
try:
    mcp = FastMCP("Tushare Intraday Tools")
    print("DEBUG: FastMCP instance created for Tushare Intraday Tools.", file=sys.stderr, flush=True)
except Exception as e:
    print(f"DEBUG: ERROR creating FastMCP: {e}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    raise

# --- FastAPI App Creation ---
app = FastAPI(
    title="Tushare Intraday API",
    description="Remote API for Tushare Intraday tools via FastAPI.",
    version="0.0.1"
)

@app.get("/")
async def read_root():
    return {"message": "Hello World - Tushare Intraday API is running!"}

# --- Token Management Endpoints ---
@app.post("/tools/setup_tushare_token", summary="Setup Tushare API token")
async def api_setup_tushare_token(payload: dict = Body(...)):
    """
    Sets the Tushare API token.
    Expects a JSON payload with a "token" key.
    Example: {"token": "your_actual_token_here"}
    """
    print(f"DEBUG: API /tools/setup_tushare_token called with payload.", file=sys.stderr, flush=True)
    token = payload.get("token")
    if not token or not isinstance(token, str):
        print(f"DEBUG: API /tools/setup_tushare_token - Missing or invalid token in payload.", file=sys.stderr, flush=True)
        raise HTTPException(status_code=400, detail="Missing or invalid 'token' in payload. Expected a JSON object with a 'token' string.")

    try:
        set_tushare_token(token)
        current_token = get_tushare_token()
        if not current_token:
            return {"status": "warning", "message": "Token配置尝试完成，但未能立即验证。请稍后检查。"}
        ts.pro_api(current_token)
        return {"status": "success", "message": "Token配置成功！您现在可以使用Tushare的API功能了。"}
    except Exception as e:
        error_message = f"Error setting up token via API: {str(e)}"
        print(f"DEBUG: ERROR in api_setup_tushare_token: {error_message}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=error_message)

# --- MCP Tool Functions ---
@mcp.tool()
def search_stocks(keyword: str) -> str:
    """
    搜索股票

    参数:
        keyword: 关键词（可以是股票代码的一部分或股票名称的一部分）
    """
    print(f"DEBUG: Tool search_stocks called with keyword: '{keyword}'.", file=sys.stderr, flush=True)
    token_value = get_tushare_token()
    if not token_value:
        return "错误：Tushare token 未配置或无法获取。请使用 setup_tushare_token 配置。"
    try:
        pro = ts.pro_api(token_value)
        df = pro.stock_basic()
        mask = (df['ts_code'].str.contains(keyword, case=False, na=False)) | \
               (df['name'].str.contains(keyword, case=False, na=False))
        results_df = df[mask]
        if results_df.empty:
            return "未找到符合条件的股票"
        output = []
        for _, row in results_df.iterrows():
            output.append(f"{row['ts_code']} - {row['name']}")
        return "\n".join(output)
    except Exception as e:
        print(f"DEBUG: ERROR in search_stocks: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return f"搜索股票失败：{str(e)}"

@mcp.tool()
def get_daily_prices(ts_code: str, trade_date: str = None, start_date: str = None, end_date: str = None) -> str:
    """
    获取指定股票在特定交易日或一段时期内的开盘价、最高价、最低价和收盘价。

    参数:
        ts_code: 股票代码 (例如: 600126.SH)
        trade_date: 交易日期 (YYYYMMDD格式, 例如: 20250227)。与 start_date/end_date 互斥。
        start_date: 开始日期 (YYYYMMDD格式)。需与 end_date 一同使用。
        end_date: 结束日期 (YYYYMMDD格式)。需与 start_date 一同使用。
    """
    print(f"DEBUG: Tool get_daily_prices called with ts_code: '{ts_code}', trade_date: '{trade_date}', start_date: '{start_date}', end_date: '{end_date}'.", file=sys.stderr, flush=True)
    token_value = get_tushare_token()
    if not token_value:
        return "错误：Tushare token 未配置或无法获取。请使用 setup_tushare_token 配置。"

    if not ((trade_date and not (start_date or end_date)) or ((start_date and end_date) and not trade_date)):
        return "错误：请提供 trade_date (用于单日查询) 或 start_date 和 end_date (用于区间查询)。"

    try:
        pro = ts.pro_api(token_value)
        api_params = {'ts_code': ts_code, 'fields': 'ts_code,trade_date,open,high,low,close,vol,amount'}
        if trade_date:
            api_params['trade_date'] = trade_date
        if start_date and end_date:
            api_params['start_date'] = start_date
            api_params['end_date'] = end_date

        df = pro.daily(**api_params)

        if df.empty:
            if trade_date:
                return f"未找到 {ts_code} 在 {trade_date} 的日线行情数据。"
            else:
                return f"未找到 {ts_code} 在 {start_date} 到 {end_date} 期间的日线行情数据。"

        df_sorted = df.sort_values(by='trade_date', ascending=False)
        
        results = []
        stock_name = _get_stock_name(pro, ts_code)
        if trade_date:
            results.append(f"--- {stock_name} ({ts_code}) {trade_date} 价格信息 ---")
        else:
            results.append(f"--- {stock_name} ({ts_code}) {start_date} to {end_date} 价格信息 ---")

        for index, row in df_sorted.iterrows():
            date_str = row['trade_date']
            results.append(f"\n日期: {date_str}")
            price_fields = {
                'open': '开盘价', 'high': '最高价', 'low': '最低价',
                'close': '收盘价', 'vol': '成交量', 'amount': '成交额'
            }
            for field, label in price_fields.items():
                if field in row and pd.notna(row[field]):
                    try:
                        numeric_value = pd.to_numeric(row[field])
                        if field == 'vol':
                            unit = '手'
                            results.append(f"  {label}: {numeric_value:,.0f} {unit}")
                        elif field == 'amount':
                            unit = '千元'
                            results.append(f"  {label}: {numeric_value:,.2f} {unit}")
                        else:
                            unit = '元'
                            results.append(f"  {label}: {numeric_value:.2f} {unit}")
                    except (ValueError, TypeError):
                        results.append(f"  {label}: (值非数字: {row[field]})")
                else:
                    results.append(f"  {label}: 未提供")
        return "\n".join(results)
    except Exception as e:
        print(f"DEBUG: ERROR in get_daily_prices: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return f"获取日线行情失败：{str(e)}"

@mcp.tool()
def get_start_date_for_n_days(end_date: str, days_ago: int = 80) -> str:
    """
    根据结束日期和天数，获取Tushare交易日历上的起始日期。

    参数:
        end_date: str, 结束日期 (格式：YYYYMMDD)
        days_ago: int, 需要回溯的交易日天数 (默认为80)
    """
    print(f"DEBUG: Tool get_start_date_for_n_days called with end_date='{end_date}', days_ago={days_ago}.", file=sys.stderr, flush=True)
    token_value = get_tushare_token()
    if not token_value:
        return "错误：Tushare token 未配置或无法获取。请使用 setup_tushare_token 配置。"

    try:
        pro = ts.pro_api(token_value)
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        # 为了获取足够的日历数据，我们估算一个较早的开始日期
        # 通常交易日与日历日的比例约为 252/365 ≈ 0.7。为保险起见，我们用更大的乘数。
        estimated_days = int(days_ago / 0.5) # 更宽松地估计
        start_dt_estimated = end_dt - timedelta(days=estimated_days)
        start_date_estimated_str = start_dt_estimated.strftime('%Y%m%d')

        df = pro.trade_cal(start_date=start_date_estimated_str, end_date=end_date, is_open='1')

        if df.empty or len(df) < days_ago:
            return f"错误：无法获取足够的交易日数据。在 {start_date_estimated_str} 和 {end_date} 之间只找到了 {len(df)} 个交易日，需要 {days_ago} 个。"

        # 日期已经是升序排列的，我们取倒数第N个即可
        trading_days = df['cal_date'].sort_values(ascending=False).tolist()
        
        if len(trading_days) < days_ago:
             return f"错误：再次确认，交易日数据不足。在 {start_date_estimated_str} 和 {end_date} 之间只找到了 {len(trading_days)} 个交易日，需要 {days_ago} 个。"

        # 获取第N个交易日
        start_date_actual = trading_days[days_ago - 1]

        return f"查询成功。对于结束日期 {end_date}，往前 {days_ago} 个交易日的开始日期是: {start_date_actual}"

    except Exception as e:
        print(f"DEBUG: ERROR in get_start_date_for_n_days: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return f"计算起始日期失败：{str(e)}"

# --- SSE Integration ---
@app.get("/sse")
async def sse_endpoint(request: Request):
    transport = SseServerTransport(request)
    await mcp.handle_request(transport)
    return transport.response

# --- Initialize Tushare Token on Startup ---
@app.on_event("startup")
async def startup_event():
    print("DEBUG: Application startup event triggered.", file=sys.stderr, flush=True)
    token = get_tushare_token()
    if token:
        print("DEBUG: Tushare token found on startup, initializing API.", file=sys.stderr, flush=True)
        try:
            ts.set_token(token)
            print("DEBUG: Tushare API initialized successfully.", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"DEBUG: Failed to initialize Tushare API: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
    else:
        print("DEBUG: No Tushare token found on startup.", file=sys.stderr, flush=True)

# --- Main Entry Point ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("intraday:app", host="0.0.0.0", port=port, reload=True)