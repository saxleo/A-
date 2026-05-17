#!/bin/bash
# dashboard_update.sh - 板块龙头看板数据自动更新
# 每分钟抓取数据，每2分10秒推送到GitHub
# 跳过午休时段 11:30-13:30
# 开盘时间 9:30 开始

WORKSPACE="/root/.openclaw/workspace"
DATA_FILE="$WORKSPACE/data/dashboard_v5.json"
REPO_DIR="$WORKSPACE/stock-review"
LOCK_FILE="/tmp/dashboard_update.lock"
LAST_PUSH_FILE="/tmp/dashboard_last_push"
LOG_FILE="/tmp/dashboard_update.log"

# 获取当前时间（HHMM格式）
CURRENT_TIME=$(date +%H%M)

# 开盘前不运行（9:30前）
if [ "$CURRENT_TIME" -lt 930 ]; then
    exit 0
fi

# 跳过午休时段 11:30-13:30
if [ "$CURRENT_TIME" -ge 1130 ] && [ "$CURRENT_TIME" -le 1330 ]; then
    exit 0
fi

# 15:00后也不运行
if [ "$CURRENT_TIME" -gt 1500 ]; then
    exit 0
fi

# 防止并发执行
if [ -f "$LOCK_FILE" ]; then
    echo "[$(date '+%H:%M:%S')] 已有实例在运行，跳过" >> "$LOG_FILE"
    exit 0
fi
touch "$LOCK_FILE"

echo "[$(date '+%H:%M:%S')] 开始更新..." >> "$LOG_FILE"

# 1. 抓取数据
cd "$WORKSPACE" || exit 1
python3 script_v5.py --no-baidu >> "$LOG_FILE" 2>&1
FETCH_EXIT=$?

if [ $FETCH_EXIT -ne 0 ]; then
    echo "[$(date '+%H:%M:%S')] ❌ 数据抓取失败" >> "$LOG_FILE"
    rm "$LOCK_FILE"
    exit 1
fi

# 2. 复制数据到仓库
cp "$DATA_FILE" "$REPO_DIR/data/dashboard_v5.json"

# 3. 检查是否需要推送（每2分钟或数据有显著变化）
NOW=$(date +%s)
SHOULD_PUSH=0

if [ -f "$LAST_PUSH_FILE" ]; then
    LAST_PUSH=$(cat "$LAST_PUSH_FILE")
    DIFF=$((NOW - LAST_PUSH))
    if [ $DIFF -ge 130 ]; then
        SHOULD_PUSH=1
        echo "[$(date '+%H:%M:%S')] 距离上次推送${DIFF}秒，达到2分10秒阈值" >> "$LOG_FILE"
    fi
else
    SHOULD_PUSH=1
    echo "[$(date '+%H:%M:%S')] 首次运行，立即推送" >> "$LOG_FILE"
fi

if [ $SHOULD_PUSH -eq 1 ]; then
    cd "$REPO_DIR" || exit 1
    
    # 检查是否有变化
    git add data/dashboard_v5.json
    if git diff --cached --quiet; then
        echo "[$(date '+%H:%M:%S')] ⚠️ 数据无变化，跳过推送" >> "$LOG_FILE"
        echo "$NOW" > "$LAST_PUSH_FILE"
    else
        git commit -m "🔄 Auto-update $(date '+%m-%d %H:%M')" --quiet
        PUSH_EXIT=$?
        if [ $PUSH_EXIT -eq 0 ]; then
            git push origin main --quiet
            PUSH_EXIT=$?
            if [ $PUSH_EXIT -eq 0 ]; then
                echo "[$(date '+%H:%M:%S')] ✅ 推送成功" >> "$LOG_FILE"
                echo "$NOW" > "$LAST_PUSH_FILE"
            else
                echo "[$(date '+%H:%M:%S')] ❌ git push 失败" >> "$LOG_FILE"
            fi
        else
            echo "[$(date '+%H:%M:%S')] ❌ git commit 失败" >> "$LOG_FILE"
        fi
    fi
else
    echo "[$(date '+%H:%M:%S')] ⏳ 数据已存本地，未到推送时间" >> "$LOG_FILE"
fi

rm "$LOCK_FILE"
echo "[$(date '+%H:%M:%S')] 完成" >> "$LOG_FILE"
