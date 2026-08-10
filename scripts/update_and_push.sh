#!/bin/bash
# 板块数据定时抓取+推送脚本
# 每2分钟执行一次

REPO_DIR="/root/.openclaw/workspace/stock-review"
SCRIPT="$REPO_DIR/scripts/fetch_plates_em.py"
LOG_FILE="/tmp/plate_update.log"

# 抓取数据
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始抓取..." >> "$LOG_FILE"
cd "$REPO_DIR"

python3 "$SCRIPT" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 抓取失败" >> "$LOG_FILE"
    exit 1
fi

# Git 推送
git add data/*.json >> "$LOG_FILE" 2>&1
if git diff --cached --quiet; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 无新数据，跳过推送" >> "$LOG_FILE"
    exit 0
fi

git commit -m "板块数据更新 $(date '+%H:%M:%S')" >> "$LOG_FILE" 2>&1
git push origin main >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 推送成功" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 推送失败" >> "$LOG_FILE"
fi
