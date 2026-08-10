#!/usr/bin/env python3
"""
东财板块数据抓取脚本 - 14板块实时监控
使用 push2delay.eastmoney.com API
简化版：只保留涨幅+主力净流入，2分钟扫描间隔
"""
import requests
import json
import time
import os
import sys
from datetime import datetime

# ========== 配置 ==========
PLATES = [
    ("PCB", "BK0877"),
    ("MLCC", "BK0890"),
    ("半导体", "BK1036"),
    ("存储芯片", "BK1137"),
    ("先进封装", "BK1101"),
    ("创新药", "BK1106"),
    ("光通信", "BK1136"),
    ("银行", "BK1283"),
    ("有色金属", "BK0478"),
    ("AI应用", "BK1629"),
    ("机器人", "BK1408"),
    ("算力", "BK1134"),
    ("半导体材料", "BK1325"),
    ("电网设备", "BK0457"),
]

API_URL = "https://push2delay.eastmoney.com/api/qt/ulist.np/get"
FIELDS = "f12,f14,f3,f62,f184"  # 只取核心3个字段
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com/",
}

# 数据保存目录
DATA_DIR = "/root/.openclaw/workspace/stock-review/data"
os.makedirs(DATA_DIR, exist_ok=True)

# 扫描间隔(秒)
SCAN_INTERVAL = 120


def fetch_plate_data():
    """抓取14个板块数据"""
    secids = ",".join([f"90.{code}" for _, code in PLATES])
    params = {
        "secids": secids,
        "fields": FIELDS,
        "np": "1",
        "fltt": "2",
        "invt": "2",
    }
    
    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
        data = resp.json()
        
        if data.get("rc") != 0:
            print(f"API返回错误: {data}")
            return None
            
        items = data["data"]["diff"]
        return items
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def parse_data(items):
    """解析数据为结构化字典"""
    result = []
    for item in items:
        result.append({
            "name": item.get("f14", ""),
            "code": item.get("f12", ""),
            "change": round(item.get("f3", 0), 2),  # 涨跌幅%
            "fund": round(item.get("f62", 0) / 1e8, 1),  # 主力净流入(亿)
            "fund_ratio": round(item.get("f184", 0), 2),  # 主力净占比%
        })
    return result


def save_data(data):
    """保存数据到JSON文件"""
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H:%M:%S")
    
    filepath = os.path.join(DATA_DIR, f"{today_str}.json")
    
    # 读取已有数据
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                all_data = json.load(f)
                if not isinstance(all_data, dict):
                    all_data = {}
        except:
            all_data = {}
    else:
        all_data = {}
    
    # 添加新时间点数据
    all_data[time_str] = data
    
    # 保存
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    return filepath


def print_table(data):
    """打印数据表格"""
    print(f"\n{'='*60}")
    print(f"【东财板块数据】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"{'板块':<12} {'涨幅':>8} {'主力净流入':>14} {'净占比':>8}")
    print("-" * 60)
    
    for item in sorted(data, key=lambda x: x["change"], reverse=True):
        print(f"{item['name']:<12} {item['change']:>+7.2f}% {item['fund']:>+13.1f}亿 "
              f"{item['fund_ratio']:>+7.2f}%")
    
    print("=" * 60)


def run_once():
    """单次抓取"""
    items = fetch_plate_data()
    if not items:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取失败，跳过")
        return False
    
    data = parse_data(items)
    print_table(data)
    
    filepath = save_data(data)
    print(f"✅ 已保存: {filepath} ({datetime.now().strftime('%H:%M:%S')})")
    return True


def main():
    """主函数"""
    loop_mode = "--loop" in sys.argv
    
    if loop_mode:
        print(f"🚀 启动循环模式，每 {SCAN_INTERVAL} 秒(2分钟)抓取一次")
        print("   按 Ctrl+C 停止\n")
        try:
            while True:
                run_once()
                time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n⏹️ 已停止")
    else:
        run_once()


if __name__ == "__main__":
    main()
