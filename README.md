# Tushare Intraday API

这是一个基于 Tushare API 的日内交易数据服务，提供股票搜索、日线行情和交易日历计算功能，支持通过 SSE（Server-Sent Events）进行实时数据传输。

## 功能特点

- **股票搜索**：通过关键词搜索股票代码和名称
- **日线行情**：获取指定股票在特定交易日或一段时期内的价格数据
- **交易日历计算**：根据结束日期和天数，计算 Tushare 交易日历上的起始日期
- **SSE 支持**：通过 Server-Sent Events 提供实时数据流
- **安全的 Token 配置**：提供 Tushare API Token 的安全配置与状态检查机制

## 环境要求

- Python 3.10+
- Tushare API Token

## 快速开始

### 本地运行

1. 克隆仓库

```bash
git clone <repository-url>
cd intraday
```

2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 运行服务

```bash
python intraday.py
```

服务将在 http://localhost:8080 上启动。

### 使用 Docker 运行

1. 构建 Docker 镜像

```bash
docker build -t tushare-intraday .
```

2. 运行 Docker 容器

```bash
docker run -p 8080:8080 -e TUSHARE_TOKEN=your_token_here tushare-intraday
```

### 部署到 Google Cloud Run

1. 构建并推送 Docker 镜像到 Google Container Registry

```bash
gcloud builds submit --tag gcr.io/your-project-id/tushare-intraday
```

2. 部署到 Cloud Run

```bash
gcloud run deploy tushare-intraday \
  --image gcr.io/your-project-id/tushare-intraday \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="TUSHARE_TOKEN=your_token_here"
```

## API 使用

### 设置 Tushare Token

```
POST /tools/setup_tushare_token
Content-Type: application/json

{
  "token": "your_tushare_token_here"
}
```

### 通过 SSE 使用工具

连接到 SSE 端点：

```
GET /sse
```

然后可以使用以下工具：

1. **搜索股票**

```json
{
  "tool": "search_stocks",
  "params": {
    "keyword": "平安"
  }
}
```

2. **获取日线行情**

```json
{
  "tool": "get_daily_prices",
  "params": {
    "ts_code": "000001.SZ",
    "trade_date": "20230301"
  }
}
```

或者按日期范围查询：

```json
{
  "tool": "get_daily_prices",
  "params": {
    "ts_code": "000001.SZ",
    "start_date": "20230101",
    "end_date": "20230131"
  }
}
```

3. **计算交易日历起始日期**

```json
{
  "tool": "get_start_date_for_n_days",
  "params": {
    "end_date": "20230301",
    "days_ago": 20
  }
}
```

## 许可证

MIT