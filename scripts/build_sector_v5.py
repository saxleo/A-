#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_v5.py - V5看板构建脚本
读取 dashboard_v5.json，生成自包含的 index_v5.html

用法:
  python3 build_v5.py
"""

import json
from pathlib import Path
from datetime import datetime

DATA_FILE = Path("/root/.openclaw/workspace/data/dashboard_v5.json")
OUTPUT = Path("/root/.openclaw/workspace/sector_dashboard_v5.html")

def fmtm(v):
    v = float(v) if v else 0
    if abs(v) >= 1e8:
        return f"{v/1e8:+.1f}亿"
    elif abs(v) >= 1e4:
        return f"{v/1e4:+.1f}万"
    return f"{v:+.0f}"

def status_tag(avg):
    if avg >= 2.0: return ('主升🔴', 'tag-bull')
    elif avg >= 0.5: return ('震荡🟡', 'tag-sideways')
    elif avg >= -1.0: return ('蓄势⚪', 'tag-accum')
    return ('退潮🟢', 'tag-bear')

def build():
    if not DATA_FILE.exists():
        print("[ERROR] 未找到 dashboard_v5.json，请先运行 script_v5.py")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 主题映射
    SECTOR_MAP = {
        'AI芯片/GPU': '🔥 AI算力', '光芯片/硅光/薄膜铌酸锂': '🔥 AI算力',
        '光模块/CPO/光引擎': '🔥 AI算力', '铜缆高速连接': '🔥 AI算力',
        'PCB/高速连接板': '🔥 AI算力', '液冷散热': '🔥 AI算力',
        '先进封装/测试': '🔥 AI算力', 'EDA/IP': '🔥 AI算力',
        '半导体设备': '🔥 AI算力', '半导体材料': '🔥 AI算力',
        '晶圆代工/制造': '🔥 AI算力', '算力租赁/IDC': '🔥 AI算力',
        '光纤/光器件': '🔥 AI算力', '存力/HBM存储': '🔥 AI算力',
        'AI服务器': '🔥 AI算力',
        '核心零部件': '🤖 机器人', '整机/执行器/应用': '🤖 机器人',
        '整机+动力系统': '🤖 机器人', '设备+整车/应用': '🤖 机器人',
        '正负极材料+电解质': '🔋 新能源', '新型电力系统': '🔋 新能源',
        '储能+逆变器': '🔋 新能源',
        '航空装备+航天装备': '🚀 军工', '舰船+军工信息化': '🚀 军工',
        '卫星制造+应用': '🚀 军工', '火箭+地面设备+材料': '🚀 军工',
        '空管/雷达+碳纤维材料': '🚀 军工',
    }

    def get_theme(name):
        v = SECTOR_MAP.get(name, '💎 ' + name)
        parts = v.split()
        return parts[0], parts[1] if len(parts) > 1 else name

    # 按主题聚合
    by_theme = {}
    for sector_name, stocks in data['sector_data'].items():
        emoji, theme_name = get_theme(sector_name)
        if theme_name not in by_theme:
            by_theme[theme_name] = {'sectors': [], 'emoji': emoji}
        by_theme[theme_name]['sectors'].append({'name': sector_name, 'stocks': stocks})

    for theme, info in by_theme.items():
        all_s = []
        for s in info['sectors']:
            all_s.extend(s['stocks'])
        info['avg'] = round(sum(s.get('change_pct', 0) for s in all_s) / len(all_s), 2) if all_s else 0
        info['book'] = round(sum(s.get('book_diff', 0) for s in all_s), 2)
        info['main'] = round(sum(s.get('main_force', 0) for s in all_s if s.get('has_fund_flow')), 2)
        info['mf5d'] = round(sum(s.get('mf_5d', 0) for s in all_s), 2)
        info['has_ff'] = sum(1 for s in all_s if s.get('has_fund_flow'))
        info['up'] = sum(1 for s in all_s if s.get('change_pct', 0) > 0)
        info['total'] = len(all_s)
        info['all'] = sorted(all_s, key=lambda x: x.get('change_pct', 0), reverse=True)
        info['top'] = info['all'][0] if info['all'] else None
        sector_avgs = []
        for s in info['sectors']:
            if s['stocks']:
                sector_avgs.append((s['name'], sum(x.get('change_pct', 0) for x in s['stocks']) / len(s['stocks'])))
        sector_avgs.sort(key=lambda x: x[1], reverse=True)
        info['top_sector'] = sector_avgs[0][0] if sector_avgs else ''

    sorted_themes = sorted(by_theme.items(), key=lambda x: x[1]['avg'], reverse=True)

    # 市场异动TOP5
    all_stocks = []
    for s in data['sector_data'].values():
        all_stocks.extend(s)
    all_stocks.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
    top5 = all_stocks[:5]

    # 生成HTML
    html = generate_html(data, sorted_themes, top5, SECTOR_MAP)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] 看板生成: {OUTPUT}")
    print(f"     大小: {len(html)} bytes")


def generate_html(data, sorted_themes, top5, SECTOR_MAP):
    # CSS
    css = """
:root{--bg:#0a0e17;--card-bg:#111827;--elevated:#1f2937;--border:#374151;--text:#f3f4f6;--muted:#9ca3af;--up:#ef4444;--up-bg:rgba(239,68,68,0.1);--down:#22c55e;--down-bg:rgba(34,197,94,0.1);--accent:#3b82f6;--accent2:#8b5cf6;--gold:#f59e0b}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;line-height:1.5;min-height:100vh}
.fav-bar{position:fixed;top:0;left:0;right:0;z-index:100;height:56px;background:var(--card-bg);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;padding:0 20px;overflow-x:auto;scrollbar-width:thin}
.fav-bar::-webkit-scrollbar{height:3px}
.fav-bar::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.fav-label{font-size:16px;font-weight:700;white-space:nowrap;flex-shrink:0}
.fav-tag{display:flex;align-items:center;gap:6px;padding:4px 12px;background:var(--elevated);border-radius:20px;cursor:pointer;border:1px solid var(--border);white-space:nowrap;font-size:13px;transition:all .15s;flex-shrink:0}
.fav-tag:hover{border-color:var(--accent)}
.fav-tag .fav-name{font-weight:500}
.fav-tag .fav-pct{font-family:'SF Mono',Monaco,monospace;font-weight:700}
.fav-tag .fav-del{opacity:0;transition:opacity .15s;font-size:12px;color:var(--muted)}
.fav-tag:hover .fav-del{opacity:1}
.fav-add{padding:4px 12px;border:1px dashed var(--border);border-radius:20px;color:var(--muted);cursor:pointer;white-space:nowrap;font-size:13px;flex-shrink:0}
.fav-add:hover{border-color:var(--accent);color:var(--accent)}
.main{padding-top:72px;padding-bottom:24px}
.header{text-align:center;margin-bottom:24px;padding:0 20px}
.header h1{font-size:26px;font-weight:700;letter-spacing:1px}
.header .meta{color:var(--muted);font-size:12px;margin-top:6px}
.header .meta span{margin:0 8px}
.quick-movers{max-width:1600px;margin:0 auto 20px;padding:0 20px}
.qm-title{font-size:14px;font-weight:600;margin-bottom:10px;color:var(--gold)}
.qm-row{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px}
.qm-item{display:flex;align-items:center;gap:8px;padding:8px 14px;background:var(--card-bg);border:1px solid var(--border);border-radius:10px;font-size:13px;white-space:nowrap;cursor:pointer;transition:all .15s}
.qm-item:hover{border-color:var(--accent)}
.qm-code{color:var(--muted);font-size:11px}
.qm-pct{font-family:'SF Mono',Monaco,monospace;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;max-width:1600px;margin:0 auto;padding:0 20px}
@media(min-width:1400px){.grid{grid-template-columns:repeat(4,1fr)}}
@media(max-width:1024px){.grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:768px){.grid{grid-template-columns:repeat(2,1fr)}}
.card{background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:16px;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.card:hover{border-color:var(--accent);transform:translateY(-2px)}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-title{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:600}
.card-emoji{font-size:18px}
.card-meta{display:flex;gap:10px;align-items:center}
.card-tag{font-size:11px;padding:2px 8px;border-radius:6px;font-weight:500}
.tag-bull{background:var(--up-bg);color:var(--up)}
.tag-sideways{background:rgba(245,158,11,0.15);color:#f59e0b}
.tag-bear{background:var(--down-bg);color:var(--down)}
.tag-accum{background:rgba(59,130,246,0.15);color:var(--accent)}
.card-count{font-size:11px;color:var(--muted);background:var(--elevated);padding:2px 8px;border-radius:10px}
.card-stats{display:flex;gap:16px;margin-bottom:12px;font-size:13px}
.stat-item{display:flex;flex-direction:column}
.stat-label{font-size:11px;color:var(--muted);margin-bottom:2px}
.stat-val{font-family:'SF Mono',Monaco,monospace;font-weight:700;font-size:14px}
.card-sub-leader{font-size:12px;color:var(--accent);margin-bottom:10px;padding:4px 8px;background:rgba(59,130,246,0.1);border-radius:6px;display:inline-block}
.card-top3{display:flex;flex-direction:column;gap:6px}
.top3-row{display:flex;align-items:center;justify-content:space-between;padding:6px 8px;background:var(--elevated);border-radius:6px;font-size:12px}
.top3-name{font-weight:500}
.top3-code{color:var(--muted);font-size:10px;margin-left:4px}
.top3-pct{font-family:'SF Mono',Monaco,monospace;font-weight:700;font-size:13px}
.card-footer{display:flex;justify-content:space-between;margin-top:12px;font-size:11px;color:var(--muted)}
.page2{display:none;max-width:1600px;margin:0 auto;padding:0 20px}
.page2.active{display:block}
.breadcrumb{display:flex;align-items:center;gap:8px;margin-bottom:16px;font-size:14px}
.breadcrumb a{color:var(--accent);cursor:pointer}
.breadcrumb a:hover{text-decoration:underline}
.breadcrumb span{color:var(--muted)}
.sub-tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.sub-tab{padding:6px 14px;border-radius:8px;font-size:13px;cursor:pointer;border:1px solid var(--border);background:var(--card-bg);transition:all .15s}
.sub-tab:hover{border-color:var(--accent)}
.sub-tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.sub-tab .tab-pct{font-family:'SF Mono',Monaco,monospace;font-weight:700;margin-left:6px}
.sector-summary{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap}
.sum-box{background:var(--card-bg);border:1px solid var(--border);border-radius:10px;padding:14px 18px;min-width:140px}
.sum-label{font-size:11px;color:var(--muted);margin-bottom:4px}
.sum-val{font-size:20px;font-weight:700;font-family:'SF Mono',Monaco,monospace}
.stock-table{width:100%;border-collapse:collapse;font-size:13px}
.stock-table thead th{text-align:left;padding:10px 12px;color:var(--muted);font-weight:500;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--card-bg);white-space:nowrap;cursor:pointer;user-select:none}
.stock-table thead th:hover{color:var(--text)}
.stock-table td{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:middle}
.stock-table tbody tr{cursor:pointer;transition:background .1s}
.stock-table tbody tr:hover td{background:var(--elevated)}
.stock-table .rank{text-align:center;color:var(--muted);font-weight:600;width:40px}
.stock-table .name-cell{display:flex;flex-direction:column}
.stock-table .code-txt{font-size:11px;color:var(--muted)}
.stock-table .price,.stock-table .change,.stock-table .amount{font-family:'SF Mono',Monaco,monospace}
.stock-table .change{font-weight:700;text-align:right}
.stock-table .price{text-align:right}
.stock-table .amount{text-align:right;color:var(--muted);font-size:12px}
.stock-table .action-btns{display:flex;gap:8px}
.stock-table .btn-sm{padding:3px 8px;border-radius:4px;font-size:11px;border:none;cursor:pointer}
.btn-fav{background:rgba(245,158,11,0.2);color:var(--gold)}
.btn-detail{background:var(--accent);color:#fff}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:200;display:none;align-items:center;justify-content:center;padding:20px}
.overlay.active{display:flex}
.modal{background:var(--card-bg);border:1px solid var(--border);border-radius:16px;width:100%;max-width:720px;max-height:90vh;overflow-y:auto}
.modal-header{padding:18px 24px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.modal-title{font-size:18px;font-weight:600}
.modal-close{background:none;border:none;color:var(--muted);font-size:24px;cursor:pointer;line-height:1}
.modal-close:hover{color:var(--text)}
.modal-body{padding:20px 24px}
.kline-tabs{display:flex;gap:8px;margin-bottom:16px}
.kline-tab{padding:4px 12px;border-radius:6px;font-size:12px;cursor:pointer;border:1px solid var(--border);background:var(--elevated)}
.kline-tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.kline-canvas{width:100%;height:200px;background:var(--elevated);border-radius:8px;margin-bottom:16px}
.book-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.book-col h4{font-size:13px;margin-bottom:10px;color:var(--muted)}
.book-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px}
.book-row:last-child{border-bottom:none}
.book-price{font-family:'SF Mono',Monaco,monospace;font-weight:600}
.book-vol{color:var(--muted);font-size:11px}
.book-buy .book-price{color:var(--up)}
.book-sell .book-price{color:var(--down)}
.book-bar{height:3px;border-radius:2px;margin-top:2px}
.book-buy .book-bar{background:var(--up)}
.book-sell .book-bar{background:var(--down)}
.book-diff-box{background:var(--elevated);border-radius:8px;padding:12px 16px;margin-top:16px}
.book-diff-label{font-size:12px;color:var(--muted);margin-bottom:4px}
.book-diff-val{font-size:18px;font-weight:700;font-family:'SF Mono',Monaco,monospace}
.info-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
.info-item{background:var(--elevated);border-radius:8px;padding:10px 12px;text-align:center}
.info-label{font-size:11px;color:var(--muted);margin-bottom:2px}
.info-val{font-size:14px;font-weight:700;font-family:'SF Mono',Monaco,monospace}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--muted)}
@media(max-width:600px){.info-grid{grid-template-columns:repeat(2,1fr)}.book-grid{grid-template-columns:1fr}.card-stats{flex-wrap:wrap}}
"""

    # HTML body structure
    body = '<div class="fav-bar" id="favBar"><span class="fav-label">⭐ 自选</span><span class="fav-add" onclick="addFavPrompt()">+ 添加自选</span></div>'
    body += '<div class="main">'

    # Page 1
    body += '<div id="page1">'
    body += '<div class="header"><h1>🔥 板块龙头股监控看板 V5</h1>'
    body += f'<div class="meta"><span id="updateTime">{data["timestamp"][:19]}</span><span>·</span><span>143只龙头股</span><span>·</span><span id="refreshStatus">自动刷新中</span></div></div>'

    # Quick movers
    body += '<div class="quick-movers"><div class="qm-title">📈 市场异动 TOP5</div><div class="qm-row" id="quickMovers">'
    for s in top5:
        color = 'var(--up)' if s.get('change_pct', 0) >= 0 else 'var(--down)'
        body += f'<div class="qm-item" onclick="openStock(\'{s["code"]}\')">'
        body += f'<span class="qm-code">{s["code"]}</span><span>{s["name"]}</span>'
        body += f'<span class="qm-pct" style="color:{color}">{s["change_pct"]:+.2f}%</span></div>'
    body += '</div></div>'

    # Theme grid
    body += '<div class="grid" id="themeGrid">'
    for theme_name, info in sorted_themes:
        tag_text, tag_class = status_tag(info['avg'])
        book_color = 'var(--up)' if info['book'] >= 0 else 'var(--down)'
        avg_color = 'var(--up)' if info['avg'] >= 0 else 'var(--down)'
        main_color = 'var(--up)' if info['main'] >= 0 else 'var(--down)'
        mf5d_color = 'var(--up)' if info['mf5d'] >= 0 else 'var(--down)'
        body += f'<div class="card" onclick="goToTheme(\'{theme_name}\')">'
        body += '<div class="card-header">'
        body += f'<div class="card-title"><span class="card-emoji">{info["emoji"]}</span>{theme_name}</div>'
        body += f'<div class="card-meta"><span class="card-tag {tag_class}">{tag_text}</span><span class="card-count">{info["up"]}/{info["total"]}涨</span></div>'
        body += '</div>'
        body += '<div class="card-stats">'
        body += f'<div class="stat-item"><span class="stat-label">平均涨跌</span><span class="stat-val" style="color:{avg_color}">{info["avg"]:+.2f}%</span></div>'
        if info['has_ff'] > 0:
            body += f'<div class="stat-item"><span class="stat-label">主力净流</span><span class="stat-val" style="color:{main_color}">{fmtm(info["main"])}</span></div>'
        else:
            body += f'<div class="stat-item"><span class="stat-label">盘口差</span><span class="stat-val" style="color:{book_color}">{fmtm(info["book"])}</span></div>'
        body += f'<div class="stat-item"><span class="stat-label">上涨率</span><span class="stat-val">{info["up"]}/{info["total"]}</span></div>'
        body += f'<div class="stat-item"><span class="stat-label">5日主力净流</span><span class="stat-val" style="color:{mf5d_color}">{fmtm(info["mf5d"])}</span></div>'
        body += '</div>'
        if info['top_sector']:
            body += f'<div class="card-sub-leader">🏆 领涨细分: {info["top_sector"]}</div>'
        body += '<div class="card-top3">'
        for s in info['all'][:3]:
            pct_color = 'var(--up)' if s.get('change_pct', 0) >= 0 else 'var(--down)'
            main_txt = ''
            if s.get('has_fund_flow') and s.get('main_force'):
                mc = 'var(--up)' if s['main_force'] >= 0 else 'var(--down)'
                main_txt = f' <span style="color:{mc};font-size:10px">{fmtm(s["main_force"])}</span>'
            mf5d_txt = ''
            if s.get('mf_5d') is not None:
                mc5 = 'var(--up)' if s['mf_5d'] >= 0 else 'var(--down)'
                mf5d_txt = f' <span style="color:{mc5};font-size:10px">5日{fmtm(s["mf_5d"])}</span>'
            body += '<div class="top3-row">'
            body += f'<span><span class="top3-name">{s["name"]}</span><span class="top3-code">{s["code"]}</span>{main_txt}{mf5d_txt}</span>'
            body += f'<span class="top3-pct" style="color:{pct_color}">{s["change_pct"]:+.2f}%</span>'
            body += '</div>'
        body += '</div>'
        body += '<div class="card-footer">'
        top_name = info['top']['name'] if info['top'] else '-'
        top_pct = info['top']['change_pct'] if info['top'] else 0
        body += f'<span>领涨: {top_name} {top_pct:+.2f}%</span><span>点击查看全部</span>'
        body += '</div></div>'
    body += '</div></div>'

    # Page 2
    body += '<div id="page2" class="page2">'
    body += '<div class="breadcrumb"><a onclick="goToPage1()">📊 主题概览</a><span>/</span><span id="breadcrumbTheme"></span></div>'
    body += '<div class="sector-summary" id="sectorSummary"></div>'
    body += '<div class="sub-tabs" id="subTabs"></div>'
    body += '<div id="stockTableWrap"></div></div>'

    # Modal
    body += '<div id="overlay" class="overlay" onclick="closeModal(event)">'
    body += '<div class="modal" onclick="event.stopPropagation()">'
    body += '<div class="modal-header"><div class="modal-title" id="modalTitle"></div><button class="modal-close" onclick="closeModal()">×</button></div>'
    body += '<div class="modal-body">'
    body += '<div class="info-grid" id="infoGrid"></div>'
    body += '<div class="kline-tabs">'
    body += '<div class="kline-tab active" data-tab="book">📊 五档盘口</div>'
    body += '<div class="kline-tab" data-tab="kline">📈 走势</div>'
    body += '</div>'
    body += '<div id="tabContentBook">'
    body += '<div class="book-grid" id="bookGrid"></div>'
    body += '<div class="book-diff-box"><div class="book-diff-label">盘口差估算 (买盘力量 - 卖盘力量)</div><div class="book-diff-val" id="bookDiffVal"></div></div>'
    body += '</div>'
    body += '<div id="tabContentKline" style="display:none">'
    body += '<canvas class="kline-canvas" id="klineCanvas" width="672" height="200"></canvas>'
    body += '<p style="text-align:center;color:var(--muted);font-size:12px">基于开高低收数据的走势示意</p>'
    body += '</div></div></div></div>'

    body += '</div>'

    # JavaScript
    js_data = json.dumps(data['raw_data'], ensure_ascii=False, separators=(',', ':'))
    sector_data = json.dumps(data['sector_data'], ensure_ascii=False, separators=(',', ':'))
    theme_map = json.dumps(SECTOR_MAP, ensure_ascii=False, separators=(',', ':'))

    js = f"""
const RAW_DATA = {js_data};
const SECTOR_DATA = {sector_data};
const THEME_MAP = {theme_map};

let currentTheme = null;
let currentSector = null;
let currentStock = null;
let refreshTimer = null;

function getFavs(){{try{{return JSON.parse(localStorage.getItem('fav_stocks')||'[]');}}catch(e){{return[];}}}}
function setFavs(favs){{localStorage.setItem('fav_stocks',JSON.stringify(favs));renderFavBar();}}
function isFav(code){{return getFavs().includes(code);}}
function toggleFav(code){{let favs=getFavs();if(favs.includes(code))favs=favs.filter(c=>c!==code);else favs.push(code);setFavs(favs);}}
function addFavPrompt(){{const code=prompt('输入股票代码(6位数字):');if(code&&/^\\d{{6}}$/.test(code)){{let favs=getFavs();if(!favs.includes(code)){{favs.push(code);setFavs(favs);}}}}}}
function renderFavBar(){{
  const bar=document.getElementById('favBar');
  const favs=getFavs();
  let html='<span class="fav-label">⭐ 自选</span>';
  for(const code of favs){{
    const s=RAW_DATA[code];if(!s)continue;
    const color=s.change_pct>=0?'var(--up)':'var(--down)';
    html+=`<div class="fav-tag" onclick="openStock('${{code}}')">
      <span class="fav-name">${{s.name}}</span>
      <span class="fav-pct" style="color:${{color}}">${{s.change_pct>=0?'+':''}}${{s.change_pct.toFixed(2)}}%</span>
      <span class="fav-del" onclick="event.stopPropagation();toggleFav('${{code}}')">✕</span>
    </div>`;
  }}
  html+='<span class="fav-add" onclick="addFavPrompt()">+ 添加自选</span>';
  bar.innerHTML=html;
}}

function goToPage1(){{document.getElementById('page1').style.display='block';document.getElementById('page2').classList.remove('active');currentTheme=null;currentSector=null;}}
function goToTheme(themeName){{currentTheme=themeName;document.getElementById('page1').style.display='none';document.getElementById('page2').classList.add('active');document.getElementById('breadcrumbTheme').textContent=themeName;renderPage2();}}

function renderPage2(){{
  if(!currentTheme)return;
  const sectors=[];
  for(const[name,stocks] of Object.entries(SECTOR_DATA)){{
    const mapped=THEME_MAP[name]||'';
    if(mapped.includes(currentTheme))sectors.push({{name,stocks}});
  }}
  if(sectors.length===0)return;
  const allStocks=[];
  for(const s of sectors)allStocks.push(...s.stocks);
  const avg=allStocks.length?(allStocks.reduce((a,b)=>a+b.change_pct,0)/allStocks.length).toFixed(2):0;
  const book=allStocks.reduce((a,b)=>a+(b.book_diff||0),0);
  const main=allStocks.reduce((a,b)=>a+(b.main_force||0),0);
  const mf5d_all=allStocks.reduce((a,b)=>a+(b.mf_5d||0),0);
  const has_ff=allStocks.filter(s=>s.has_fund_flow).length;
  const up=allStocks.filter(s=>s.change_pct>0).length;
  document.getElementById('sectorSummary').innerHTML=`<div class="sum-box"><div class="sum-label">平均涨跌</div><div class="sum-val" style="color:${{avg>=0?'var(--up)':'var(--down)'}}">${{avg>=0?'+':''}}${{avg}}%</div></div>
    <div class="sum-box"><div class="sum-label">${{has_ff>0?'主力净流':'盘口差'}}</div><div class="sum-val" style="color:${{(has_ff>0?main:book)>=0?'var(--up)':'var(--down)'}}">${{fmtm(has_ff>0?main:book)}}</div></div>
    <div class="sum-box"><div class="sum-label">上涨家数</div><div class="sum-val">${{up}}/${{allStocks.length}}</div></div>
    <div class="sum-box"><div class="sum-label">5日主力净流</div><div class="sum-val" style="color:${{mf5d_all>=0?'var(--up)':'var(--down)'}}">${{fmtm(mf5d_all)}}</div></div>
    <div class="sum-box"><div class="sum-label">总成交额</div><div class="sum-val">${{fmtm(allStocks.reduce((a,b)=>a+b.amount,0))}}</div></div>`;
  let tabHtml='';
  for(const s of sectors){{
    const sAvg=s.stocks.length?(s.stocks.reduce((a,b)=>a+b.change_pct,0)/s.stocks.length).toFixed(2):0;
    const active=currentSector===s.name?'active':'';
    tabHtml+=`<div class="sub-tab ${{active}}" onclick="switchSector('${{s.name}}')">${{s.name}}<span class="tab-pct" style="color:${{sAvg>=0?'var(--up)':'var(--down)'}}">${{sAvg>=0?'+':''}}${{sAvg}}%</span></div>`;
  }}
  document.getElementById('subTabs').innerHTML=tabHtml;
  if(!currentSector&&sectors.length>0){{currentSector=sectors[0].name;renderPage2();return;}}
  const tabs=document.querySelectorAll('.sub-tab');
  tabs.forEach(t=>t.classList.toggle('active',t.textContent.includes(currentSector)));
  const stocks=SECTOR_DATA[currentSector]||[];
  stocks.sort((a,b)=>b.change_pct-a.change_pct);
  let tableHtml='<table class="stock-table"><thead><tr>';
  tableHtml+='<th class="rank">#</th><th>名称</th><th class="price">现价</th><th class="change">涨跌</th>';
  tableHtml+='<th class="amount">主力净流</th><th class="amount">5日主力净流</th><th class="amount">盘口差</th><th class="amount">成交额</th><th class="amount">振幅</th><th>操作</th></tr></thead><tbody>';
  for(let i=0;i<stocks.length;i++){{
    const s=stocks[i];
    const pctColor=s.change_pct>=0?'var(--up)':'var(--down)';
    const mainColor=(s.main_force||0)>=0?'var(--up)':'var(--down)';
    const bookColor=(s.book_diff||0)>=0?'var(--up)':'var(--down)';
    const isF=isFav(s.code);
    const amp=s.high&&s.low&&s.last_close?((s.high-s.low)/s.last_close*100).toFixed(2):'-';
    tableHtml+=`<tr onclick="openStock('${{s.code}}')">
      <td class="rank">${{i+1}}</td>
      <td><div class="name-cell"><span>${{s.name}}</span><span class="code-txt">${{s.code}}</span></div></td>
      <td class="price">${{s.price.toFixed(2)}}</td>
      <td class="change" style="color:${{pctColor}}">${{s.change_pct>=0?'+':''}}${{s.change_pct.toFixed(2)}}%</td>
      <td class="amount" style="color:${{mainColor}}">${{s.has_fund_flow?fmtm(s.main_force):'-'}}</td>
      <td class="amount" style="color:${{(s.mf_5d||0)>=0?'var(--up)':'var(--down)'}}">${{s.mf_5d!==undefined?fmtm(s.mf_5d):'-'}}</td>
      <td class="amount" style="color:${{bookColor}}">${{fmtm(s.book_diff||0)}}</td>
      <td class="amount">${{fmtm(s.amount)}}</td>
      <td class="amount">${{amp}}%</td>
      <td class="action-btns" onclick="event.stopPropagation()">
        <button class="btn-sm btn-fav" onclick="toggleFav('${{s.code}}');this.textContent=isFav('${{s.code}}')?'★':'☆';event.stopPropagation()">${{isF?'★':'☆'}}</button>
        <button class="btn-sm btn-detail" onclick="openStock('${{s.code}}');event.stopPropagation()">详情</button>
      </td>
    </tr>`;
  }}
  tableHtml+='</tbody></table>';
  document.getElementById('stockTableWrap').innerHTML=tableHtml;
}}

function switchSector(name){{currentSector=name;renderPage2();}}

function openStock(code){{
  const s=RAW_DATA[code];if(!s)return;
  currentStock=s;
  document.getElementById('modalTitle').innerHTML=`<span>${{s.name}}</span><span style="color:var(--muted);font-size:14px;margin-left:8px">${{s.code}}</span><span style="color:${{s.change_pct>=0?'var(--up)':'var(--down)'}};margin-left:12px;font-size:16px">${{s.change_pct>=0?'+':''}}${{s.change_pct.toFixed(2)}}%</span>`;
  const amp=s.high&&s.low&&s.last_close?((s.high-s.low)/s.last_close*100).toFixed(2):'-';
  let infoHtml='';
  infoHtml+=`<div class="info-item"><div class="info-label">现价</div><div class="info-val">${{s.price.toFixed(2)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">涨跌</div><div class="info-val" style="color:${{s.change_pct>=0?'var(--up)':'var(--down)'}}">${{s.change_pct>=0?'+':''}}${{s.change_pct.toFixed(2)}}%</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">开盘</div><div class="info-val">${{s.open.toFixed(2)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">最高</div><div class="info-val">${{s.high.toFixed(2)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">最低</div><div class="info-val">${{s.low.toFixed(2)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">昨收</div><div class="info-val">${{s.last_close.toFixed(2)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">成交量</div><div class="info-val">${{fmtm(s.volume)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">成交额</div><div class="info-val">${{fmtm(s.amount)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">盘口差</div><div class="info-val" style="color:${{(s.book_diff||0)>=0?'var(--up)':'var(--down)'}}">${{fmtm(s.book_diff||0)}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">主力净流</div><div class="info-val" style="color:${{(s.main_force||0)>=0?'var(--up)':'var(--down)'}}">${{s.has_fund_flow?fmtm(s.main_force):'-'}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">超大单</div><div class="info-val" style="color:${{(s.super||0)>=0?'var(--up)':'var(--down)'}}">${{s.has_fund_flow?fmtm(s.super):'-'}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">大单</div><div class="info-val" style="color:${{(s.large||0)>=0?'var(--up)':'var(--down)'}}">${{s.has_fund_flow?fmtm(s.large):'-'}}</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">振幅</div><div class="info-val">${{amp}}%</div></div>`;
  infoHtml+=`<div class="info-item"><div class="info-label">所属</div><div class="info-val" style="font-size:11px">${{s.sector}}</div></div>`;
  document.getElementById('infoGrid').innerHTML=infoHtml;

  const bids=s.bids||{{}};const asks=s.asks||{{}};
  const maxVol=Math.max(...[1,2,3,4,5].map(j=>Math.max(bids[`bid_vol${{j}}`]||0,asks[`ask_vol${{j}}`]||0)))||1;
  let bookHtml='<div class="book-col book-buy"><h4 style="color:var(--up)">买盘</h4>';
  for(let j=1;j<=5;j++){{
    const p=bids[`bid${{j}}`]||0;const v=bids[`bid_vol${{j}}`]||0;const pct=(v/maxVol*100).toFixed(1);
    bookHtml+=`<div class="book-row"><span class="book-price">${{p.toFixed(2)}}</span><span class="book-vol">${{v}}手</span></div><div class="book-bar" style="width:${{pct}}%"></div>`;
  }}
  bookHtml+='</div>';
  bookHtml+='<div class="book-col book-sell"><h4 style="color:var(--down)">卖盘</h4>';
  for(let j=1;j<=5;j++){{
    const p=asks[`ask${{j}}`]||0;const v=asks[`ask_vol${{j}}`]||0;const pct=(v/maxVol*100).toFixed(1);
    bookHtml+=`<div class="book-row"><span class="book-price">${{p.toFixed(2)}}</span><span class="book-vol">${{v}}手</span></div><div class="book-bar" style="width:${{pct}}%"></div>`;
  }}
  bookHtml+='</div>';
  document.getElementById('bookGrid').innerHTML=bookHtml;
  document.getElementById('bookDiffVal').textContent=fmtm(s.book_diff||0);
  document.getElementById('bookDiffVal').style.color=(s.book_diff||0)>=0?'var(--up)':'var(--down)';

  drawKline(s);
  document.querySelectorAll('.kline-tab').forEach(t=>{{
    t.onclick=()=>{{
      document.querySelectorAll('.kline-tab').forEach(x=>x.classList.remove('active'));
      t.classList.add('active');
      const tab=t.dataset.tab;
      document.getElementById('tabContentBook').style.display=tab==='book'?'block':'none';
      document.getElementById('tabContentKline').style.display=tab==='kline'?'block':'none';
    }};
  }});
  document.getElementById('overlay').classList.add('active');
}}

function closeModal(e){{if(!e||e.target.id==='overlay'){{document.getElementById('overlay').classList.remove('active');}}}}

function drawKline(s){{
  const canvas=document.getElementById('klineCanvas');
  const ctx=canvas.getContext('2d');
  const w=canvas.width,h=canvas.height;
  ctx.clearRect(0,0,w,h);
  const prices=[s.open,s.high,s.low,s.last_close,s.price];
  const min=Math.min(...prices.filter(p=>p>0))*0.995;
  const max=Math.max(...prices)*1.005;
  const range=max-min||1;
  function y(p){{return h-20-((p-min)/range)*(h-40);}}
  ctx.strokeStyle='rgba(255,255,255,0.05)';ctx.lineWidth=1;
  for(let i=0;i<=4;i++){{
    const py=10+i*(h-20)/4;
    ctx.beginPath();ctx.moveTo(0,py);ctx.lineTo(w,py);ctx.stroke();
  }}
  ctx.fillStyle='#6b7280';ctx.font='10px sans-serif';ctx.textAlign='left';
  ctx.fillText(max.toFixed(2),4,14);ctx.fillText(min.toFixed(2),4,h-4);ctx.textAlign='center';
  const labels=['开','高','低','收','现'];const vals=[s.open,s.high,s.low,s.last_close,s.price];
  const barW=(w-60)/5;const startX=30;
  for(let i=0;i<5;i++){{
    const v=vals[i];if(!v)continue;
    const isUp=v>=s.last_close;const color=isUp?'#ef4444':'#22c55e';
    const x=startX+i*barW+barW/2;const yPos=y(v);const yBase=y(s.last_close);
    ctx.fillStyle=color;const barH=Math.abs(yPos-yBase)||2;const top=Math.min(yPos,yBase);
    ctx.fillRect(x-12,top,24,barH);
    ctx.fillStyle='#9ca3af';ctx.font='11px sans-serif';ctx.fillText(labels[i],x,h-2);
    ctx.fillStyle=color;ctx.font='10px sans-serif';ctx.fillText(v.toFixed(2),x,top-4);
  }}
  ctx.strokeStyle='rgba(245,158,11,0.5)';ctx.setLineDash([4,4]);
  ctx.beginPath();ctx.moveTo(0,y(s.last_close));ctx.lineTo(w,y(s.last_close));ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#f59e0b';ctx.font='10px sans-serif';ctx.textAlign='right';
  ctx.fillText('昨收 '+s.last_close.toFixed(2),w-4,y(s.last_close)-4);
}}

function fmtm(v){{
  v=Number(v);if(isNaN(v))return'-';
  if(Math.abs(v)>=1e8)return(v/1e8).toFixed(1)+'亿';
  if(Math.abs(v)>=1e4)return(v/1e4).toFixed(1)+'万';
  return v.toFixed(0);
}}

async function fetchData(){{
  try{{
    const resp=await fetch('data/dashboard_v5.json?t='+Date.now());
    if(!resp.ok)return;
    const newData=await resp.json();
    document.getElementById('refreshStatus').textContent='已更新 '+new Date().toLocaleTimeString();
  }}catch(e){{
    document.getElementById('refreshStatus').textContent='刷新失败';
  }}
}}

function startRefresh(){{if(refreshTimer)clearInterval(refreshTimer);refreshTimer=setInterval(fetchData,60000);}}

document.addEventListener('DOMContentLoaded',()=>{{
  renderFavBar();
  startRefresh();
  document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeModal();}});
}});
"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔥 板块龙头股监控看板 V5</title>
<style>{css}</style>
</head>
<body>
{body}
<script>{js}</script>
</body>
</html>"""

    return html


if __name__ == "__main__":
    build()
