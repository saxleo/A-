#!/usr/bin/env python3
"""
integrate_dashboard_v2.py - V2版板块龙头股看板集成脚本
9主题3×3网格 + 4层深度导航
"""

import re
from pathlib import Path

REPO = Path("/root/.openclaw/workspace/stock-review")
INDEX = REPO / "index.html"

DASHBOARD_CSS = """
/* ========== 板块龙头股看板 V2 样式 ========== */
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

.dash-container { padding: 20px; max-width: 1400px; margin: 0 auto; }

/* 自选栏 */
.dash-fav-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; background: var(--dash-card);
  border: 1px solid var(--dash-border); border-radius: 8px;
  margin-bottom: 20px; overflow-x: auto;
}
.dash-fav-label { font-size: 16px; font-weight: 700; white-space: nowrap; color: var(--dash-gold); }
.dash-fav-tag {
  display: flex; align-items: center; gap: 6px; padding: 4px 12px;
  background: var(--dash-elevated); border-radius: 20px; cursor: pointer;
  border: 1px solid var(--dash-border); white-space: nowrap; font-size: 13px;
  color: var(--dash-text); transition: all .15s;
}
.dash-fav-tag:hover { border-color: var(--dash-accent); }
.dash-fav-add {
  padding: 4px 12px; border: 1px dashed var(--dash-border); border-radius: 20px;
  color: var(--dash-muted); cursor: pointer; white-space: nowrap; font-size: 13px;
}

/* 第一层：3×3主题网格 */
.dash-theme-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
@media (max-width: 1024px) { .dash-theme-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .dash-theme-grid { grid-template-columns: 1fr; } }

.dash-theme-card {
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 12px;
  padding: 16px; cursor: pointer; transition: all .2s;
}
.dash-theme-card:hover { border-color: var(--dash-accent); transform: translateY(-2px); }
.dash-theme-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
}
.dash-theme-title { font-size: 16px; font-weight: 700; color: var(--dash-text); }
.dash-theme-emoji { font-size: 20px; margin-right: 6px; }
.dash-theme-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 500;
}
.dash-tag-bull { background: var(--dash-up-bg); color: var(--dash-up); }
.dash-tag-sideways { background: rgba(245,158,11,0.15); color: #f59e0b; }
.dash-tag-bear { background: var(--dash-down-bg); color: var(--dash-down); }
.dash-tag-accum { background: rgba(59,130,246,0.15); color: var(--dash-accent); }

.dash-theme-stats {
  display: flex; gap: 16px; margin-bottom: 14px;
}
.dash-stat-item { display: flex; flex-direction: column; }
.dash-stat-label { font-size: 11px; color: var(--dash-muted); margin-bottom: 2px; }
.dash-stat-val { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 15px; }

.dash-sector-list { display: flex; flex-direction: column; gap: 6px; }
.dash-sector-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: var(--dash-elevated); border-radius: 6px; font-size: 12px;
}
.dash-sector-name { font-weight: 500; color: var(--dash-text); }
.dash-sector-pct { font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.dash-sector-flow { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--dash-muted); }

.dash-theme-footer {
  display: flex; justify-content: space-between; margin-top: 12px;
  font-size: 11px; color: var(--dash-muted); padding-top: 10px; border-top: 1px solid var(--dash-border);
}

/* 第二层：细分列表 */
.dash-page-sector { display: none; }
.dash-page-sector.active { display: block; }

.dash-breadcrumb { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; font-size: 14px; color: var(--dash-text); }
.dash-breadcrumb a { color: var(--dash-accent); cursor: pointer; }
.dash-breadcrumb a:hover { text-decoration: underline; }

.dash-sector-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.dash-sector-card {
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 12px;
  padding: 16px; cursor: pointer; transition: all .2s;
}
.dash-sector-card:hover { border-color: var(--dash-accent); }

/* 第三层：个股表格 */
.dash-page-stock { display: none; }
.dash-page-stock.active { display: block; }

.dash-stock-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.dash-stock-table thead th {
  text-align: left; padding: 10px 12px; color: var(--dash-muted); font-weight: 500;
  border-bottom: 1px solid var(--dash-border); position: sticky; top: 0; background: var(--dash-card);
  white-space: nowrap;
}
.dash-stock-table td { padding: 10px 12px; border-bottom: 1px solid var(--dash-border); vertical-align: middle; color: var(--dash-text); }
.dash-stock-table tbody tr { cursor: pointer; transition: background .1s; }
.dash-stock-table tbody tr:hover td { background: var(--dash-elevated); }
.dash-stock-table .rank { text-align: center; color: var(--dash-muted); font-weight: 600; width: 40px; }
.dash-stock-table .name-cell { display: flex; flex-direction: column; }
.dash-stock-table .code-txt { font-size: 11px; color: var(--dash-muted); }
.dash-stock-table .mono { font-family: 'JetBrains Mono', monospace; }
.dash-stock-table .change { font-weight: 700; text-align: right; }
.dash-stock-table .price { text-align: right; }
.dash-stock-table .amount { text-align: right; color: var(--dash-muted); font-size: 12px; }
.dash-btn-sm { padding: 3px 8px; border-radius: 4px; font-size: 11px; border: none; cursor: pointer; }
.dash-btn-fav { background: rgba(245,158,11,0.2); color: var(--dash-gold); }
.dash-btn-detail { background: var(--dash-accent); color: #fff; }

/* 第四层：弹窗 */
.dash-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 200;
  display: none; align-items: center; justify-content: center; padding: 20px;
}
.dash-overlay.active { display: flex; }
.dash-modal {
  background: var(--dash-card); border: 1px solid var(--dash-border); border-radius: 16px;
  width: 100%; max-width: 720px; max-height: 90vh; overflow-y: auto;
}
.dash-modal-header { padding: 18px 24px; border-bottom: 1px solid var(--dash-border); display: flex; justify-content: space-between; align-items: center; }
.dash-modal-title { font-size: 18px; font-weight: 600; color: var(--dash-text); }
.dash-modal-close { background: none; border: none; color: var(--dash-muted); font-size: 24px; cursor: pointer; }
.dash-modal-body { padding: 20px 24px; }

.dash-info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.dash-info-item { background: var(--dash-elevated); border-radius: 8px; padding: 10px 12px; text-align: center; }
.dash-info-label { font-size: 11px; color: var(--dash-muted); margin-bottom: 2px; }
.dash-info-val { font-size: 14px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

.dash-kline-tabs { display: flex; gap: 8px; margin-bottom: 16px; }
.dash-kline-tab { padding: 4px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; border: 1px solid var(--dash-border); background: var(--dash-elevated); color: var(--dash-text); }
.dash-kline-tab.active { background: var(--dash-accent); color: #fff; }
.dash-kline-canvas { width: 100%; height: 200px; background: var(--dash-elevated); border-radius: 8px; margin-bottom: 16px; }

.dash-book-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.dash-book-col h4 { font-size: 13px; margin-bottom: 10px; color: var(--dash-muted); }
.dash-book-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--dash-border); font-size: 12px; color: var(--dash-text); }
.dash-book-price { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
.dash-book-vol { color: var(--dash-muted); font-size: 11px; }
.dash-book-buy .dash-book-price { color: var(--dash-up); }
.dash-book-sell .dash-book-price { color: var(--dash-down); }
.dash-book-bar { height: 3px; border-radius: 2px; margin-top: 2px; }
.dash-book-buy .dash-book-bar { background: var(--dash-up); }
.dash-book-sell .dash-book-bar { background: var(--dash-down); }

@media (max-width: 600px) {
  .dash-info-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-book-grid { grid-template-columns: 1fr; }
  .dash-theme-grid { grid-template-columns: 1fr; }
}
"""

def integrate():
    with open(INDEX, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Insert "板块龙头" tab as FIRST tab
    tab_html = '''            <button onclick="switchTab('sector')" id="tab-sector" class="tab-btn pb-3 text-sm font-medium text-gray-400 border-b-2 border-transparent hover:text-gray-200 whitespace-nowrap">
                <i class="fas fa-fire mr-1.5"></i>板块龙头
            </button>'''
    
    # Find the first tab button (风向早报) and insert before it
    first_tab_match = re.search(r'<button onclick="switchTab\(\'wind\'\).*?</button>', html, re.DOTALL)
    if first_tab_match:
        insert_pos = first_tab_match.start()
        html = html[:insert_pos] + tab_html + '\n' + html[insert_pos:]

    # 2. Add content section before closing main tag
    content_html = f'''
        <!-- 板块龙头股看板 V2 -->
        <div id="content-sector" class="tab-content" style="display:none">
            <div class="dash-container">
                <!-- 自选栏 -->
                <div class="dash-fav-bar" id="dashFavBar">
                    <span class="dash-fav-label">⭐ 自选</span>
                    <span class="dash-fav-add" onclick="dashAddFav()">+ 添加自选</span>
                </div>
                
                <!-- 第一层：9主题卡片 -->
                <div id="dashPage1">
                    <div class="dash-theme-grid" id="dashThemeGrid"></div>
                </div>
                
                <!-- 第二层：细分赛道列表 -->
                <div id="dashPage2" class="dash-page-sector">
                    <div class="dash-breadcrumb">
                        <a onclick="dashGoToPage1()">📊 主题概览</a>
                        <span>/</span>
                        <span id="dashBreadcrumbTheme"></span>
                    </div>
                    <div class="dash-sector-grid" id="dashSectorGrid"></div>
                </div>
                
                <!-- 第三层：个股表格 -->
                <div id="dashPage3" class="dash-page-stock">
                    <div class="dash-breadcrumb">
                        <a onclick="dashGoToPage1()">📊 主题概览</a>
                        <span>/</span>
                        <a onclick="dashGoToPage2()" id="dashBreadcrumbSector"></a>
                        <span>/</span>
                        <span id="dashBreadcrumbStockSector"></span>
                    </div>
                    <div id="dashStockTableWrap"></div>
                </div>
                
                <!-- 第四层：弹窗 -->
                <div id="dashOverlay" class="dash-overlay" onclick="dashCloseModal(event)">
                    <div class="dash-modal" onclick="event.stopPropagation()">
                        <div class="dash-modal-header">
                            <div class="dash-modal-title" id="dashModalTitle"></div>
                            <button class="dash-modal-close" onclick="dashCloseModal()">×</button>
                        </div>
                        <div class="dash-modal-body">
                            <div class="dash-info-grid" id="dashInfoGrid"></div>
                            <div class="dash-kline-tabs">
                                <div class="dash-kline-tab active" onclick="dashSwitchTab(this,'book')">📊 五档盘口</div>
                                <div class="dash-kline-tab" onclick="dashSwitchTab(this,'kline')">📈 走势</div>
                            </div>
                            <div id="dashTabContentBook">
                                <div class="dash-book-grid" id="dashBookGrid"></div>
                                <div style="background:var(--dash-elevated);border-radius:8px;padding:12px 16px;margin-top:16px">
                                    <div style="font-size:12px;color:var(--dash-muted);margin-bottom:4px">盘口差估算 (买盘力量 - 卖盘力量)</div>
                                    <div style="font-size:18px;font-weight:700;font-family:'JetBrains Mono',monospace" id="dashBookDiffVal"></div>
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
        </div>
'''

    main_close = '</main>'
    main_pos = html.find(main_close)
    if main_pos != -1:
        html = html[:main_pos] + content_html + html[main_pos:]

    # 3. Add CSS
    css_block = f'<style>\n{DASHBOARD_CSS}\n</style>'
    head_close = '</head>'
    head_pos = html.find(head_close)
    if head_pos != -1:
        html = html[:head_pos] + css_block + '\n' + html[head_pos:]

    # 4. Add JavaScript
    js_block = '''
<script>
// ===== 板块龙头股看板 V2 =====
let dashData = {};
let dashCurrentTheme = null;
let dashCurrentSector = null;

// 9主题分类映射
const THEME_MAP = {
    'AI芯片/GPU': ['🧠', 'AI芯片'],
    '先进封装/测试': ['🧠', 'AI芯片'],
    'EDA/IP': ['🧠', 'AI芯片'],
    '光模块/CPO/光引擎': ['🔆', '光模块'],
    '光芯片/硅光/薄膜铌酸锂': ['🔆', '光模块'],
    '铜缆高速连接': ['🔆', '光模块'],
    '光纤/光器件': ['🔆', '光模块'],
    '半导体设备': ['💎', '半导体'],
    '半导体材料': ['💎', '半导体'],
    '晶圆代工/制造': ['💎', '半导体'],
    'PCB/高速连接板': ['💎', '半导体'],
    'AI服务器': ['⚡', '算力'],
    '算力租赁/IDC': ['⚡', '算力'],
    '液冷散热': ['⚡', '算力'],
    '存力/HBM存储': ['⚡', '算力'],
    '核心零部件': ['🤖', '机器人零部件'],
    '整机+动力系统': ['🤖', '机器人零部件'],
    '整机/执行器/应用': ['🦾', '机器人应用'],
    '设备+整车/应用': ['🦾', '机器人应用'],
    '正负极材料+电解质': ['🔋', '固态电池'],
    '新型电力系统': ['💡', '电力储能'],
    '储能+逆变器': ['💡', '电力储能'],
    '航空装备+航天装备': ['🚀', '军工航天'],
    '舰船+军工信息化': ['🚀', '军工航天'],
    '火箭+地面设备+材料': ['🚀', '军工航天'],
    '卫星制造+应用': ['🚀', '军工航天'],
    '空管/雷达+碳纤维材料': ['🚀', '军工航天'],
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
        html += `<div class="dash-fav-tag" onclick="dashOpenStock('${code}')"><span style="font-weight:500">${s.name}</span><span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:${color}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span><span style="opacity:0;transition:opacity .15s;font-size:12px;color:var(--dash-muted)" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0" onclick="event.stopPropagation();dashToggleFav('${code}')">✕</span></div>`;
    }
    html += '<span class="dash-fav-add" onclick="dashAddFav()">+ 添加自选</span>';
    bar.innerHTML = html;
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

// ===== 第一层：9主题卡片 =====
function dashRenderThemes() {
    if (!dashData.sector_data) return;
    
    // 按9主题聚合
    const themes = {};
    for (const [sectorName, stocks] of Object.entries(dashData.sector_data)) {
        const mapped = THEME_MAP[sectorName];
        if (!mapped) continue;
        const [emoji, themeName] = mapped;
        if (!themes[themeName]) themes[themeName] = { emoji, sectors: [] };
        themes[themeName].sectors.push({ name: sectorName, stocks });
    }
    
    // 计算每个主题的数据
    for (const themeName in themes) {
        const t = themes[themeName];
        const allStocks = [];
        for (const s of t.sectors) allStocks.push(...s.stocks);
        t.avg = allStocks.length ? (allStocks.reduce((a,b) => a + b.change_pct, 0) / allStocks.length).toFixed(2) : 0;
        t.totalMain = allStocks.reduce((a,b) => a + (b.main_force || 0), 0);
        t.totalBook = allStocks.reduce((a,b) => a + (b.book_diff || 0), 0);
        t.up = allStocks.filter(s => s.change_pct > 0).length;
        t.total = allStocks.length;
        t.hasFf = allStocks.filter(s => s.has_fund_flow).length;
        
        // 细分排行（按平均涨幅）
        for (const s of t.sectors) {
            s.avg = s.stocks.length ? (s.stocks.reduce((a,b) => a + b.change_pct, 0) / s.stocks.length).toFixed(2) : 0;
            s.main = s.stocks.reduce((a,b) => a + (b.main_force || 0), 0);
            s.up = s.stocks.filter(x => x.change_pct > 0).length;
        }
        t.sectors.sort((a,b) => b.avg - a.avg);
    }
    
    // 按平均涨幅排序主题
    const sortedThemes = Object.entries(themes).sort((a,b) => b[1].avg - a[1].avg);
    
    // 渲染3×3网格
    let gridHtml = '';
    for (const [themeName, t] of sortedThemes) {
        const [tagText, tagClass] = dashStatusTag(parseFloat(t.avg));
        const avgColor = t.avg >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const mainColor = (t.hasFf > 0 ? t.totalMain : t.totalBook) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const mainLabel = t.hasFf > 0 ? '主力净流入' : '盘口差';
        const mainVal = t.hasFf > 0 ? t.totalMain : t.totalBook;
        
        gridHtml += `<div class="dash-theme-card" onclick="dashGoToTheme('${themeName}')">
            <div class="dash-theme-header">
                <div class="dash-theme-title"><span class="dash-theme-emoji">${t.emoji}</span>${themeName}</div>
                <div><span class="dash-theme-tag ${tagClass}">${tagText}</span></div>
            </div>
            <div class="dash-theme-stats">
                <div class="dash-stat-item"><span class="dash-stat-label">平均涨跌</span><span class="dash-stat-val" style="color:${avgColor}">${t.avg >= 0 ? '+' : ''}${t.avg}%</span></div>
                <div class="dash-stat-item"><span class="dash-stat-label">${mainLabel}</span><span class="dash-stat-val" style="color:${mainColor}">${dashFmtm(mainVal)}</span></div>
                <div class="dash-stat-item"><span class="dash-stat-label">上涨率</span><span class="dash-stat-val">${t.up}/${t.total}</span></div>
            </div>
            <div class="dash-sector-list">`;
        
        // TOP3细分
        for (const s of t.sectors.slice(0, 3)) {
            const pctColor = s.avg >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
            const mainColor2 = s.main >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
            gridHtml += `<div class="dash-sector-row">
                <span class="dash-sector-name">${s.name}</span>
                <span><span class="dash-sector-pct" style="color:${pctColor}">${s.avg >= 0 ? '+' : ''}${s.avg}%</span> <span class="dash-sector-flow" style="color:${mainColor2}">${dashFmtm(s.main)}</span></span>
            </div>`;
        }
        
        gridHtml += `</div><div class="dash-theme-footer"><span>${t.sectors.length}个细分</span><span>点击查看全部 →</span></div></div>`;
    }
    
    document.getElementById('dashThemeGrid').innerHTML = gridHtml;
}

// ===== 第二层：细分赛道列表 =====
function dashGoToTheme(themeName) {
    dashCurrentTheme = themeName;
    document.getElementById('dashPage1').style.display = 'none';
    document.getElementById('dashPage2').classList.add('active');
    document.getElementById('dashPage3').classList.remove('active');
    document.getElementById('dashBreadcrumbTheme').textContent = themeName;
    dashRenderSectors();
}

function dashRenderSectors() {
    if (!dashData.sector_data || !dashCurrentTheme) return;
    
    const sectors = [];
    for (const [name, stocks] of Object.entries(dashData.sector_data)) {
        const mapped = THEME_MAP[name];
        if (!mapped) continue;
        if (mapped[1] === dashCurrentTheme) sectors.push({ name, stocks });
    }
    
    let html = '';
    for (const s of sectors) {
        const avg = s.stocks.length ? (s.stocks.reduce((a,b) => a + b.change_pct, 0) / s.stocks.length).toFixed(2) : 0;
        const main = s.stocks.reduce((a,b) => a + (b.main_force || 0), 0);
        const book = s.stocks.reduce((a,b) => a + (b.book_diff || 0), 0);
        const up = s.stocks.filter(x => x.change_pct > 0).length;
        const hasFf = s.stocks.filter(x => x.has_fund_flow).length;
        const top = s.stocks.sort((a,b) => b.change_pct - a.change_pct)[0];
        const avgColor = avg >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const mainColor = (hasFf > 0 ? main : book) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        
        html += `<div class="dash-sector-card" onclick="dashGoToSector('${s.name}')">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div style="font-size:15px;font-weight:600;color:var(--dash-text)">${s.name}</div>
                <div style="font-size:13px;color:${avgColor};font-family:'JetBrains Mono',monospace;font-weight:700">${avg >= 0 ? '+' : ''}${avg}%</div>
            </div>
            <div style="display:flex;gap:16px;margin-bottom:12px;font-size:13px">
                <div><span style="font-size:11px;color:var(--dash-muted)">${hasFf > 0 ? '主力净流入' : '盘口差'}</span><br/><span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:${mainColor}">${dashFmtm(hasFf > 0 ? main : book)}</span></div>
                <div><span style="font-size:11px;color:var(--dash-muted)">上涨</span><br/><span style="font-weight:700">${up}/${s.stocks.length}</span></div>
                <div><span style="font-size:11px;color:var(--dash-muted)">成交额</span><br/><span style="font-family:'JetBrains Mono',monospace">${dashFmtm(s.stocks.reduce((a,b) => a + b.amount, 0))}</span></div>
            </div>
            <div style="font-size:12px;color:var(--dash-muted)">领涨: <span style="color:var(--dash-text)">${top ? top.name : '-'} ${top ? (top.change_pct >= 0 ? '+' : '') + top.change_pct.toFixed(2) + '%' : ''}</span></div>
        </div>`;
    }
    
    document.getElementById('dashSectorGrid').innerHTML = html;
}

// ===== 第三层：个股表格 =====
function dashGoToSector(sectorName) {
    dashCurrentSector = sectorName;
    document.getElementById('dashPage2').classList.remove('active');
    document.getElementById('dashPage3').classList.add('active');
    document.getElementById('dashBreadcrumbSector').textContent = dashCurrentTheme;
    document.getElementById('dashBreadcrumbStockSector').textContent = sectorName;
    dashRenderStockTable();
}

function dashGoToPage2() {
    document.getElementById('dashPage3').classList.remove('active');
    document.getElementById('dashPage2').classList.add('active');
}

function dashRenderStockTable() {
    if (!dashData.sector_data || !dashCurrentSector) return;
    const stocks = dashData.sector_data[dashCurrentSector] || [];
    stocks.sort((a,b) => b.change_pct - a.change_pct);
    
    let html = '<table class="dash-stock-table"><thead><tr>';
    html += '<th class="rank">#</th><th>名称</th><th class="price">现价</th><th class="change">涨跌</th>';
    html += '<th class="amount">主力净流</th><th class="amount">盘口差</th><th class="amount">成交额</th><th class="amount">振幅</th><th>操作</th></tr></thead><tbody>';
    
    for (let i = 0; i < stocks.length; i++) {
        const s = stocks[i];
        const pctColor = s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const mainColor = (s.main_force || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const bookColor = (s.book_diff || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)';
        const isF = dashIsFav(s.code);
        const amp = s.high && s.low && s.last_close ? ((s.high - s.low) / s.last_close * 100).toFixed(2) : '-';
        
        html += `<tr onclick="dashOpenStock('${s.code}')">
            <td class="rank">${i+1}</td>
            <td><div class="name-cell"><span>${s.name}</span><span class="code-txt">${s.code}</span></div></td>
            <td class="mono price">${s.price.toFixed(2)}</td>
            <td class="mono change" style="color:${pctColor}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</td>
            <td class="mono amount" style="color:${mainColor}">${s.has_fund_flow ? dashFmtm(s.main_force) : '-'}</td>
            <td class="mono amount" style="color:${bookColor}">${dashFmtm(s.book_diff || 0)}</td>
            <td class="mono amount">${dashFmtm(s.amount)}</td>
            <td class="mono amount">${amp}%</td>
            <td><button class="dash-btn-sm dash-btn-fav" onclick="event.stopPropagation();dashToggleFav('${s.code}');this.textContent=dashIsFav('${s.code}')?'★':'☆'">${isF?'★':'☆'}</button></td>
        </tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('dashStockTableWrap').innerHTML = html;
}

// ===== 第四层：弹窗 =====
function dashOpenStock(code) {
    const s = dashData.raw_data && dashData.raw_data[code];
    if (!s) return;
    
    document.getElementById('dashModalTitle').innerHTML = `<span>${s.name}</span><span style="color:var(--dash-muted);font-size:14px;margin-left:8px">${s.code}</span><span style="color:${s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'};margin-left:12px;font-size:16px">${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span>`;
    
    const amp = s.high && s.low && s.last_close ? ((s.high - s.low) / s.last_close * 100).toFixed(2) : '-';
    let infoHtml = '';
    const fields = [
        ['现价', s.price.toFixed(2), ''],
        ['涨跌', `${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%`, s.change_pct >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'],
        ['开盘', s.open.toFixed(2), ''],
        ['最高', s.high.toFixed(2), ''],
        ['最低', s.low.toFixed(2), ''],
        ['昨收', s.last_close.toFixed(2), ''],
        ['成交量', dashFmtm(s.volume), ''],
        ['成交额', dashFmtm(s.amount), ''],
        ['盘口差', dashFmtm(s.book_diff || 0), (s.book_diff || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'],
        ['主力净流', s.has_fund_flow ? dashFmtm(s.main_force) : '-', (s.main_force || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'],
        ['超大单', s.has_fund_flow ? dashFmtm(s.super) : '-', (s.super || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'],
        ['大单', s.has_fund_flow ? dashFmtm(s.large) : '-', (s.large || 0) >= 0 ? 'var(--dash-up)' : 'var(--dash-down)'],
        ['振幅', `${amp}%`, ''],
        ['所属', s.sector, '']
    ];
    for (const [label, val, color] of fields) {
        infoHtml += `<div class="dash-info-item"><div class="dash-info-label">${label}</div><div class="dash-info-val"${color ? ` style="color:${color}"` : ''}>${val}</div></div>`;
    }
    document.getElementById('dashInfoGrid').innerHTML = infoHtml;
    
    const bids = s.bids || {}; const asks = s.asks || {};
    const maxVol = Math.max(...[1,2,3,4,5].map(j => Math.max(bids[`bid_vol${j}`] || 0, asks[`ask_vol${j}`] || 0))) || 1;
    let bookHtml = '<div class="dash-book-col dash-book-buy"><h4 style="color:var(--dash-up)">买盘</h4>';
    for (let j = 1; j <= 5; j++) {
        const p = bids[`bid${j}`] || 0; const v = bids[`bid_vol${j}`] || 0; const pct = (v / maxVol * 100).toFixed(1);
        bookHtml += `<div class="dash-book-row"><span class="dash-book-price">${p.toFixed(2)}</span><span class="dash-book-vol">${v}手</span></div><div class="dash-book-bar" style="width:${pct}%"></div>`;
    }
    bookHtml += '</div><div class="dash-book-col dash-book-sell"><h4 style="color:var(--dash-down)">卖盘</h4>';
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

function dashCloseModal(e) { if (!e || e.target.id === 'dashOverlay') document.getElementById('dashOverlay').classList.remove('active'); }

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
    for (let i = 0; i <= 4; i++) { const py = 10 + i * (h - 20) / 4; ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(w, py); ctx.stroke(); }
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

function dashSwitchTab(el, tab) {
    document.querySelectorAll('.dash-kline-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('dashTabContentBook').style.display = tab === 'book' ? 'block' : 'none';
    document.getElementById('dashTabContentKline').style.display = tab === 'kline' ? 'block' : 'none';
}

function dashGoToPage1() {
    document.getElementById('dashPage1').style.display = 'block';
    document.getElementById('dashPage2').classList.remove('active');
    document.getElementById('dashPage3').classList.remove('active');
    dashCurrentTheme = null;
    dashCurrentSector = null;
}

// ===== 数据加载 =====
async function dashLoadData() {
    try {
        const resp = await fetch('data/dashboard_v5.json?t=' + Date.now());
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        dashData = await resp.json();
        dashRenderFavBar();
        dashRenderThemes();
    } catch (e) {
        console.error('[Dashboard] Load failed:', e);
        document.getElementById('dashThemeGrid').innerHTML = '<div style="text-align:center;color:var(--dash-muted);padding:40px">数据加载失败，请稍后刷新</div>';
    }
}

// ===== Tab切换改造 =====
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

// ===== 初始化 =====
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

    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write(html)

    print("[OK] V2 板块龙头股看板已集成到 index.html")
    print("     新特性:")
    print("     - 9主题 3×3 网格")
    print("     - 4层导航: 主题→细分→个股→弹窗")
    print("     - 板块龙头 Tab 位于第一位")

if __name__ == '__main__':
    integrate()
