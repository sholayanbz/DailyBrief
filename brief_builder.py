#!/usr/bin/env python3
"""
brief_builder.py — Morning Brief HTML Generator (Railway edition)
Usage: python3 brief_builder.py brief-data-YYYY-MM-DD.json
DATA_DIR env var controls where gex-data.json is read from and HTML is written to.
"""

import json
import sys
import os
from datetime import datetime

# ─── CSS + BASE TEMPLATE (never changes) ─────────────────────────────────────

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e8e8f0;font-family:'Inter',sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.container{max-width:780px;margin:0 auto;padding:32px 20px}
a{color:#6c8cff;text-decoration:none}
a:hover{text-decoration:underline}
.header{text-align:center;padding:48px 0 40px;border-bottom:1px solid rgba(108,140,255,0.15)}
.logo{font-size:13px;font-weight:800;letter-spacing:6px;color:#6c8cff;text-transform:uppercase;margin-bottom:8px}
.header-date{font-size:14px;color:#7a7a8e;font-weight:400;margin-bottom:20px}
.headline{font-size:28px;font-weight:800;line-height:1.25;color:#fff;margin-bottom:8px}
.subtitle{font-size:15px;color:#7a7a8e;font-weight:400}
.exec-summary{background:linear-gradient(135deg,rgba(108,140,255,0.08),rgba(108,140,255,0.03));border:1px solid rgba(108,140,255,0.2);border-radius:12px;padding:24px 28px;margin:32px 0;font-size:15px;line-height:1.75;color:#c8c8d8}
.exec-summary strong{color:#fff}
.section-title{font-size:12px;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:#6c8cff;margin:40px 0 20px;display:flex;align-items:center;gap:10px}
.section-title::after{content:'';flex:1;height:1px;background:rgba(108,140,255,0.15)}
.market-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}
@media(max-width:600px){.market-grid{grid-template-columns:repeat(2,1fr)}}
.market-card{background:#12121a;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;text-align:center}
.market-card .label{font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:#7a7a8e;margin-bottom:6px}
.market-card .value{font-size:20px;font-weight:700;color:#fff;margin-bottom:4px;font-family:'JetBrains Mono',monospace}
.market-card .change{font-size:13px;font-weight:600;font-family:'JetBrains Mono',monospace}
.up{color:#34d399}.down{color:#f87171}.neutral{color:#7a7a8e}
.macro-card{background:#12121a;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:20px 24px;margin-bottom:14px;border-left:3px solid #6c8cff}
.macro-card.critical{border-left-color:#f87171}
.macro-card.important{border-left-color:#fbbf24}
.macro-card.monitor{border-left-color:#34d399}
.macro-tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;padding:3px 10px;border-radius:4px;margin-bottom:10px}
.macro-tag.critical{background:rgba(248,113,113,0.15);color:#f87171}
.macro-tag.important{background:rgba(251,191,36,0.15);color:#fbbf24}
.macro-tag.monitor{background:rgba(52,211,153,0.15);color:#34d399}
.macro-card h3{font-size:16px;font-weight:700;color:#fff;margin-bottom:8px}
.macro-card p{font-size:14px;color:#a0a0b8;line-height:1.7;margin-bottom:10px}
.macro-card .implication{font-size:13px;font-weight:600;color:#fbbf24;padding-top:8px;border-top:1px solid rgba(255,255,255,0.05)}
.cal-table{width:100%;border-collapse:collapse;font-size:14px}
.cal-table th{text-align:left;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#7a7a8e;padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.08)}
.cal-table td{padding:12px;border-bottom:1px solid rgba(255,255,255,0.04);color:#c8c8d8}
.cal-table tr:hover{background:rgba(108,140,255,0.04)}
.impact-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}
.impact-high{background:#f87171}.impact-med{background:#fbbf24}.impact-low{background:#34d399}
.geo-card{background:#12121a;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:20px 24px;margin-bottom:14px}
.geo-card h3{font-size:15px;font-weight:700;color:#fff;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.status-tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:3px 8px;border-radius:4px}
.status-active{background:rgba(248,113,113,0.15);color:#f87171}
.status-escalating{background:rgba(251,191,36,0.15);color:#fbbf24}
.status-ongoing{background:rgba(108,140,255,0.15);color:#6c8cff}
.geo-card p{font-size:13px;color:#a0a0b8;line-height:1.7;margin-top:6px}
.geo-card .watch{font-size:13px;font-weight:600;color:#6c8cff;margin-top:8px}
.setups-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
@media(max-width:600px){.setups-grid{grid-template-columns:1fr}}
.setup-card{background:#12121a;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:18px 20px}
.setup-card .ticker{font-size:16px;font-weight:800;color:#6c8cff;font-family:'JetBrains Mono',monospace}
.setup-card .name{font-size:12px;color:#7a7a8e;margin-bottom:8px}
.setup-card .notes{font-size:13px;color:#c8c8d8;line-height:1.6}
.gex-table{width:100%;border-collapse:collapse;font-size:13px;font-family:'JetBrains Mono',monospace}
.gex-table th{text-align:left;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#7a7a8e;padding:10px;border-bottom:1px solid rgba(255,255,255,0.08)}
.gex-table td{padding:10px;border-bottom:1px solid rgba(255,255,255,0.04)}
.gex-table tr:hover{background:rgba(108,140,255,0.04)}
.gex-table .ticker-col{color:#6c8cff;font-weight:700}
.gex-table .put-wall{color:#f87171}.gex-table .gamma-flip{color:#fbbf24}.gex-table .call-wall{color:#34d399}
.gex-cat{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#7a7a8e;padding:14px 10px 6px;border-bottom:none}
.bias-bull{color:#34d399;font-weight:600}.bias-bear{color:#f87171;font-weight:600}.bias-neutral{color:#fbbf24;font-weight:600}
.gex-note{background:rgba(108,140,255,0.06);border:1px solid rgba(108,140,255,0.12);border-radius:8px;padding:14px 18px;margin-top:16px;font-size:12px;color:#a0a0b8;line-height:1.7}
.gex-note strong{color:#c8c8d8}
.earnings-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
@media(max-width:600px){.earnings-grid{grid-template-columns:1fr}}
.earnings-card{background:#12121a;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:18px 20px}
.earnings-card .ticker{font-size:16px;font-weight:800;color:#6c8cff;font-family:'JetBrains Mono',monospace}
.earnings-card .timing{font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:#7a7a8e;margin-left:8px}
.earnings-card .day{font-size:12px;color:#7a7a8e;margin-bottom:6px}
.earnings-card .why{font-size:13px;color:#c8c8d8;line-height:1.6}
.footer{text-align:center;padding:40px 0 32px;border-top:1px solid rgba(108,140,255,0.1);margin-top:48px}
.footer .brand{font-size:11px;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:#6c8cff;margin-bottom:8px}
.footer .disclaimer{font-size:11px;color:#555;line-height:1.6;max-width:500px;margin:0 auto}
"""

FONTS = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'

# GEX categories and which tickers belong to each
GEX_CATEGORIES = [
    ("Indexes",              ["SPX", "NDX", "VIX"]),
    ("ETFs",                 ["SPY", "QQQ", "IWM"]),
    ("Macro / Commodities",  ["USO", "GLD", "TLT"]),
    ("Futures",              ["ES_SPX", "NQ_NDX"]),
    ("Key Stocks",           ["NVDA", "AAPL", "TSLA", "META", "AMD", "MU"]),
]

FUTURES_DISPLAY = {"ES_SPX": "ES", "NQ_NDX": "NQ"}

# ─── SECTION RENDERERS ────────────────────────────────────────────────────────

def render_header(d):
    return f"""
<div class="header">
  <div class="logo">The Daily Brief</div>
  <div class="header-date">{d['date_display']} &bull; Post-Market Edition</div>
  <h1 class="headline">{d['headline']}</h1>
  <div class="subtitle">{d['subtitle']}</div>
</div>"""

def render_exec_summary(d):
    return f"""
<div class="section-title">Executive Summary</div>
<div class="exec-summary">{d['exec_summary']}</div>"""

def render_market_snapshot(items):
    cards = "\n".join(
        f"""  <div class="market-card">
    <div class="label">{m['label']}</div>
    <div class="value">{m['value']}</div>
    <div class="change {m['direction']}">{'&#9650;' if m['direction']=='up' else '&#9660;'} {m['change']}</div>
  </div>"""
        for m in items
    )
    # Split into rows of 4
    main = items[:8]
    extra = items[8:]
    main_cards = "\n".join(
        f"""  <div class="market-card">
    <div class="label">{m['label']}</div>
    <div class="value">{m['value']}</div>
    <div class="change {m['direction']}">{'&#9650;' if m['direction']=='up' else '&#9660;'} {m['change']}</div>
  </div>"""
        for m in main
    )
    extra_html = ""
    if extra:
        extra_cards = "\n".join(
            f"""  <div class="market-card">
    <div class="label">{m['label']}</div>
    <div class="value">{m['value']}</div>
    <div class="change {m['direction']}">{'&#9650;' if m['direction']=='up' else '&#9660;'} {m['change']}</div>
  </div>"""
            for m in extra
        )
        cols = len(extra)
        extra_html = f'\n<div class="market-grid" style="grid-template-columns:repeat({cols},1fr);max-width:{cols*195}px;margin:8px auto 0">\n{extra_cards}\n</div>'

    return f"""
<div class="section-title">Market Snapshot</div>
<div class="market-grid">
{main_cards}
</div>{extra_html}"""

def render_rrg(sectors):
    """Render an inline Relative Rotation Graph from sector tail data."""
    if not sectors:
        return ""
    data_js = json.dumps(sectors)
    return f"""
<div class="section-title">Sector Rotation — RRG</div>
<div style="background:#12121a;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px 12px 12px">
  <div style="text-align:center;font-size:11px;color:#7a7a8e;margin-bottom:6px;font-family:'Inter',sans-serif;letter-spacing:1px">vs. SPY &bull; Weekly periods &bull; Hover for details</div>
  <svg id="brief-rrg" viewBox="0 0 700 440" style="width:100%;height:auto;display:block" xmlns="http://www.w3.org/2000/svg"></svg>
  <div id="rrg-tip" style="position:fixed;background:#1a1a2e;border:1px solid rgba(108,140,255,0.3);border-radius:8px;padding:10px 14px;pointer-events:none;opacity:0;transition:opacity 0.15s;z-index:999;min-width:150px;font-family:'Inter',sans-serif"></div>
</div>
<script>
(function(){{
  var S={data_js};
  var W=700,H=440,P={{t:38,r:38,b:50,l:50}};
  var CW=W-P.l-P.r, CH=H-P.t-P.b;
  var NS='http://www.w3.org/2000/svg';
  // Auto-fit axis range to actual data with padding
  var allR=[],allM=[];
  S.forEach(function(s){{ s.tail.forEach(function(p){{ allR.push(p[0]); allM.push(p[1]); }}); }});
  var PAD=1.5;
  var XN=Math.min.apply(null,allR)-PAD, XX=Math.max.apply(null,allR)+PAD;
  var YN=Math.min.apply(null,allM)-PAD, YX=Math.max.apply(null,allM)+PAD;
  // Always keep 100 comfortably visible
  XN=Math.min(XN,98.5); XX=Math.max(XX,101.5);
  YN=Math.min(YN,98.5); YX=Math.max(YX,101.5);
  function px(r,m){{ return [P.l+(r-XN)/(XX-XN)*CW, P.t+(YX-m)/(YX-YN)*CH]; }}
  var C=px(100,100), CX=C[0], CY=C[1];
  var svg=document.getElementById('brief-rrg');
  function el(tag,a,p){{
    var e=document.createElementNS(NS,tag);
    for(var k in a)e.setAttribute(k,a[k]);
    (p||svg).appendChild(e); return e;
  }}
  function tx(t,a,p){{ var e=el('text',a,p); e.textContent=t; return e; }}
  // Quadrant fills
  [
    [CX,P.t,P.l+CW-CX,CY-P.t,'rgba(52,211,153,0.05)'],
    [CX,CY,P.l+CW-CX,P.t+CH-CY,'rgba(251,191,36,0.05)'],
    [P.l,CY,CX-P.l,P.t+CH-CY,'rgba(248,113,113,0.05)'],
    [P.l,P.t,CX-P.l,CY-P.t,'rgba(108,140,255,0.05)']
  ].forEach(function(q){{ el('rect',{{x:q[0],y:q[1],width:q[2],height:q[3],fill:q[4]}}); }});
  // Grid lines — dynamic range
  var gStart=Math.ceil(Math.min(XN,YN)), gEnd=Math.floor(Math.max(XX,YX));
  for(var v=gStart;v<=gEnd;v++){{
    var xp=px(v,YN)[0], yp=px(XN,v)[1];
    var lc=v===100?'rgba(255,255,255,0.2)':'rgba(255,255,255,0.05)', sw=v===100?'1.5':'0.5';
    el('line',{{x1:xp,y1:P.t,x2:xp,y2:P.t+CH,stroke:lc,'stroke-width':sw}});
    el('line',{{x1:P.l,y1:yp,x2:P.l+CW,y2:yp,stroke:lc,'stroke-width':sw}});
    if(v%2===0){{
      tx(v,{{x:xp,y:P.t+CH+14,fill:'#555','font-size':'8','text-anchor':'middle','font-family':'JetBrains Mono,monospace'}});
      tx(v,{{x:P.l-6,y:yp+3,fill:'#555','font-size':'8','text-anchor':'end','font-family':'JetBrains Mono,monospace'}});
    }}
  }}
  // Quadrant labels
  [
    ['LEADING',  P.l+CW-6,P.t+13,'end',  '#34d399'],
    ['WEAKENING',P.l+CW-6,P.t+CH-8,'end','#fbbf24'],
    ['LAGGING',  P.l+6,   P.t+CH-8,'start','#f87171'],
    ['IMPROVING',P.l+6,   P.t+13,'start','#6c8cff']
  ].forEach(function(q){{
    tx(q[0],{{x:q[1],y:q[2],fill:q[4],opacity:'0.5','font-size':'8','font-weight':'700',
      'letter-spacing':'1.5','text-anchor':q[3],'font-family':'Inter,sans-serif'}});
  }});
  // Axis labels
  tx('\u2190 RS-Ratio \u2192',{{x:P.l+CW/2,y:H-8,fill:'#7a7a8e','font-size':'9','text-anchor':'middle','font-family':'Inter,sans-serif'}});
  tx('\u2190 RS-Momentum \u2192',{{x:12,y:P.t+CH/2,fill:'#7a7a8e','font-size':'9','text-anchor':'middle',
    'font-family':'Inter,sans-serif',transform:'rotate(-90,12,'+(P.t+CH/2)+')'}});
  var tip=document.getElementById('rrg-tip');
  var qmap={{}}; qmap['LL']=['Leading','#34d399']; qmap['LH']=['Weakening','#fbbf24'];
  qmap['HL']=['Improving','#6c8cff']; qmap['HH']=['Lagging','#f87171'];
  function quad(r,m){{
    var k=(r<100?'H':'L')+(m<100?'H':'L');
    return qmap[k]||['—','#7a7a8e'];
  }}
  // --- Pass 1: compute dot positions and initial label anchors ---
  var items=S.map(function(s){{
    var pts=s.tail.map(function(p){{ return px(p[0],p[1]); }});
    var cur=pts[pts.length-1];
    var dx=cur[0]-CX, dy=cur[1]-CY;
    var dist=Math.sqrt(dx*dx+dy*dy)||1;
    var lx=cur[0]+(dx/dist)*18;
    var ly=cur[1]+(dy/dist)*18;
    return {{s:s,pts:pts,cur:cur,lx:lx,ly:ly,alx:lx,aly:ly}};
  }});
  // --- Pass 2: force-based label collision resolution ---
  var MIN_SEP=30;
  for(var iter=0;iter<120;iter++){{
    for(var i=0;i<items.length;i++){{
      for(var j=i+1;j<items.length;j++){{
        var a=items[i],b=items[j];
        var ddx=b.lx-a.lx, ddy=b.ly-a.ly;
        var sep=Math.sqrt(ddx*ddx+ddy*ddy);
        if(sep<MIN_SEP&&sep>0.01){{
          var push=(MIN_SEP-sep)/2;
          var nx=ddx/sep, ny=ddy/sep;
          a.lx-=nx*push*0.55; a.ly-=ny*push*0.55;
          b.lx+=nx*push*0.55; b.ly+=ny*push*0.55;
        }}
      }}
      // Weak spring toward anchor so labels stay near their dot
      items[i].lx+=(items[i].alx-items[i].lx)*0.06;
      items[i].ly+=(items[i].aly-items[i].ly)*0.06;
    }}
  }}
  // --- Pass 3: draw everything ---
  items.forEach(function(item){{
    var s=item.s, pts=item.pts, cur=item.cur, n=pts.length;
    var g=el('g',{{}});
    // Tail lines
    for(var i=0;i<n-1;i++){{
      var op=(0.15+(i/(n-1))*0.6).toFixed(2);
      var lw=(0.7+(i/(n-1))*1.8).toFixed(2);
      el('line',{{x1:pts[i][0],y1:pts[i][1],x2:pts[i+1][0],y2:pts[i+1][1],
        stroke:s.color,'stroke-width':lw,opacity:op,'stroke-linecap':'round'}},g);
    }}
    // Tail dots
    pts.slice(0,-1).forEach(function(p,i){{
      el('circle',{{cx:p[0],cy:p[1],r:'2',fill:s.color,opacity:(0.15+(i/(n-1))*0.3).toFixed(2)}},g);
    }});
    // Arrow
    if(n>=2){{
      var prev=pts[n-2];
      var ang=(Math.atan2(cur[1]-prev[1],cur[0]-prev[0])*180/Math.PI).toFixed(1);
      el('polygon',{{points:'0,-4 5,0 0,4',fill:s.color,opacity:'0.85',
        transform:'translate('+cur[0]+','+cur[1]+') rotate('+ang+')'}},g);
    }}
    // Glow + dot
    el('circle',{{cx:cur[0],cy:cur[1],r:'12',fill:s.color,opacity:'0.1'}},g);
    el('circle',{{cx:cur[0],cy:cur[1],r:'6.5',fill:'#12121a',stroke:s.color,'stroke-width':'2'}},g);
    // Leader line if label was pushed far from dot
    var ldx=item.lx-cur[0], ldy=item.ly-cur[1];
    if(Math.sqrt(ldx*ldx+ldy*ldy)>22){{
      el('line',{{x1:cur[0],y1:cur[1],x2:item.lx,y2:item.ly,
        stroke:s.color,'stroke-width':'0.8',opacity:'0.4','stroke-dasharray':'2,2.5'}},g);
    }}
    // Ticker label
    var anchor=item.lx>=cur[0]?'start':'end';
    tx(s.ticker,{{x:item.lx,y:item.ly+3.5,fill:s.color,'font-size':'9.5','font-weight':'700',
      'text-anchor':anchor,'font-family':'JetBrains Mono,monospace'}},g);
    // Hover hit zone
    var hz=el('circle',{{cx:cur[0],cy:cur[1],r:'17',fill:'transparent','style':'cursor:pointer'}},g);
    hz.addEventListener('mouseenter',function(e){{
      var tail=s.tail[s.tail.length-1], r=tail[0], m=tail[1];
      var q=quad(r,m);
      tip.innerHTML='<div style="font-family:JetBrains Mono,monospace;font-size:14px;font-weight:700;color:'+s.color+';margin-bottom:3px">'+s.ticker+'</div>'
        +'<div style="color:#7a7a8e;font-size:11px;margin-bottom:8px">'+s.name+'</div>'
        +'<div style="display:flex;justify-content:space-between;gap:14px;font-size:11px;color:#c8c8d8;margin-bottom:2px"><span>RS-Ratio</span><span style="font-family:JetBrains Mono,monospace;font-weight:600">'+r.toFixed(2)+'</span></div>'
        +'<div style="display:flex;justify-content:space-between;gap:14px;font-size:11px;color:#c8c8d8;margin-bottom:6px"><span>RS-Momentum</span><span style="font-family:JetBrains Mono,monospace;font-weight:600">'+m.toFixed(2)+'</span></div>'
        +'<div style="font-size:11px;font-weight:700;color:'+q[1]+'">'+q[0]+'</div>';
      tip.style.opacity='1';
      tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
    }});
    hz.addEventListener('mousemove',function(e){{
      tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
    }});
    hz.addEventListener('mouseleave',function(){{ tip.style.opacity='0'; }});
    svg.appendChild(g);
  }});
}})();
</script>"""


def render_macro_radar(cards):
    html = '\n<div class="section-title">Macro Radar</div>\n'
    for c in cards:
        p = c['priority']
        html += f"""
<div class="macro-card {p}">
  <span class="macro-tag {p}">{p.capitalize()}</span>
  <h3>{c['title']}</h3>
  <p>{c['body']}</p>
  <div class="implication">Market implication: {c['implication']}</div>
</div>"""
    return html

def render_calendar(events):
    rows = "\n".join(
        f"""    <tr>
      <td>{e['date']}</td>
      <td>{e['event']}</td>
      <td>{e['detail']}</td>
      <td><span class="impact-dot impact-{e['impact']}"></span>{e['impact'].capitalize()}</td>
    </tr>"""
        for e in events
    )
    return f"""
<div class="section-title">Week Ahead Calendar</div>
<table class="cal-table">
  <thead>
    <tr><th>Date</th><th>Event</th><th>Detail</th><th>Impact</th></tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>"""

def render_geopolitical(cards):
    html = '\n<div class="section-title">Geopolitical Watch</div>\n'
    for c in cards:
        html += f"""
<div class="geo-card">
  <h3><span class="status-tag status-{c['status']}">{c['status_label']}</span> {c['title']}</h3>
  <p>{c['body']}</p>
  <div class="watch">Watch: {c['watch']}</div>
</div>"""
    return html

def render_setups(cards):
    items = "\n".join(
        f"""  <div class="setup-card">
    <div class="ticker">{c['ticker']}</div>
    <div class="name">{c['name']}</div>
    <div class="notes">{c['notes']}</div>
  </div>"""
        for c in cards
    )
    return f"""
<div class="section-title">Setups to Watch</div>
<div class="setups-grid">
{items}
</div>"""

def render_gex(gex_path, generated_at):
    """Read gex-data.json and render the GEX table."""
    if not os.path.exists(gex_path):
        return f"""
<div class="section-title">GEX Levels — Tomorrow's Dealer Positioning</div>
<div class="gex-note"><strong>Data unavailable.</strong> gex-data.json was not found. Check that the GEX fetcher script ran.</div>"""

    with open(gex_path) as f:
        gex = json.load(f)

    gen_ts = gex.get("generated_at", "")
    today_str = generated_at[:10]  # YYYY-MM-DD
    stale = not gen_ts.startswith(today_str)

    stale_warning = ""
    if stale:
        stale_warning = f'<div class="gex-note" style="margin-bottom:12px"><strong>⚠ Stale data.</strong> GEX file was generated at {gen_ts}, not today. Check the gex-fetcher script.</div>'

    tickers_data = gex.get("tickers", {})
    rows = ""
    for cat_name, tickers in GEX_CATEGORIES:
        rows += f'<tr><td colspan="6" class="gex-cat">{cat_name}</td></tr>\n'
        for t in tickers:
            if t not in tickers_data:
                continue
            g = tickers_data[t].get("classic_gex", {})
            spot     = g.get("spot", "—")
            flip     = g.get("zero_gamma", "—")
            call_vol = g.get("major_pos_vol", "—")
            call_oi  = g.get("major_pos_oi", "—")
            put_vol  = g.get("major_neg_vol", "—")
            put_oi   = g.get("major_neg_oi", "—")
            display = FUTURES_DISPLAY.get(t, t)
            # Bias: spot vs gamma flip
            try:
                bias_class = "bias-bull" if float(spot) > float(flip) else "bias-bear"
                bias_label = "Bullish" if float(spot) > float(flip) else "Bearish"
                if abs(float(spot) - float(flip)) / float(flip) < 0.001:
                    bias_class, bias_label = "bias-neutral", "Neutral"
            except (TypeError, ValueError, ZeroDivisionError):
                bias_class, bias_label = "bias-neutral", "—"

            def fmt(v):
                try:
                    f = float(v)
                    return f"{f:,.2f}" if f < 1000 else f"{f:,.0f}"
                except (TypeError, ValueError):
                    return str(v)

            rows += f"""<tr>
  <td class="ticker-col">{display}</td>
  <td>{fmt(spot)}</td>
  <td class="put-wall">{fmt(put_vol)} / {fmt(put_oi)}</td>
  <td class="gamma-flip">{fmt(flip)}</td>
  <td class="call-wall">{fmt(call_vol)} / {fmt(call_oi)}</td>
  <td class="{bias_class}">{bias_label}</td>
</tr>\n"""

    return f"""
<div class="section-title">GEX Levels — Tomorrow's Dealer Positioning</div>
{stale_warning}
<table class="gex-table">
  <thead>
    <tr><th>Ticker</th><th>Spot</th><th class="put-wall">Put Wall <span style="font-size:9px;font-weight:400;color:#7a7a8e;letter-spacing:0">(vol / oi)</span></th><th class="gamma-flip">Gamma Flip</th><th class="call-wall">Call Wall <span style="font-size:9px;font-weight:400;color:#7a7a8e;letter-spacing:0">(vol / oi)</span></th><th>Bias</th></tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>
<div class="gex-note">
  <strong>How to read this:</strong> The <span style="color:#f87171">Put Wall</span> is the strike with the highest negative gamma — acts as support. The <span style="color:#fbbf24">Gamma Flip</span> is where dealer gamma shifts from negative to positive — above this level, dealers stabilize price; below it, they amplify moves. The <span style="color:#34d399">Call Wall</span> is the strike with the highest positive gamma — acts as resistance. <strong>Bias</strong> is determined by spot price relative to the gamma flip level. Data as of {gen_ts[:16].replace('T',' ')} via GexBot.
</div>"""

def render_earnings(cards):
    items = ""
    for c in cards:
        catalyst = c.get("catalyst", False)
        style = ' style="grid-column:1/-1;background:rgba(251,191,36,0.06);border-color:rgba(251,191,36,0.15)"' if catalyst else ""
        ticker_style = ' style="color:#fbbf24"' if catalyst else ""
        timing_html = f'<span class="timing">{c["timing"]}</span>' if not catalyst else ""
        items += f"""  <div class="earnings-card"{style}>
    <div><span class="ticker"{ticker_style}>{c['ticker']}</span>{timing_html}</div>
    <div class="day">{c['day']}</div>
    <div class="why">{c['why']}</div>
  </div>\n"""
    return f"""
<div class="section-title">Earnings on Deck</div>
<div class="earnings-grid">
{items}
</div>"""

def render_footer():
    return """
<div class="footer">
  <div class="brand">The Daily Brief</div>
  <div style="font-size:12px;color:#7a7a8e;margin-bottom:12px">Generated by your AI Research Desk</div>
  <div class="disclaimer">This brief is for informational purposes only and does not constitute investment advice, a recommendation, or a solicitation to buy or sell any securities. All data sourced from public markets and web searches. Past performance is not indicative of future results. Always do your own research and consult a licensed financial advisor before making investment decisions.</div>
</div>"""

# ─── MAIN ASSEMBLER ───────────────────────────────────────────────────────────

def build(data_path):
    with open(data_path) as f:
        d = json.load(f)

    date_str = d.get("date", datetime.today().strftime("%Y-%m-%d"))
    data_dir = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
    gex_path = os.path.join(data_dir, "gex-data.json")

    sections = [
        render_header(d),
        render_exec_summary(d),
        render_market_snapshot(d["market_snapshot"]),
        render_rrg(d.get("sector_rotation", [])),
        render_macro_radar(d["macro_cards"]),
        render_calendar(d["calendar"]),
        render_geopolitical(d["geopolitical"]),
        render_setups(d["setups"]),
        render_gex(gex_path, d.get("date", "")),
        render_earnings(d["earnings"]),
        render_footer(),
    ]

    body = "\n".join(sections)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Daily Brief — {d.get('date_display', date_str)}</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="container">
{body}
</div>
</body>
</html>"""

    out_path = os.path.join(data_dir, f"post-market-brief-{date_str}.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"✓ Brief written to: {out_path}")
    return out_path


def run(data_path: str) -> str:
    """Callable entry point for main.py pipeline."""
    return build(data_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 brief_builder.py brief-data-YYYY-MM-DD.json")
        sys.exit(1)
    build(sys.argv[1])
