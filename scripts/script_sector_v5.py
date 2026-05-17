#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script_v5.py - V5版板块龙头股数据抓取

数据策略:
- mootdx quotes(1分钟): 价格/涨跌幅/开高低收/成交量/成交额/五档盘口
- 百度股市通PAE(1分钟): 真实主力净流入/超大单/大单/中单/小单
- 五档盘口差(1分钟): 辅助判断买盘/卖盘力量对比

无需东财/问财/百度技能,全部本地直连,零鉴权

用法:
  python3 script_v5.py              # 完整抓取
  python3 script_v5.py --realtime   # 只抓mootdx实时(0.3秒)
"""

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

SECTOR_FILE = Path("/root/.openclaw/workspace/sector_stocks_final.md")
DATA_DIR = Path("/root/.openclaw/workspace/data")

_BAIDU_HEADERS = {
    "Host": "finance.pae.baidu.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0",
    "Accept": "application/vnd.finance-web.v1+json",
    "Origin": "https://gushitong.baidu.com",
    "Referer": "https://gushitong.baidu.com/",
}


def parse_sector_md():
    """解析markdown股票清单"""
    stocks = {}
    current_sector = None
    with open(SECTOR_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            m = re.match(r"^#{3,4}\s+\d+\.\d+\s+(.+?)\s*[（(]", line)
            if m:
                current_sector = m.group(1).strip()
                if current_sector not in stocks:
                    stocks[current_sector] = []
                continue
            if current_sector and line.startswith("|") and not line.startswith("|:---"):
                parts = [p.strip() for p in line.split("|")]
                parts = [p for p in parts if p]
                if len(parts) >= 3:
                    try:
                        code = parts[1]
                        name = parts[2]
                        if re.match(r"^\d{6}$", code):
                            stocks[current_sector].append((code, name))
                    except Exception:
                        pass
    all_codes = []
    seen = set()
    for sector, items in stocks.items():
        for code, name in items:
            if code not in seen:
                all_codes.append((code, name, sector))
                seen.add(code)
    return stocks, all_codes


def fetch_mootdx(codes):
    """mootdx批量获取实时行情(含五档盘口)"""
    try:
        from mootdx.quotes import Quotes
    except ImportError:
        print("[ERROR] mootdx未安装: pip install mootdx")
        return {}

    def fmt(code):
        c = str(code).strip()
        return (1, c) if c.startswith(("6", "8")) else (0, c)

    total = len(codes)
    print(f"[mootdx] 共 {total} 只标的")

    tdx_items = []
    for code, name, sector in codes:
        market, tdx_code = fmt(code)
        tdx_items.append(
            {
                "market": market,
                "code": tdx_code,
                "name": name,
                "sector": sector,
                "raw_code": code,
            }
        )

    client = Quotes.factory(market="std", multithread=True, heartbeat=True)
    results = {}
    batch_size = 50

    start = time.time()
    for i in range(0, total, batch_size):
        batch = tdx_items[i : i + batch_size]
        symbols = [c["code"] for c in batch]
        markets = [c["market"] for c in batch]

        try:
            df = client.quotes(symbol=symbols, market=markets)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    tdx_code = str(row.get("code", "")).strip()
                    matched = [c for c in batch if c["code"] == tdx_code]
                    if not matched:
                        continue
                    item = matched[0]

                    price = float(row.get("price", 0))
                    last_close = float(row.get("last_close", price))
                    change_pct = 0
                    if last_close > 0:
                        change_pct = round((price - last_close) / last_close * 100, 2)

                    bids = {}
                    asks = {}
                    bid_total = 0
                    ask_total = 0
                    for j in range(1, 6):
                        b_price = float(row.get(f"bid{j}", 0))
                        b_vol = int(row.get(f"bid_vol{j}", 0))
                        a_price = float(row.get(f"ask{j}", 0))
                        a_vol = int(row.get(f"ask_vol{j}", 0))
                        bids[f"bid{j}"] = b_price
                        bids[f"bid_vol{j}"] = b_vol
                        asks[f"ask{j}"] = a_price
                        asks[f"ask_vol{j}"] = a_vol
                        bid_total += b_price * b_vol * 100
                        ask_total += a_price * a_vol * 100

                    book_diff = round(bid_total - ask_total, 2)

                    results[item["raw_code"]] = {
                        "code": item["raw_code"],
                        "name": item["name"],
                        "sector": item["sector"],
                        "price": price,
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "last_close": last_close,
                        "volume": int(row.get("vol", 0)),
                        "amount": float(row.get("amount", 0)),
                        "change_pct": change_pct,
                        "bids": bids,
                        "asks": asks,
                        "book_diff": book_diff,
                        "timestamp": datetime.now().isoformat(),
                    }
        except Exception as e:
            print(f"[WARN] Batch error: {e}")

        time.sleep(0.05)

    client.close()
    elapsed = time.time() - start
    success = sum(1 for v in results.values() if "error" not in v)
    print(f"[mootdx] 完成: {success}/{total} 成功, 耗时 {elapsed:.2f}秒")
    return results


def fetch_baidu_fund_flow(codes, max_workers=10):
    """百度PAE批量获取资金流向(主力净流入/超大单/大单)"""
    total = len(codes)
    print(f"[百度PAE] 共 {total} 只标的, 并发={max_workers}")

    today = datetime.now().strftime("%Y%m%d")
    results = {}

    def fetch_one(code):
        url = (
            f"https://finance.pae.baidu.com/vapi/v1/fundflow"
            f"?code={code}&market=ab&date={today}&finClientType=pc"
        )
        try:
            r = requests.get(url, headers=_BAIDU_HEADERS, timeout=10)
            d = r.json()
            if str(d.get("ResultCode", -1)) != "0":
                return (code, None)

            raw = d.get("Result", {}).get("update_data", "")
            if not raw:
                return (code, None)

            rows = []
            for segment in raw.split(";"):
                parts = segment.split(",")
                if len(parts) >= 9:
                    rows.append(
                        {
                            "time": parts[0],
                            "mainForce": float(parts[2]) if parts[2] else 0,
                            "retail": float(parts[3]) if parts[3] else 0,
                            "super": float(parts[4]) if parts[4] else 0,
                            "large": float(parts[5]) if parts[5] else 0,
                            "price": float(parts[8]) if parts[8] else 0,
                        }
                    )

            if not rows:
                return (code, None)

            # 汇总全天
            total_main = sum(r["mainForce"] for r in rows)
            total_retail = sum(r["retail"] for r in rows)
            total_super = sum(r["super"] for r in rows)
            total_large = sum(r["large"] for r in rows)
            last = rows[-1]

            return (
                code,
                {
                    "main_force": round(total_main, 2),
                    "retail": round(total_retail, 2),
                    "super": round(total_super, 2),
                    "large": round(total_large, 2),
                    "medium": round(total_main - total_super - total_large, 2),
                    "little": round(total_retail, 2),
                    "last_time": last["time"],
                    "data_points": len(rows),
                },
            )
        except Exception as e:
            return (code, {"error": str(e)})

    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_one, c[0]): c[0] for c in codes}
        for f in as_completed(futures):
            code, data = f.result()
            if data:
                results[code] = data

    elapsed = time.time() - start
    success = sum(1 for v in results.values() if "error" not in v)
    print(f"[百度PAE] 完成: {success}/{total} 成功, 耗时 {elapsed:.2f}秒")
    return results


def merge_data(mootdx_data, baidu_data):
    """合并mootdx和百度PAE数据"""
    merged = {}
    for code, m_data in mootdx_data.items():
        b_data = baidu_data.get(code, {})
        merged[code] = {
            **m_data,
            "main_force": b_data.get("main_force", 0) if "error" not in b_data else 0,
            "retail": b_data.get("retail", 0) if "error" not in b_data else 0,
            "super": b_data.get("super", 0) if "error" not in b_data else 0,
            "large": b_data.get("large", 0) if "error" not in b_data else 0,
            "medium": b_data.get("medium", 0) if "error" not in b_data else 0,
            "little": b_data.get("little", 0) if "error" not in b_data else 0,
            "has_fund_flow": code in baidu_data and "error" not in baidu_data.get(code, {}),
            "fund_flow_time": b_data.get("last_time", "") if "error" not in b_data else "",
        }
    return merged


def organize_by_sector(data):
    """按板块组织并排序"""
    sectors = {}
    for code, item in data.items():
        if "error" in item:
            continue
        sector = item.get("sector", "未知")
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(item)

    for sector in sectors:
        sectors[sector].sort(key=lambda x: x.get("change_pct", 0), reverse=True)

    return sectors


def save_dashboard(data, sectors):
    """保存看板数据"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "total": len(data),
        "success": sum(1 for v in data.values() if "error" not in v),
        "has_fund_flow": sum(1 for v in data.values() if v.get("has_fund_flow")),
        "sector_data": sectors,
        "raw_data": data,
    }

    out = DATA_DIR / "dashboard_v5.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"[SAVE] {out}")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--realtime", action="store_true", help="只抓mootdx实时")
    parser.add_argument("--no-baidu", action="store_true", help="跳过百度PAE资金流向")
    args = parser.parse_args()

    print("=" * 60)
    print("板块龙头股 V5 数据抓取 (mootdx+百度PAE)")
    print("=" * 60)

    sector_stocks, all_codes = parse_sector_md()
    print(f"[INFO] 解析到 {len(all_codes)} 只标的, {len(sector_stocks)} 个细分")

    # mootdx实时层
    print("\n" + "=" * 60)
    print("[1/2] mootdx实时层 (价格/盘口/盘口差)")
    print("=" * 60)
    mootdx_data = fetch_mootdx(all_codes)

    # 百度PAE资金流向
    baidu_data = {}
    if not args.no_baidu:
        print("\n" + "=" * 60)
        print("[2/2] 百度PAE资金流向 (主力净流入/超大单/大单)")
        print("=" * 60)
        baidu_data = fetch_baidu_fund_flow(all_codes)

    # 合并并保存
    print("\n" + "=" * 60)
    print("[MERGE] 合并数据")
    print("=" * 60)
    merged = merge_data(mootdx_data, baidu_data)
    sectors = organize_by_sector(merged)
    save_dashboard(merged, sectors)

    # 打印统计
    print(f"\n{'='*60}")
    print("[SUMMARY] 板块强度排行")
    print(f"{'='*60}")
    sector_stats = []
    for name, stocks in sectors.items():
        if not stocks:
            continue
        avg_change = sum(s.get("change_pct", 0) for s in stocks) / len(stocks)
        total_main = sum(s.get("main_force", 0) for s in stocks)
        total_book = sum(s.get("book_diff", 0) for s in stocks)
        up_count = sum(1 for s in stocks if s.get("change_pct", 0) > 0)
        has_ff = sum(1 for s in stocks if s.get("has_fund_flow"))
        sector_stats.append(
            {
                "name": name,
                "avg": avg_change,
                "main": total_main,
                "book": total_book,
                "up": up_count,
                "total": len(stocks),
                "has_ff": has_ff,
                "top": stocks[0] if stocks else None,
            }
        )

    sector_stats.sort(key=lambda x: x["avg"], reverse=True)
    for s in sector_stats:
        top_str = (
            f"{s['top']['name']} {s['top']['change_pct']:+.2f}%"
            if s["top"]
            else "-"
        )
        main_str = f"主力{fmtm(s['main'])}" if s["has_ff"] > 0 else f"盘口差{fmtm(s['book'])}"
        print(
            f"  {s['name']:22s} | 平均 {s['avg']:+.2f}% | {s['up']}/{s['total']}涨 | {main_str} | 领涨: {top_str}"
        )

    print("\n[OK] 完成!")


def fmtm(v):
    v = float(v) if v else 0
    if abs(v) >= 1e8:
        return f"{v/1e8:+.1f}亿"
    elif abs(v) >= 1e4:
        return f"{v/1e4:+.1f}万"
    return f"{v:+.0f}"


if __name__ == "__main__":
    main()
