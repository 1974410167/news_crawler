# News Service API 完整文档

📰 全球新闻采集服务 - 提供个股新闻和宏观新闻的采集、存储、查询 API

---

## 📋 目录

1. [服务概览](#服务概览)
2. [认证方式](#认证方式)
3. [API 接口列表](#api-接口列表)
4. [接口详细说明](#接口详细说明)
5. [公网访问方案](#公网访问方案)
6. [示例代码](#示例代码)

---

## 服务概览

### 基础信息

| 项目 | 值 |
|------|-----|
| **API 地址** | `http://localhost:8000` |
| **API 密钥** | `news-api-key-2026` |
| **数据源** | SEC/Yahoo/Google/SeekingAlpha/Reuters/CNBC/Bloomberg/FT |
| **数据量** | ~430 条/24 小时 |
| **部署方式** | Docker Compose |

### 架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  数据采集层  │────▶│  PostgreSQL  │────▶│  FastAPI    │
│  (每 2 小时)   │     │  (newsdb)    │     │  (:8000)    │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   用户/API  │
                                         │   调用者    │
                                         └─────────────┘
```

---

## 认证方式

所有 API 请求需要在 Header 中包含 API Key：

```http
X-API-Key: news-api-key-2026
```

---

## API 接口列表

| 接口 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 健康检查 | GET | `/v1/health` | 检查服务和数据库状态 |
| 搜索个股新闻 | GET | `/v1/news/search` | 搜索单只股票新闻 |
| 批量搜索 | POST | `/v1/news/search/batch` | 批量搜索多只股票 |
| 手动采集 | POST | `/v1/ingest/run` | 手动触发新闻采集 |
| 统计摘要 | GET | `/v1/stats/summary` | 获取新闻统计摘要 |
| 宏观专项 | GET | `/v1/stats/macro` | 宏观新闻专项统计 |

---

## 接口详细说明

### 1. 健康检查

**接口**: `GET /v1/health`

**描述**: 检查 API 服务和数据库连接状态

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 描述 |
|------|------|------|------|------|
| X-API-Key | Header | string | 是 | API 密钥 |

**响应示例**:
```json
{
  "status": "ok",
  "db_status": "ok",
  "timestamp": "2026-03-06T14:00:00.000000"
}
```

**字段说明**:
- `status`: 服务状态 (ok/degraded)
- `db_status`: 数据库状态 (ok/error: xxx)
- `timestamp`: 当前时间戳

---

### 2. 搜索个股新闻

**接口**: `GET /v1/news/search`

**描述**: 搜索指定股票的最新新闻

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|------|--------|------|
| symbol | query | string | 是 | - | 股票代码 (如 AAPL) |
| days | query | int | 否 | 3 | 搜索最近 N 天 (1-30) |
| limit | query | int | 否 | 20 | 返回数量 (1-100) |
| source | query | string | 否 | - | 指定数据源 |

**请求示例**:
```bash
curl "http://localhost:8000/v1/news/search?symbol=AAPL&days=7&limit=20" \
  -H "X-API-Key: news-api-key-2026"
```

**响应示例**:
```json
[
  {
    "id": "uuid-string",
    "symbol": "AAPL",
    "title": "Apple Announces New Product Launch",
    "url": "https://example.com/news/123",
    "source": "google_news",
    "evidence_type": "news",
    "category": "company_news",
    "published_at": "2026-03-06T10:00:00",
    "origin_publisher": "Reuters",
    "summary_text": "Apple today announced...",
    "dedup_key": "abc123...",
    "inserted_at": "2026-03-06T10:05:00"
  }
]
```

**字段说明**:
- `id`: 新闻唯一 ID (UUID)
- `symbol`: 股票代码
- `title`: 新闻标题
- `url`: 原文链接
- `source`: 数据源 (google_news/sec_edgar/yahoo_finance 等)
- `evidence_type`: 证据类型 (news/filing/insider 等)
- `category`: 分类 (company_news/earnings/filing/macro 等)
- `published_at`: 新闻发布时间
- `origin_publisher`: 原始发布媒体
- `summary_text`: 新闻摘要
- `dedup_key`: 去重标识
- `inserted_at`: 入库时间

---

### 3. 批量搜索

**接口**: `POST /v1/news/search/batch`

**描述**: 批量搜索多只股票的最新新闻（自动覆盖全部数据源）

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|------|--------|------|
| symbols | body | array | 是 | - | 股票代码列表 |
| days | body | int | 否 | 3 | 搜索最近 N 天 |
| limit_per_symbol | body | int | 否 | 5 | 每只股票返回数量 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/v1/news/search/batch" \
  -H "X-API-Key: news-api-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"], "days": 3, "limit_per_symbol": 10}'
```

**响应示例**:
```json
{
  "results": {
    "AAPL": [...],
    "MSFT": [...],
    "GOOGL": [...]
  }
}
```

---

### 4. 手动触发采集

**接口**: `POST /v1/ingest/run`

**描述**: 手动触发新闻采集任务（自动使用全部数据源）

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|------|--------|------|
| symbols | body | array | 否 | ["AMD","INTC","MSFT"] | 股票代码列表 |
| days | body | int | 否 | 3 | 采集最近 N 天 |
| include_macro | body | bool | 否 | true | 是否包含宏观新闻 |

**响应示例**:
```json
{
  "fetched_total": 150,
  "inserted_total": 45,
  "dedup_skipped": 100,
  "errors_by_source": {},
  "macro_fetched": 20,
  "macro_inserted": 5
}
```

---

### 5. 统计摘要

**接口**: `GET /v1/stats/summary`

**描述**: 获取指定时间范围内的新闻统计摘要

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|------|--------|------|
| hours | query | int | 否 | 24 | 统计最近 N 小时 (1-168) |

**请求示例**:
```bash
curl "http://localhost:8000/v1/stats/summary?hours=24" \
  -H "X-API-Key: news-api-key-2026"
```

**响应示例**:
```json
{
  "status": "ok",
  "period": {
    "start": "2026-03-05T14:00:00",
    "end": "2026-03-06T14:00:00",
    "hours": 24
  },
  "summary": {
    "total": 435,
    "by_category": {
      "company_news": 220,
      "insider": 140,
      "filing": 25,
      "macro": 20,
      "earnings": 5
    },
    "by_source": {
      "google_news": 180,
      "sec_edgar": 170,
      "yahoo_finance": 40
    },
    "by_symbol": {
      "META": 60,
      "AMD": 58,
      "MSFT": 45
    },
    "macro_count": 20,
    "period_start": "2026-03-05T14:00:00",
    "period_end": "2026-03-06T14:00:00"
  },
  "all_time_total": 1250
}
```

---

### 6. 宏观新闻专项

**接口**: `GET /v1/stats/macro`

**描述**: 获取宏观新闻专项统计和最新列表

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|------|--------|------|
| hours | query | int | 否 | 24 | 统计最近 N 小时 |

**响应示例**:
```json
{
  "total": 20,
  "period_hours": 24,
  "by_source": {
    "macro_ft_economics": 13,
    "macro_cnbc_economy": 4
  },
  "latest": [
    {
      "title": "Fed signals potential rate cut",
      "source": "macro_cnbc_economy",
      "published_at": "2026-03-06T10:00:00"
    }
  ]
}
```

---

## 公网访问方案

### 方案 1: Cloudflare Tunnel（推荐 ⭐⭐⭐⭐⭐）

**优点**: 免费、安全、无需公网 IP、自动 HTTPS

**步骤**:

1. **安装 cloudflared**
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

2. **登录 Cloudflare**
```bash
cloudflared tunnel login
```

3. **创建 Tunnel**
```bash
cloudflared tunnel create news-api
```

4. **配置路由** (`~/.cloudflared/config.yml`)
```yaml
tunnel: news-api
credentials-file: /root/.cloudflared/xxx.json

ingress:
  - hostname: news-api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

5. **启动 Tunnel**
```bash
cloudflared tunnel run news-api
```

6. **配置 DNS**
在 Cloudflare Dashboard 添加 CNAME 记录

**访问地址**: `https://news-api.yourdomain.com`

---

### 方案 2: Nginx 反向代理 + 公网 IP（⭐⭐⭐⭐）

**前提**: 服务器有公网 IP

**步骤**:

1. **安装 Nginx**
```bash
sudo apt update && sudo apt install nginx
```

2. **配置 Nginx** (`/etc/nginx/sites-available/news-api`)
```nginx
server {
    listen 80;
    server_name news-api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **配置 SSL** (Let's Encrypt)
```bash
sudo certbot --nginx -d news-api.yourdomain.com
```

**访问地址**: `https://news-api.yourdomain.com`

---

### 方案 3: Ngrok（快速测试 ⭐⭐⭐）

**步骤**:
```bash
# 安装
npm install -g ngrok

# 启动
ngrok http 8000
```

**访问地址**: `https://xxx.ngrok.io` (每次变化)

---

### 方案 4: Docker 端口映射 + 防火墙（⭐⭐）

**最简单，但安全性较低**

1. **配置防火墙**
```bash
sudo ufw allow from YOUR_IP to any port 8000
```

**访问地址**: `http://YOUR_SERVER_IP:8000`

---

## 示例代码

### Python

```python
import requests

API_BASE = "https://news-api.yourdomain.com"
API_KEY = "news-api-key-2026"
headers = {"X-API-Key": API_KEY}

# 搜索新闻
response = requests.get(f"{API_BASE}/v1/news/search", params={"symbol": "AAPL", "days": 7}, headers=headers)
news_list = response.json()

# 获取统计
response = requests.get(f"{API_BASE}/v1/stats/summary", params={"hours": 24}, headers=headers)
stats = response.json()
print(f"过去 24 小时：{stats['summary']['total']} 条新闻")
```

### JavaScript

```javascript
const axios = require('axios');
const API_BASE = 'https://news-api.yourdomain.com';
const API_KEY = 'news-api-key-2026';

async function searchNews(symbol, days = 3) {
  const response = await axios.get(`${API_BASE}/v1/news/search`, {
    params: { symbol, days },
    headers: { 'X-API-Key': API_KEY }
  });
  return response.data;
}
```

### cURL

```bash
# 健康检查
curl https://news-api.yourdomain.com/v1/health -H "X-API-Key: news-api-key-2026"

# 搜索新闻
curl "https://news-api.yourdomain.com/v1/news/search?symbol=AAPL&days=7" -H "X-API-Key: news-api-key-2026"

# 获取统计
curl "https://news-api.yourdomain.com/v1/stats/summary?hours=24" -H "X-API-Key: news-api-key-2026"
```

---

## 安全建议

1. ✅ **必须使用 HTTPS** (Cloudflare Tunnel 或 Nginx + SSL)
2. ✅ **定期轮换 API Key**
3. ✅ **配置 IP 白名单** (如果可能)
4. ✅ **设置速率限制** (防止滥用)
5. ✅ **监控访问日志**

---

**文档版本**: v1.0  
**更新时间**: 2026-03-06  
**GitHub**: https://github.com/1974410167/news_crawler
