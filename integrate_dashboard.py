#!/usr/bin/env python3
"""
integrate_dashboard.py - 将板块龙头股看板V5整合进现有index.html
"""

import re
from pathlib import Path

REPO = Path("/root/.openclaw/workspace/stock-review")
INDEX = REPO / "index.html"
DASHBOARD_CSS = """
/* ========== 板块龙头股看板集成样式 ========== */
:root {
  --dash-bg: #0a0e17;
  --dash-card: #111827;
  --dash-elevated: #1f2937;
  --dash-border: #374151;
  --dash-text: #f3f4f6;
  --dash-muted: #9ca3af;
  --dash-up: #ef4444;
  --dash-up-bg: rgba(239,68,68,0.1);
  --dash-down: #22c55e;
  --dash-down-bg: rgba(34,197,94,0.1);
  --dash-accent: #3b82f6;
  --dash-gold: #f59e0b;
}

.dash-fav-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--dash-card);
  border: 1px solid var(--dash-border);
  border-radius: 8px;
  margin-bottom: 16px;
  overflow-x: auto;
  scrollbar-width: thin;
}
.dash-fav-bar::-webkit-scrollbar { height: 3px; }
.dash-fav-bar::-webkit-scrollbar-thumb { background: var(--dash-border); border-radius: 3px; }
.dash-fav-label { font-size: 16px; font-weight: 700; white-space: nowrap; color: var(--dash-gold); }
.dash-fav-tag {
  display: flex; align-items: center; gap: 6px; padding: 4px 12px;
  background: var(--dash-elevated); border-radius: 20px; cursor: pointer;
  border: 1px solid var(--dash-border); white-space: nowrap; font-size: 13px;
  transition: all .15s; color: var(--dash-text);
}
.dash-fav-tag:hover { border-color: var(--dash-accent); }
.dash-fav-tag .fav-name { font-weight: 500; }
.dash-fav-tag .fav-pct { font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.dash-fav-tag .fav-del { opacity: 0; transition: opacity .15s; font-size: 12px; color: var(--dash-muted); }
.dash-fav-tag:hover .fav-del { opacity: 1; }
.dash-fav-add {
  padding: 4px 12px; border: 1px dashed var(--dash-border); border-radius: 20px;
  color: var(--dash-muted); cursor: pointer; white-space: nowrap; font-size: 13px;
}
.dash-fav-add:hover { border-color: var(--dash-accent); color: var(--dash-accent); }

.dash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
@media (min-width: 1400px) { .dash-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 1024px) { .dash-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px) { .dash-grid { grid-template-columns: repeat(2, 1fr); } }

.dash-card {
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 12px;
  padding: 16px; cursor: pointer; transition: all .2s; position: relative; overflow: hidden;
}
.dash-card:hover { border-color: var(--dash-accent); transform: translateY(-2px); }
.dash-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.dash-card-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; color: var(--dash-text); }
.dash-card-emoji { font-size: 18px; }
.dash-card-meta { display: flex; gap: 10px; align-items: center; }
.dash-card-tag { font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 500; }
.dash-tag-bull { background: var(--dash-up-bg); color: var(--dash-up); }
.dash-tag-sideways { background: rgba(245,158,11,0.15); color: #f59e0b; }
.dash-tag-bear { background: var(--dash-down-bg); color: var(--dash-down); }
.dash-tag-accum { background: rgba(59,130,246,0.15); color: var(--dash-accent); }
.dash-card-count { font-size: 11px; color: var(--dash-muted); background: var(--dash-elevated); padding: 2px 8px; border-radius: 10px; }
.dash-card-stats { display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px; }
.dash-stat-item { display: flex; flex-direction: column; }
.dash-stat-label { font-size: 11px; color: var(--dash-muted); margin-bottom: 2px; }
.dash-stat-val { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 14px; }
.dash-card-sub-leader {
  font-size: 12px; color: var(--dash-accent); margin-bottom: 10px;
  padding: 4px 8px; background: rgba(59,130,246,0.1); border-radius: 6px; display: inline-block;
}
.dash-card-top3 { display: flex; flex-direction: column; gap: 6px; }
.dash-top3-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 8px; background: var(--dash-elevated); border-radius: 6px; font-size: 12px;
}
.dash-top3-name { font-weight: 500; color: var(--dash-text); }
.dash-top3-code { color: var(--dash-muted); font-size: 10px; margin-left: 4px; }
.dash-top3-pct { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 13px; }
.dash-card-footer {
  display: flex; justify-content: space-between; margin-top: 12px; font-size: 11px; color: var(--dash-muted);
}

.dash-page2 { display: none; }
.dash-page2.active { display: block; }
.dash-breadcrumb { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; font-size: 14px; color: var(--dash-text); }
.dash-breadcrumb a { color: var(--dash-accent); cursor: pointer; }
.dash-breadcrumb a:hover { text-decoration: underline; }
.dash-breadcrumb span { color: var(--dash-muted); }

.dash-sub-tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.dash-sub-tab {
  padding: 6px 14px; border-radius: 8px; font-size: 13px; cursor: pointer;
  border: 1px solid var(--dash-border); background: var(--dash-card); color: var(--dash-text);
  transition: all .15s;
}
.dash-sub-tab:hover { border-color: var(--dash-accent); }
.dash-sub-tab.active { background: var(--dash-accent); color: #fff; border-color: var(--dash-accent); }
.dash-sub-tab .tab-pct { font-family: 'JetBrains Mono', monospace; font-weight: 700; margin-left: 6px; }

.dash-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.dash-table thead th {
  text-align: left; padding: 10px 12px; color: var(--dash-muted); font-weight: 500;
  border-bottom: 1px solid var(--dash-border); position: sticky; top: 0; background: var(--dash-card);
  white-space: nowrap; cursor: pointer;
}
.dash-table td { padding: 10px 12px; border-bottom: 1px solid var(--dash-border); vertical-align: middle; color: var(--dash-text); }
.dash-table tbody tr { cursor: pointer; transition: background .1s; }
.dash-table tbody tr:hover td { background: var(--dash-elevated); }
.dash-table .rank { text-align: center; color: var(--dash-muted); font-weight: 600; width: 40px; }
.dash-table .name-cell { display: flex; flex-direction: column; }
.dash-table .code-txt { font-size: 11px; color: var(--dash-muted); }
.dash-table .price, .dash-table .change, .dash-table .amount { font-family: 'JetBrains Mono', monospace; }
.dash-table .change { font-weight: 700; text-align: right; }
.dash-table .price { text-align: right; }
.dash-table .amount { text-align: right; color: var(--dash-muted); font-size: 12px; }
.dash-table .action-btns { display: flex; gap: 8px; }
.dash-btn-sm { padding: 3px 8px; border-radius: 4px; font-size: 11px; border: none; cursor: pointer; }
.dash-btn-fav { background: rgba(245,158,11,0.2); color: var(--dash-gold); }
.dash-btn-detail { background: var(--dash-accent); color: #fff; }

.dash-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 200;
  display: none; align-items: center; justify-content: center; padding: 20px;
}
.dash-overlay.active { display: flex; }
.dash-modal {
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 16px;
  width: 100%; max-width: 720px; max-height: 90vh; overflow-y: auto;
}
.dash-modal-header {
  padding: 18px 24px; border-bottom: 1px solid var(--dash-border);
  display: flex; justify-content: space-between; align-items: center;
}
.dash-modal-title { font-size: 18px; font-weight: 600; color: var(--dash-text); }
.dash-modal-close { background: none; border: none; color: var(--dash-muted); font-size: 24px; cursor: pointer; line-height: 1; }
.dash-modal-close:hover { color: var(--dash-text); }
.dash-modal-body { padding: 20px 24px; }

.dash-kline-tabs { display: flex; gap: 8px; margin-bottom: 16px; }
.dash-kline-tab { padding: 4px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; border: 1px solid var(--dash-border); background: var(--dash-elevated); color: var(--dash-text); }
.dash-kline-tab.active { background: var(--dash-accent); color: #fff; border-color: var(--dash-accent); }
.dash-kline-canvas { width: 100%; height: 200px; background: var(--dash-elevated); border-radius: 8px; margin-bottom: 16px; }

.dash-book-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.dash-book-col h4 { font-size: 13px; margin-bottom: 10px; color: var(--dash-muted); }
.dash-book-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--dash-border); font-size: 12px; color: var(--dash-text); }
.dash-book-row:last-child { border-bottom: none; }
.dash-book-price { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
.dash-book-vol { color: var(--dash-muted); font-size: 11px; }
.dash-book-buy .dash-book-price { color: var(--dash-up); }
.dash-book-sell .dash-book-price { color: var(--dash-down); }
.dash-book-bar { height: 3px; border-radius: 2px; margin-top: 2px; }
.dash-book-buy .dash-book-bar { background: var(--dash-up); }
.dash-book-sell .dash-book-bar { background: var(--dash-down); }
.dash-book-diff-box { background: var(--dash-elevated); border-radius: 8px; padding: 12px 16px; margin-top: 16px; }
.dash-book-diff-label { font-size: 12px; color: var(--dash-muted); margin-bottom: 4px; }
.dash-book-diff-val { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

.dash-info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.dash-info-item { background: var(--dash-elevated); border-radius: 8px; padding: 10px 12px; text-align: center; }
.dash-info-label { font-size: 11px; color: var(--dash-muted); margin-bottom: 2px; }
.dash-info-val { font-size: 14px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

.dash-sector-summary { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.dash-sum-box {
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 10px;
  padding: 14px 18px; min-width: 140px;
}
.dash-sum-label { font-size: 11px; color: var(--dash-muted); margin-bottom: 4px; }
.dash-sum-val { font-size: 20px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

.dash-quick-movers { margin-bottom: 20px; }
.dash-qm-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; color: var(--dash-gold); }
.dash-qm-row { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.dash-qm-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 14px;
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 10px;
  font-size: 13px; white-space: nowrap; cursor: pointer; transition: all .15s; color: var(--dash-text);
}
.dash-qm-item:hover { border-color: var(--dash-accent); }
.dash-qm-code { color: var(--dash-muted); font-size: 11px; }
.dash-qm-pct { font-family: 'JetBrains Mono', monospace; font-weight: 700; }

@media (max-width: 600px) {
  .dash-info-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-book-grid { grid-template-columns: 1fr; }
  .dash-card-stats { flex-wrap: wrap; }
}
"""

def integrate():
    # Read existing index.html
    with open(INDEX, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add new tab button after the last tab
    tab_html = '''            <button onclick="switchTab('sector')" id="tab-sector" class="tab-btn pb-3 text-sm font-medium text-gray-400 border-b-2 border-transparent hover:text-gray-200 whitespace-nowrap">
                <i class="fas fa-fire mr-1.5"></i>板块龙头
            </button>'''

    # Find the last tab button and insert after it
    last_tab_pattern = r'(</button>\s*</div>\s*<!-- Tab 导航 -->)'
    match = re.search(r'<button onclick="switchTab\(\'history\'\).*?</button>', html, re.DOTALL)
    if match:
        insert_pos = match.end()
        html = html[:insert_pos] + '\n' + tab_html + html[insert_pos:]

    # 2. Add new content section before the closing </main>
    content_html = f'''
        <!-- 板块龙头股看板内容 -->
        <div id="content-sector" class="tab-content" style="display:none">
            <!-- 自选栏 -->
            <div class="dash-fav-bar" id="dashFavBar">
                <span class="dash-fav-label">⭐ 自选</span>
                <span class="dash-fav-add" onclick="dashAddFav()">+ 添加自选</span>
            </div>
            <!-- 第一层 -->
            <div id="dashPage1">
                <div class="dash-quick-movers">
                    <div class="dash-qm-title">📈 市场异动 TOP5</div>
                    <div class="dash-qm-row" id="dashQuickMovers"></div>
                </div>
                <div class="dash-grid" id="dashThemeGrid"></div>
            </div>
            <!-- 第二层 -->
            <div id="dashPage2" class="dash-page2">
                <div class="dash-breadcrumb">
                    <a onclick="dashGoToPage1()">📊 主题概览</a>
                    <span>/</span>
                    <span id="dashBreadcrumbTheme"></span>
                </div>
                <div class="dash-sector-summary" id="dashSectorSummary"></div>
                <div class="dash-sub-tabs" id="dashSubTabs"></div>
                <div id="dashStockTableWrap"></div>
            </div>
            <!-- 第三层弹窗 -->
            <div id="dashOverlay" class="dash-overlay" onclick="dashCloseModal(event)">
                <div class="dash-modal" onclick="event.stopPropagation()">
                    <div class="dash-modal-header">
                        <div class="dash-modal-title" id="dashModalTitle"></div>
                        <button class="dash-modal-close" onclick="dashCloseModal()">×</button>
                    </div>
                    <div class="dash-modal-body">
                        <div class="dash-info-grid" id="dashInfoGrid"></div>
                        <div class="dash-kline-tabs">
                            <div class="dash-kline-tab active" data-tab="book" onclick="dashSwitchTab(this)">📊 五档盘口</div>
                            <div class="dash-kline-tab" data-tab="kline" onclick="dashSwitchTab(this)">📈 走势</div>
                        </div>
                        <div id="dashTabContentBook">
                            <div class="dash-book-grid" id="dashBookGrid"></div>
                            <div class="dash-book-diff-box">
                                <div class="dash-book-diff-label">盘口差估算 (买盘力量 - 卖盘力量)</div>
                                <div class="dash-book-diff-val" id="dashBookDiffVal"></div>
                            </div>
                        </div>
                        <div id="dashTabContentKline" style="display:none">
                            <canvas class="dash-kline-canvas" id="dashKlineCanvas" width="672" height="200"></canvas>
                            <p style="text-align:center;color:var(--dash-muted);font-size:12px">基于开高低收数据的走势示意</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
'''

    # Insert before </main>
    main_close = '</main>'
    main_pos = html.find(main_close)
    if main_pos != -1:
        html = html[:main_pos] + content_html + html[main_pos:]

    # 3. Add CSS before </head>
    css_block = f'<style>\n{DASHBOARD_CSS}\n</style>'
    head_close = '</head>'
    head_pos = html.find(head_close)
    if head_pos != -1:
        html = html[:head_pos] + css_block + '\n' + html[head_pos:]

    # 4. Add JavaScript before </body>
    js_block = '''
<script>
// ===== 板块龙头股看板数据 =====
let dashData = {};
let dashCurrentTheme = null;
let dashCurrentSector = null;
let dashCurrentStock = null;
let dashRefreshTimer = null;

// 主题映射
const SECTOR_MAP = {
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
};

function dashGetFavs() { try { return JSON.parse(localStorage.getItem('fav_stocks') || '[]'); } catch(e) { return []; } }
function dashSetFavs(favs) { localStorage.setItem('fav_stocks', JSON.stringify(favs)); dashRenderFavBar(); }
function dashIsFav(code) { return dashGetFavs().includes(code); }
function dashToggleFav(code) { let favs = dashGetFavs(); if (favs.includes(code)) favs = favs.filter(c => c !== code); else favs.push(code); dashSetFavs(favs); }
function dashAddFav() { const code = prompt('输入股票代码(6位数字):'); if (code && /^\\d{6}$/.test(code)) { let favs = dashGetFavs(); if (!favs.includes(code)) { favs.push(code); dashSetFavs(favs); } } }

function dashRenderFavBar() {
    const bar = document.getElementById('dashFavBar');
    const favs = dashGetFavs();
    let html = '<span class="dash-fav-label">⭐ 自选</span>';
    for (const code of favs) {
        const s = dashData.raw_data && dashData.raw_data[code];
        if (!s) continue;
        const color = s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        html += `<div class="dash-fav-tag" onclick="dashOpenStock('${code}')">
            <span class="fav-name">${s.name}</span>
            <span class="fav-pct" style="color:${color}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span>
            <span class="fav-del" onclick="event.stopPropagation();dashToggleFav('${code}')">✕</span>
        </div>`;
    }
    html += '<span class="dash-fav-add" onclick="dashAddFav()">+ 添加自选</span>';
    bar.innerHTML = html;
}

function dashGoToPage1() {
    document.getElementById('dashPage1').style.display = 'block';
    document.getElementById('dashPage2').classList.remove('active');
    dashCurrentTheme = null;
    dashCurrentSector = null;
}

function dashGoToTheme(themeName) {
    dashCurrentTheme = themeName;
    document.getElementById('dashPage1').style.display = 'none';
    document.getElementById('dashPage2').classList.add('active');
    document.getElementById('dashBreadcrumbTheme').textContent = themeName;
    dashRenderPage2();
}

function dashFmtm(v) {
    v = Number(v); if (isNaN(v)) return '-';
    if (Math.abs(v) >= 1e8) return (v/1e8).toFixed(1) + '亿';
    if (Math.abs(v) >= 1e4) return (v/1e4).toFixed(1) + '万';
    return v.toFixed(0);
}

function dashStatusTag(avg) {
    if (avg >= 2.0) return ['主升🔴', 'dash-tag-bull'];
    if (avg >= 0.5) return ['震荡🟡', 'dash-tag-sideways'];
    if (avg >= -1.0) return ['蓄势⚪', 'dash-tag-accum'];
    return ['退潮🟢', 'dash-tag-bear'];
}

function dashRenderPage2() {
    if (!dashCurrentTheme) return;
    const sectors = [];
    for (const [name, stocks] of Object.entries(dashData.sector_data || {})) {
        const mapped = SECTOR_MAP[name] || '';
        if (mapped.includes(dashCurrentTheme)) sectors.push({name, stocks});
    }
    if (sectors.length === 0) return;
    const allStocks = [];
    for (const s of sectors) allStocks.push(...s.stocks);
    const avg = allStocks.length ? (allStocks.reduce((a,b) => a + b.change_pct, 0) / allStocks.length).toFixed(2) : 0;
    const book = allStocks.reduce((a,b) => a + (b.book_diff || 0), 0);
    const main = allStocks.reduce((a,b) => a + (b.main_force || 0), 0);
    const has_ff = allStocks.filter(s => s.has_fund_flow).length;
    const up = allStocks.filter(s => s.change_pct > 0).length;
    document.getElementById('dashSectorSummary').innerHTML = `
        <div class="dash-sum-box"><div class="dash-sum-label">平均涨跌</div><div class="dash-sum-val" style="color:${avg >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${avg >= 0 ? '+' : ''}${avg}%</div></div>
        <div class="dash-sum-box"><div class="dash-sum-label">${has_ff > 0 ? '主力净流' : '盘口差'}</div><div class="dash-sum-val" style="color:${(has_ff > 0 ? main : book) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${dashFmtm(has_ff > 0 ? main : book)}</div></div>
        <div class="dash-sum-box"><div class="dash-sum-label">上涨家数</div><div class="dash-sum-val">${up}/${allStocks.length}</div></div>
        <div class="dash-sum-box"><div class="dash-sum-label">总成交额</div><div class="dash-sum-val">${dashFmtm(allStocks.reduce((a,b) => a + b.amount, 0))}</div></div>
    `;
    let tabHtml = '';
    for (const s of sectors) {
        const sAvg = s.stocks.length ? (s.stocks.reduce((a,b) => a + b.change_pct, 0) / s.stocks.length).toFixed(2) : 0;
        const active = dashCurrentSector === s.name ? 'active' : '';
        tabHtml += `<div class="dash-sub-tab ${active}" onclick="dashSwitchSector('${s.name}')">${s.name}<span class="tab-pct" style="color:${sAvg >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${sAvg >= 0 ? '+' : ''}${sAvg}%</span></div>`;
    }
    document.getElementById('dashSubTabs').innerHTML = tabHtml;
    if (!dashCurrentSector && sectors.length > 0) { dashCurrentSector = sectors[0].name; dashRenderPage2(); return; }
    const stocks = dashData.sector_data && dashData.sector_data[dashCurrentSector] || [];
    stocks.sort((a,b) => b.change_pct - a.change_pct);
    let tableHtml = '<table class="dash-table"><thead><tr>';
    tableHtml += '<th class="rank">#</th><th>名称</th><th class="price">现价</th><th class="change">涨跌</th>';
    tableHtml += '<th class="amount">主力净流</th><th class="amount">盘口差</th><th class="amount">成交额</th><th class="amount">振幅</th><th>操作</th></tr></thead><tbody>';
    for (let i = 0; i < stocks.length; i++) {
        const s = stocks[i];
        const pctColor = s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const mainColor = (s.main_force || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const bookColor = (s.book_diff || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const isF = dashIsFav(s.code);
        const amp = s.high && s.low && s.last_close ? ((s.high - s.low) / s.last_close * 100).toFixed(2) : '-';
        tableHtml += `<tr onclick="dashOpenStock('${s.code}')">
            <td class="rank">${i+1}</td>
            <td><div class="name-cell"><span>${s.name}</span><span class="code-txt">${s.code}</span></div></td>
            <td class="price">${s.price.toFixed(2)}</td>
            <td class="change" style="color:${pctColor}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</td>
            <td class="amount" style="color:${mainColor}">${s.has_fund_flow ? dashFmtm(s.main_force) : '-'}</td>
            <td class="amount" style="color:${bookColor}">${dashFmtm(s.book_diff || 0)}</td>
            <td class="amount">${dashFmtm(s.amount)}</td>
            <td class="amount">${amp}%</td>
            <td class="action-btns" onclick="event.stopPropagation()">
                <button class="dash-btn-sm dash-btn-fav" onclick="dashToggleFav('${s.code}');this.textContent=dashIsFav('${s.code}')?'★':'☆';event.stopPropagation()">${isF ? '★' : '☆'}</button>
                <button class="dash-btn-sm dash-btn-detail" onclick="dashOpenStock('${s.code}');event.stopPropagation()">详情</button>
            </td>
        </tr>`;
    }
    tableHtml += '</tbody></table>';
    document.getElementById('dashStockTableWrap').innerHTML = tableHtml;
}

function dashSwitchSector(name) { dashCurrentSector = name; dashRenderPage2(); }

function dashOpenStock(code) {
    const s = dashData.raw_data && dashData.raw_data[code];
    if (!s) return;
    dashCurrentStock = s;
    document.getElementById('dashModalTitle').innerHTML = `<span>${s.name}</span><span style="color:var(--dash-muted);font-size:14px;margin-left:8px">${s.code}</span><span style="color:${s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'};margin-left:12px;font-size:16px">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span>`;
    const amp = s.high && s.low && s.last_close ? ((s.high - s.low) / s.last_close * 100).toFixed(2) : '-';
    let infoHtml = '';
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">现价</div><div class="dash-info-val">${s.price.toFixed(2)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">涨跌</div><div class="dash-info-val" style="color:${s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">开盘</div><div class="dash-info-val">${s.open.toFixed(2)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">最高</div><div class="dash-info-val">${s.high.toFixed(2)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">最低</div><div class="dash-info-val">${s.low.toFixed(2)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">昨收</div><div class="dash-info-val">${s.last_close.toFixed(2)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">成交量</div><div class="dash-info-val">${dashFmtm(s.volume)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">成交额</div><div class="dash-info-val">${dashFmtm(s.amount)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">盘口差</div><div class="dash-info-val" style="color:${(s.book_diff || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${dashFmtm(s.book_diff || 0)}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">主力净流</div><div class="dash-info-val" style="color:${(s.main_force || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${s.has_fund_flow ? dashFmtm(s.main_force) : '-'}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">超大单</div><div class="dash-info-val" style="color:${(s.super || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${s.has_fund_flow ? dashFmtm(s.super) : '-'}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">大单</div><div class="dash-info-val" style="color:${(s.large || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'}">${s.has_fund_flow ? dashFmtm(s.large) : '-'}</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">振幅</div><div class="dash-info-val">${amp}%</div></div>`;
    infoHtml += `<div class="dash-info-item"><div class="dash-info-label">所属</div><div class="dash-info-val" style="font-size:11px">${s.sector}</div></div>`;
    document.getElementById('dashInfoGrid').innerHTML = infoHtml;
    const bids = s.bids || {}; const asks = s.asks || {};
    const maxVol = Math.max(...[1,2,3,4,5].map(j => Math.max(bids[`bid_vol${j}`] || 0, asks[`ask_vol${j}`] || 0))) || 1;
    let bookHtml = '<div class="dash-book-col dash-book-buy"><h4 style="color:var(--dash-up)">买盘</h4>';
    for (let j = 1; j <= 5; j++) {
        const p = bids[`bid${j}`] || 0; const v = bids[`bid_vol${j}`] || 0; const pct = (v / maxVol * 100).toFixed(1);
        bookHtml += `<div class="dash-book-row"><span class="dash-book-price">${p.toFixed(2)}</span><span class="dash-book-vol">${v}手</span></div><div class="dash-book-bar" style="width:${pct}%"></div>`;
    }
    bookHtml += '</div>';
    bookHtml += '<div class="dash-book-col dash-book-sell"><h4 style="color:var(--dash-down)">卖盘</h4>';
    for (let j = 1; j <= 5; j++) {
        const p = asks[`ask${j}`] || 0; const v = asks[`ask_vol${j}`] || 0; const pct = (v / maxVol * 100).toFixed(1);
        bookHtml += `<div class="dash-book-row"><span class="dash-book-price">${p.toFixed(2)}</span><span class="dash-book-vol">${v}手</span></div><div class="dash-book-bar" style="width:${pct}%"></div>`;
    }
    bookHtml += '</div>';
    document.getElementById('dashBookGrid').innerHTML = bookHtml;
    document.getElementById('dashBookDiffVal').textContent = dashFmtm(s.book_diff || 0);
    document.getElementById('dashBookDiffVal').style.color = (s.book_diff || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
    dashDrawKline(s);
    document.getElementById('dashOverlay').classList.add('active');
}

function dashCloseModal(e) { if (!e || e.target.id === 'dashOverlay') { document.getElementById('dashOverlay').classList.remove('active'); } }

function dashDrawKline(s) {
    const canvas = document.getElementById('dashKlineCanvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const prices = [s.open, s.high, s.low, s.last_close, s.price];
    const min = Math.min(...prices.filter(p => p > 0)) * 0.995;
    const max = Math.max(...prices) * 1.005;
    const range = max - min || 1;
    function y(p) { return h - 20 - ((p - min) / range) * (h - 40); }
    ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const py = 10 + i * (h - 20) / 4;
        ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(w, py); ctx.stroke();
    }
    ctx.fillStyle = '#6b7280'; ctx.font = '10px sans-serif'; ctx.textAlign = 'left';
    ctx.fillText(max.toFixed(2), 4, 14); ctx.fillText(min.toFixed(2), 4, h - 4); ctx.textAlign = 'center';
    const labels = ['开', '高', '低', '收', '现']; const vals = [s.open, s.high, s.low, s.last_close, s.price];
    const barW = (w - 60) / 5; const startX = 30;
    for (let i = 0; i < 5; i++) {
        const v = vals[i]; if (!v) continue;
        const isUp = v >= s.last_close; const color = isUp ? '#ef4444' : '#22c55e';
        const x = startX + i * barW + barW / 2; const yPos = y(v); const yBase = y(s.last_close);
        ctx.fillStyle = color; const barH = Math.abs(yPos - yBase) || 2; const top = Math.min(yPos, yBase);
        ctx.fillRect(x - 12, top, 24, barH);
        ctx.fillStyle = '#9ca3af'; ctx.font = '11px sans-serif'; ctx.fillText(labels[i], x, h - 2);
        ctx.fillStyle = color; ctx.font = '10px sans-serif'; ctx.fillText(v.toFixed(2), x, top - 4);
    }
    ctx.strokeStyle = 'rgba(245,158,11,0.5)'; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(0, y(s.last_close)); ctx.lineTo(w, y(s.last_close)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = '#f59e0b'; ctx.font = '10px sans-serif'; ctx.textAlign = 'right';
    ctx.fillText('昨收 ' + s.last_close.toFixed(2), w - 4, y(s.last_close) - 4);
}

function dashSwitchTab(el) {
    document.querySelectorAll('.dash-kline-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    const tab = el.dataset.tab;
    document.getElementById('dashTabContentBook').style.display = tab === 'book' ? 'block' : 'none';
    document.getElementById('dashTabContentKline').style.display = tab === 'kline' ? 'block' : 'none';
}

async function dashLoadData() {
    try {
        const resp = await fetch('data/dashboard_v5.json?t=' + Date.now());
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        dashData = await resp.json();
        dashRenderDashboard();
    } catch (e) {
        console.error('[Dashboard] Load failed:', e);
        document.getElementById('dashThemeGrid').innerHTML = '<div style="text-align:center;color:var(--dash-muted);padding:40px">数据加载失败，请稍后刷新</div>';
    }
}

function dashRenderDashboard() {
    if (!dashData.raw_data) return;
    dashRenderFavBar();
    // 按主题聚合
    const byTheme = {};
    for (const [sectorName, stocks] of Object.entries(dashData.sector_data || {})) {
        const mapped = SECTOR_MAP[sectorName] || '';
        const parts = mapped.split(' ');
        const emoji = parts[0] || '💎'; const themeName = parts[1] || sectorName;
        if (!byTheme[themeName]) byTheme[themeName] = { sectors: [], emoji };
        byTheme[themeName].sectors.push({ name: sectorName, stocks });
    }
    for (const theme in byTheme) {
        const info = byTheme[theme];
        const allS = []; for (const s of info.sectors) allS.push(...s.stocks);
        info.avg = allS.length ? (allS.reduce((a,b) => a + b.change_pct, 0) / allS.length).toFixed(2) : 0;
        info.book = allS.reduce((a,b) => a + (b.book_diff || 0), 0);
        info.main = allS.reduce((a,b) => a + (b.main_force || 0), 0);
        info.has_ff = allS.filter(s => s.has_fund_flow).length;
        info.up = allS.filter(s => s.change_pct > 0).length;
        info.total = allS.length;
        info.all = allS.sort((a,b) => b.change_pct - a.change_pct);
        info.top = info.all[0];
        const sectorAvgs = [];
        for (const s of info.sectors) { if (s.stocks.length) sectorAvgs.push([s.name, s.stocks.reduce((a,b) => a + b.change_pct, 0) / s.stocks.length]); }
        sectorAvgs.sort((a,b) => b[1] - a[1]);
        info.top_sector = sectorAvgs[0] ? sectorAvgs[0][0] : '';
    }
    const sortedThemes = Object.entries(byTheme).sort((a,b) => b[1].avg - a[1].avg);
    // TOP5
    const allStocks = [];
    for (const s of Object.values(dashData.sector_data || {})) allStocks.push(...s);
    allStocks.sort((a,b) => b.change_pct - a.change_pct);
    const top5 = allStocks.slice(0, 5);
    // Render quick movers
    let qmHtml = '';
    for (const s of top5) {
        const color = s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        qmHtml += `<div class="dash-qm-item" onclick="dashOpenStock('${s.code}')"><span class="dash-qm-code">${s.code}</span><span>${s.name}</span><span class="dash-qm-pct" style="color:${color}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span></div>`;
    }
    document.getElementById('dashQuickMovers').innerHTML = qmHtml;
    // Render cards
    let gridHtml = '';
    for (const [themeName, info] of sortedThemes) {
        const [tagText, tagClass] = dashStatusTag(parseFloat(info.avg));
        const avgColor = info.avg >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const mainColor = info.main >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        gridHtml += `<div class="dash-card" onclick="dashGoToTheme('${themeName}')">
            <div class="dash-card-header">
                <div class="dash-card-title"><span class="dash-card-emoji">${info.emoji}</span>${themeName}</div>
                <div class="dash-card-meta"><span class="dash-card-tag ${tagClass}">${tagText}</span><span class="dash-card-count">${info.up}/${info.total}涨</span></div>
            </div>
            <div class="dash-card-stats">
                <div class="dash-stat-item"><span class="dash-stat-label">平均涨跌</span><span class="dash-stat-val" style="color:${avgColor}">${info.avg >= 0 ? '+' : ''}${info.avg}%</span></div>
                <div class="dash-stat-item"><span class="dash-stat-label">${info.has_ff > 0 ? '主力净流' : '盘口差'}</span><span class="dash-stat-val" style="color:${info.has_ff > 0 ? mainColor : (info.book >= 0 ? 'var(--dash-up)' : 'var(--dash-down)')}">${dashFmtm(info.has_ff > 0 ? info.main : info.book)}</span></div>
                <div class="dash-stat-item"><span class="dash-stat-label">上涨率</span><span class="dash-stat-val">${info.up}/${info.total}</span></div>
            </div>`;
        if (info.top_sector) gridHtml += `<div class="dash-card-sub-leader">🏆 领涨细分: ${info.top_sector}</div>`;
        gridHtml += `<div class="dash-card-top3">`;
        for (const s of info.all.slice(0, 3)) {
            const pctColor = s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
            let mainTxt = '';
            if (s.has_fund_flow && s.main_force) {
                const mc = s.main_force >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
                mainTxt = ` <span style="color:${mc};font-size:10px">${dashFmtm(s.main_force)}</span>`;
            }
            gridHtml += `<div class="dash-top3-row"><span><span class="dash-top3-name">${s.name}</span><span class="dash-top3-code">${s.code}</span>${mainTxt}</span><span class="dash-top3-pct" style="color:${pctColor}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span></div>`;
        }
        gridHtml += `</div><div class="dash-card-footer"><span>领涨: ${info.top ? info.top.name : '-'} ${info.top ? (info.top.change_pct >= 0 ? '+' : '') + info.top.change_pct.toFixed(2) + '%' : ''}</span><span>点击查看全部</span></div></div>`;
    }
    document.getElementById('dashThemeGrid').innerHTML = gridHtml;
}

// 当切换到板块龙头tab时加载数据
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('text-gold', 'border-gold');
        btn.classList.add('text-gray-400', 'border-transparent');
    });
    document.getElementById('content-' + tabName).style.display = 'block';
    const activeBtn = document.getElementById('tab-' + tabName);
    activeBtn.classList.remove('text-gray-400', 'border-transparent');
    activeBtn.classList.add('text-gold', 'border-gold');
    if (tabName === 'sector' && (!dashData.raw_data || Object.keys(dashData.raw_data).length === 0)) {
        dashLoadData();
    }
}

// 初始化时加载数据
document.addEventListener('DOMContentLoaded', () => {
    dashLoadData();
    document.addEventListener('keydown', e => { if (e.key === 'Escape') dashCloseModal(); });
});
</script>
'''

    body_close = '</body>'
    body_pos = html.rfind(body_close)
    if body_pos != -1:
        html = html[:body_pos] + js_block + '\n' + html[body_pos:]

    # Write back
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write(html)

    print("[OK] 板块龙头股看板已集成到 index.html")
    print(f"     新增: '板块龙头' Tab")
    print(f"     访问: https://saxleo.github.io/A-/")

if __name__ == '__main__':
    integrate()
