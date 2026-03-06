#!/bin/bash
# 每日新闻采集报告脚本
# 每天北京时间 10:00 执行，发送过去 24 小时统计

set -e

cd "$(dirname "$0")/.."

# 获取日期
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 开始生成新闻统计报告..."

# 使用 API 获取统计数据（更可靠）
STATS_JSON=$(curl -s "http://localhost:8000/v1/stats/summary?hours=24" \
  -H "X-API-Key: news-api-key-2026")

# 解析 JSON
TOTAL=$(echo "$STATS_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['summary']['total'])")
MACRO=$(echo "$STATS_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['summary']['macro_count'])")
ALL_TIME=$(echo "$STATS_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['all_time_total'])")

# 获取分类统计
CATEGORY_STATS=$(echo "$STATS_JSON" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for cat, count in d['summary']['by_category'].items():
    print(f'CATEGORY:{cat}:{count}')
")

# 获取来源统计
SOURCE_STATS=$(echo "$STATS_JSON" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for src, count in sorted(d['summary']['by_source'].items(), key=lambda x: -x[1])[:10]:
    print(f'SOURCE:{src}:{count}')
")

# 获取股票统计
SYMBOL_STATS=$(echo "$STATS_JSON" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for sym, count in sorted(d['summary']['by_symbol'].items(), key=lambda x: -x[1])[:10]:
    print(f'SYMBOL:{sym}:{count}')
")

echo "📊 统计结果：总计=$TOTAL, 宏观=$MACRO, 总量=$ALL_TIME"

# 构建消息内容
MESSAGE="📊 **新闻采集日报**
📅 统计时间：${YESTERDAY} ~ ${TODAY}

**过去 24 小时统计**
• 新增新闻：**${TOTAL} 条**
• 宏观新闻：**${MACRO} 条**
• 数据库总量：**${ALL_TIME} 条**

**按分类**
"

# 添加分类统计
while IFS=: read -r prefix cat count; do
    [ -n "$cat" ] && MESSAGE="${MESSAGE}• ${cat}: ${count} 条
"
done <<< "$CATEGORY_STATS"

MESSAGE="${MESSAGE}
**数据源 Top 10**
"

# 添加数据源统计
while IFS=: read -r prefix source count; do
    [ -n "$source" ] && MESSAGE="${MESSAGE}• ${source}: ${count} 条
"
done <<< "$SOURCE_STATS"

MESSAGE="${MESSAGE}
**热门股票 Top 10**
"

# 添加热门股票
while IFS=: read -r prefix symbol count; do
    [ -n "$symbol" ] && MESSAGE="${MESSAGE}• ${symbol}: ${count} 条
"
done <<< "$SYMBOL_STATS"

MESSAGE="${MESSAGE}
---
🤖 自动报告 | News Service"

# 通过 OpenClaw 发送到飞书
openclaw message send -t "ou_1f0dfac373311ed5ab5cb9de75539dcc" -m "$MESSAGE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 日报发送成功：${TOTAL} 条新闻"
