#!/bin/bash
# Run ingestion job manually

set -e
cd "$(dirname "$0")/.."

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default symbols (用户持仓)
SYMBOLS=${INGEST_SYMBOLS:-"AMD,AMZN,ARM,IBKR,INTC,META,MSFT,MSTR,QCOM,TSLA"}
DAYS=${DEFAULT_DAYS:-3}

echo "=== News Ingestion Job ==="
echo "Symbols: $SYMBOLS"
echo "Days: $DAYS"
echo "Sources: ${INGEST_SOURCES:-sec_edgar,google_news}"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Run ingestion
docker compose exec -T api python -m app.ingest.ingest_job

echo ""
echo "=== Ingestion Complete ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
