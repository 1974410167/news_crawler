# News Service MVP

Cloud-based news collection and query service for stock-related news.

## Features

- **Multi-source ingestion**: SEC EDGAR, Google News RSS, Company IR, Longbridge
- **Deduplication**: SHA256-based dedup with URL/title normalization
- **Query API**: FastAPI with X-API-Key authentication
- **Scheduled runs**: cron-based hourly ingestion

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your API key
vim .env

# Start services
docker-compose up -d

# Run ingestion manually
./scripts/run_ingest.sh

# Test API
curl -H "X-API-Key: your-key" http://localhost:8000/v1/health
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /v1/health | GET | Health check |
| /v1/news/search | GET | Search by symbol |
| /v1/news/search/batch | POST | Batch search |
| /v1/ingest/run | POST | Trigger ingestion |

## Cron Setup

```bash
# Edit crontab
crontab -e

# Add hourly job (runs at minute 0)
0 * * * * cd ~/news_service && ./scripts/run_ingest.sh >> /var/log/news_ingest.log 2>&1
```

## Database Schema

news_items table:
- id (UUID), symbol, title, url, source
- evidence_type (official/media)
- category (filing/earnings/company_news)
- published_at, origin_publisher, summary_text
- dedup_key (unique), inserted_at

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| NEWS_API_KEY | dev-api-key | API authentication key |
| DATABASE_URL | postgresql://... | Database connection |
| INGEST_SOURCES | sec_edgar,google_news | Comma-separated sources |
| DEFAULT_DAYS | 3 | Default query window |
| USER_AGENT | news_service/1.0 | User-Agent for requests |
