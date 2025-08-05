# Tushare MCP API

<div align="center">

**基于 Model Context Protocol (MCP) 封装的 Tushare 股票数据服务**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

</div>

---

## 项目简介
本项目利用 [Tushare](https://tushare.pro) 金融数据接口，并结合 [FastAPI](https://fastapi.tiangolo.com/) 与 [FastMCP](https://smithery.sh/docs/mcp/)，提供一套开箱即用的 **股票数据 API 服务**。你可以通过 HTTP 请求或 MCP 协议调用下列能力：

| 功能 | 说明 |
| ---- | ---- |
| Token 管理 | `setup_tushare_token`：配置 Tushare Token<br>`check_token_status`：检查 Token 有效性 |
| 日线行情 | `get_daily_prices`：查询单日或区间日线数据 |
| 周线行情 | `get_weekly_prices`：查询单只股票或指定交易周的周线行情 |
| 月线行情 | `get_monthly_prices`：查询月线行情 |
| 交易日历 | `get_trade_calendar`：获取交易所开市日列表 |
| 股票搜索 | `search_stocks`：按代码或名称关键字搜索股票 |
| MCP SSE | 内建 Server-Sent Events 通道，可在支持 MCP 的 IDE 里直接连接 |

> **注意**：README 已根据 `server.py` 当前功能进行同步；诸如 `hotlist.py` 等模块已移除或未实现，若后续添加请同步更新此文档。

---

## 快速开始

### 1. 克隆项目
```bash
$ git clone https://github.com/buuzzy/daylevel.git
$ cd daylevel
```

### 2. 创建并激活虚拟环境（推荐）
```bash
$ python -m venv venv
$ source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate     # Windows
```

### 3. 安装依赖
```bash
(venv) $ pip install -r requirements.txt
```

### 4. 配置 Tushare Token
项目运行前需先设置环境变量 `TUSHARE_TOKEN`，可通过两种方式完成：

1. **.env 文件（推荐）**  
   ```bash
   # 创建配置文件
   echo "TUSHARE_TOKEN=你的token" > ~/.tushare_mcp/.env
   ```
2. **临时环境变量**  
   ```bash
   export TUSHARE_TOKEN="你的token"   # macOS/Linux
   setx TUSHARE_TOKEN "你的token"      # Windows PowerShell
   ```

### 5. 启动服务
```bash
(venv) $ python server.py
```
启动成功后，默认监听 `127.0.0.1:8000`，根路径 `/` 返回健康检查信息。

---

## API 示例
所有接口均为 **POST/GET JSON**，示例基于 `curl`：

### 1. 设置 Token
```bash
curl -X POST http://127.0.0.1:8000/tools/setup_tushare_token \
     -H "Content-Type: application/json" \
     -d '{"token":"<your_token_here>"}'
```

### 2. 日线行情（单日）
```bash
curl -G http://127.0.0.1:8000/tools/get_daily_prices \
     --data-urlencode "ts_code=600519.SH" \
     --data-urlencode "trade_date=20250301"
```

更多接口与参数请参见 `server.py` 中函数注释。

---

## 在 IDE 中使用 MCP
1. 在支持 MCP 的 IDE（如 Cursor、Trae）中添加新服务器：
   - **SSE Endpoint**：`http://127.0.0.1:8000/sse`
2. 连接成功后，即可在对话中调用上述工具函数。

---

## 目录结构
```
├── server.py          # 主服务，定义所有工具与 FastAPI 路由
├── requirements.txt   # 依赖列表
├── Dockerfile         # （可选）容器化部署
├── LICENSE            # MIT 许可
└── README.md          # 项目说明
```

---

## 贡献指南
欢迎 Issue 与 PR！在提交新功能前，请确保：
1. 在 `server.py` 中实现对应工具；
2. 增加或更新 README 中的功能表格与示例；
3. 通过 `flake8` 或 `black` 格式化代码。

---

## License

MIT © 2024 buuzzy
