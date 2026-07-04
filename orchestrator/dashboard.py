"""Sekmeli birleşik dashboard: ana sayfa ÖZET + her AI için ayrı detay sekmesi.
Self-contained HTML (inline CSS/JS, harici kaynak yok)."""
from __future__ import annotations

import html
from datetime import datetime
from typing import Dict, List

AI_COLORS = {
    "consensus": "#a855f7", "deepseek": "#38bdf8", "claude": "#f59e0b",
    "microsoft": "#34d399", "codex": "#f472b6",
}
MEDALS = ["🥇", "🥈", "🥉", "", "", ""]
TAB_ORDER = ["consensus", "deepseek", "claude", "codex", "microsoft"]


def _esc(x) -> str:
    return html.escape(str(x))


def _num(x, fmt="{:.2f}"):
    try:
        return fmt.format(float(x))
    except (TypeError, ValueError):
        return "—"


def _side_badge(side: str) -> str:
    s = str(side).upper()
    if s.startswith("BUY") or s == "ALIS":
        cls, txt = "buy", "AL"
    elif "SELL" in s or s == "SATIS":
        cls, txt = "sell", ("SAT ½" if "PARTIAL" in s else "SAT")
    else:
        cls, txt = "hold", _esc(side)
    return f'<span class="badge {cls}">{txt}</span>'


def _chip(name: str, key: str) -> str:
    c = AI_COLORS.get(key, "#64748b")
    return f'<span class="chip" style="--c:{c}">{_esc(name)}</span>'


def _ordered(comps):
    idx = {k: i for i, k in enumerate(TAB_ORDER)}
    return sorted(comps, key=lambda c: idx.get(c["key"], 99))


# ---------- ÖZET ----------

def _leaderboard(comps, xu30):
    ranked = sorted([c for c in comps if c.get("active")],
                    key=lambda c: c["return_pct"], reverse=True)
    cards = []
    for i, c in enumerate(ranked):
        medal = MEDALS[i] if i < len(MEDALS) else ""
        color = AI_COLORS.get(c["key"], "#64748b")
        rc = "pos" if c["return_pct"] >= 0 else "neg"
        alpha = round(c["return_pct"] - xu30, 2)
        ac = "pos" if alpha >= 0 else "neg"
        cards.append(f"""
        <div class="lb-card" style="--c:{color}" onclick="showTab('{c['key']}')">
          <div class="lb-top"><span class="lb-medal">{medal}</span>
            <span class="lb-name">{_esc(c['name'])}</span><span class="lb-rank">#{i+1}</span></div>
          <div class="lb-ret {rc}">%{c['return_pct']:+.2f}</div>
          <div class="lb-meta"><span>Değer <b>{c['value']:,.0f}</b></span>
            <span>Alfa <b class="{ac}">%{alpha:+.2f}</b></span></div>
          <div class="lb-meta"><span>Nakit {c['cash']:,.0f}</span>
            <span>{len(c['positions'])} pozisyon</span></div>
          <div class="lb-cta">detay →</div>
        </div>""")
    inactive = [c for c in comps if not c.get("active")]
    for c in inactive:
        cards.append(f'<div class="lb-card inactive"><div class="lb-name">{_esc(c["name"])}</div>'
                     f'<div class="muted">İlk döngüde portföy oluşacak</div></div>')
    return '<div class="lb-grid">' + "".join(cards) + "</div>"


def _trade_feed(feed):
    if not feed:
        return '<p class="muted">Henüz işlem yok.</p>'
    rows = []
    for t in feed:
        price = t.get("price", "")
        price_s = _num(price) if isinstance(price, (int, float)) and price else _esc(price or "—")
        rows.append(f"""<tr>
          <td class="mono nowrap">{_esc(t.get('ts') or '—')}</td>
          <td>{_chip(t.get('who',''), t.get('who_key',''))}</td>
          <td>{_side_badge(t.get('side',''))}</td>
          <td class="mono"><b>{_esc(t.get('ticker','—'))}</b></td>
          <td class="num mono">{_esc(t.get('qty',''))}</td>
          <td class="num mono">{price_s}</td>
          <td class="reason">{_esc(t.get('reason',''))}</td></tr>""")
    return f"""<div class="scroll"><table class="feed">
      <thead><tr><th>Zaman</th><th>AI</th><th>İşlem</th><th>Hisse</th>
        <th class="num">Adet</th><th class="num">Fiyat</th><th>Gerekçe</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>"""


def _consensus_table(consensus):
    if not consensus:
        return '<p class="muted">Henüz 2+ AI\'ın ortak seçtiği hisse yok.</p>'
    rows = []
    for c in consensus:
        chips = " ".join(f'<span class="mini-chip">{_esc(b["ai"].split()[0])}</span>' for b in c["backers"])
        sc = "pos" if c["deepscore"] >= 65 else ("warn" if c["deepscore"] >= 50 else "neg")
        rows.append(f"""<tr>
          <td class="mono"><b>{_esc(c['ticker'])}</b></td><td>{_esc(c['name'])}</td>
          <td><span class="tag">{_esc(c['sector'])}</span></td>
          <td class="num"><span class="agree">×{c['agreement']}</span></td>
          <td>{chips}</td><td class="num mono {sc}">{_num(c['deepscore'],'{:.1f}')}</td>
          <td class="num mono">{_num(c['rsi'],'{:.0f}')}</td></tr>""")
    return f"""<div class="scroll"><table>
      <thead><tr><th>Hisse</th><th>Şirket</th><th>Sektör</th><th class="num">Ortaklık</th>
        <th>AI'lar</th><th class="num">DeepScore</th><th class="num">RSI</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>"""


# ---------- PER-AI SEKME ----------

def _positions_table(comp):
    if not comp["positions"]:
        return '<p class="muted">Açık pozisyon yok (nakit bekliyor).</p>'
    rows = []
    for p in sorted(comp["positions"], key=lambda x: x["weight_pct"], reverse=True):
        pc = "pos" if p["pnl_pct"] >= 0 else "neg"
        rows.append(f"""<tr>
          <td class="mono"><b>{_esc(p['ticker'])}</b></td>
          <td>{_esc(p.get('name',''))}</td>
          <td><span class="tag">{_esc(p['sector'])}</span></td>
          <td class="num mono">{_esc(int(p['qty']))}</td>
          <td class="num mono">{_num(p['entry'])}</td>
          <td class="num mono">{_num(p['current'])}</td>
          <td class="num mono {pc}">%{p['pnl_pct']:+.1f}</td>
          <td class="num mono">%{_num(p['weight_pct'],'{:.0f}')}</td>
          <td class="num mono">{_num(p.get('stop'))}</td>
          <td class="num mono">{_num(p.get('target'))}</td>
          <td class="num mono">{_num(p.get('score'),'{:.0f}')}</td></tr>""")
    return f"""<div class="scroll"><table>
      <thead><tr><th>Hisse</th><th>Şirket</th><th>Sektör</th><th class="num">Adet</th>
        <th class="num">Giriş</th><th class="num">Güncel</th><th class="num">K/Z</th>
        <th class="num">Ağ.</th><th class="num">Stop</th><th class="num">Hedef</th>
        <th class="num">Skor</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>"""


def _ai_trades(comp):
    trades = comp.get("trades", [])[:25]
    if not trades:
        return ""
    rows = []
    for t in trades:
        price = t.get("price", "")
        price_s = _num(price) if isinstance(price, (int, float)) and price else _esc(price or "—")
        rows.append(f"""<tr><td class="mono nowrap">{_esc(t.get('ts') or '—')}</td>
          <td>{_side_badge(t.get('side',''))}</td><td class="mono"><b>{_esc(t.get('ticker','—'))}</b></td>
          <td class="num mono">{_esc(t.get('qty',''))}</td><td class="num mono">{price_s}</td>
          <td class="reason">{_esc(t.get('reason',''))}</td></tr>""")
    return f"""<h3>İşlem geçmişi</h3><div class="scroll"><table>
      <thead><tr><th>Zaman</th><th>İşlem</th><th>Hisse</th><th class="num">Adet</th>
        <th class="num">Fiyat</th><th>Gerekçe</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>"""


def _research_panel(notes):
    if not notes:
        return ""
    cards = []
    for n in notes:
        v = n["verdict"]
        vc = "pos" if ("AL" in v and "İZLE" not in v) else "warn"
        cards.append(f"""<div class="rn">
          <div class="rn-head"><b class="mono">{_esc(n['ticker'])}</b>
            <span class="muted">{_esc(n['name'])}</span>
            <span class="verdict {vc}">{_esc(v)}</span><span class="agree">×{n['agreement']}</span></div>
          <p class="rn-thesis">{_esc(n['thesis'])}</p>
          <p class="rn-risk">⚠ {_esc(n['risk'])}</p></div>""")
    return '<h3>🔬 Claude araştırma notları</h3><div class="rn-grid">' + "".join(cards) + "</div>"


def _ai_tab(comp, xu30, notes=None):
    color = AI_COLORS.get(comp["key"], "#64748b")
    if not comp.get("active"):
        return (f'<section class="tab" id="tab-{comp["key"]}" hidden>'
                f'<div class="ai-head" style="--c:{color}"><h2>{_esc(comp["name"])}</h2></div>'
                f'<p class="muted">Bu yarışmacı ilk döngüde portföyünü oluşturacak.</p></section>')
    rc = "pos" if comp["return_pct"] >= 0 else "neg"
    alpha = round(comp["return_pct"] - xu30, 2)
    invested = comp["value"] - comp["cash"]
    extra = _research_panel(notes) if comp["key"] == "consensus" else ""
    return f"""<section class="tab" id="tab-{comp['key']}" hidden>
      <div class="ai-head" style="--c:{color}">
        <h2>{_esc(comp['name'])}</h2>
        <span class="ai-style">{_esc(comp.get('style',''))}</span>
      </div>
      <div class="stat-row">
        <div class="stat"><span>Portföy</span><b>{comp['value']:,.0f} TL</b></div>
        <div class="stat"><span>Getiri</span><b class="{rc}">%{comp['return_pct']:+.2f}</b></div>
        <div class="stat"><span>Alfa (XU30)</span><b class="{'pos' if alpha>=0 else 'neg'}">%{alpha:+.2f}</b></div>
        <div class="stat"><span>Nakit</span><b>{comp['cash']:,.0f} TL</b></div>
        <div class="stat"><span>Yatırılan</span><b>{invested:,.0f} TL</b></div>
        <div class="stat"><span>Pozisyon</span><b>{len(comp['positions'])}</b></div>
      </div>
      <h3>Portföy</h3>
      {_positions_table(comp)}
      {extra}
      {_ai_trades(comp)}
    </section>"""


def _tabbar(comps):
    btns = ['<button class="tabbtn active" data-tab="summary" onclick="showTab(\'summary\')">📊 Özet</button>']
    for c in _ordered([c for c in comps if c.get("active")]):
        color = AI_COLORS.get(c["key"], "#64748b")
        btns.append(f'<button class="tabbtn" data-tab="{c["key"]}" style="--c:{color}" '
                    f'onclick="showTab(\'{c["key"]}\')"><span class="dot"></span>{_esc(c["name"])}</button>')
    return '<nav class="tabs">' + "".join(btns) + "</nav>"


def _health_badge(health):
    if not health:
        return ""
    if health.get("ok"):
        news = " · haber: DeepSeek LLM" if health.get("news_llm") else " · haber: havuz"
        fl = health.get("fund_live", 0)
        fund = f" · temel: canlı {fl}" if fl else " · temel: statik"
        return (f'<span class="hbadge ok">● Canlı veri {health.get("live",0)}/{health.get("total",0)}'
                f'{fund}{news}</span>')
    return ('<span class="hbadge bad">⚠ VERİ ESKİ/ÖRNEK — fiyatlar güncel olmayabilir</span>')


def build_dashboard(comps, feed, consensus, notes, consensus_pf, xu30, health=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    active_n = sum(1 for c in comps if c.get("active"))
    total_trades = sum(len(c.get("trades", [])) for c in comps)

    ai_tabs = "".join(_ai_tab(c, xu30, notes if c["key"] == "consensus" else None)
                      for c in _ordered(comps))

    return f"""<!doctype html>
<html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>BIST AI Arena</title>
<style>
  :root {{ --bg:#0b1120; --panel:#111a2e; --panel2:#0f1728; --line:#1e2b45;
    --ink:#e6edf7; --muted:#8798b5; --green:#22c55e; --red:#ef4444;
    --amber:#f59e0b; --accent:#a855f7; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:20px 16px 70px; }}
  header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:12px;
    border-bottom:1px solid var(--line); padding-bottom:14px; }}
  h1 {{ font-size:22px; margin:0; }} h1 .spark {{ color:var(--accent); }}
  .sub {{ color:var(--muted); font-size:13px; }} .sub b {{ color:var(--ink); }}
  h2 {{ font-size:18px; margin:0; }}
  h3 {{ font-size:13px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted);
    margin:26px 0 12px; font-weight:600; }}
  .muted {{ color:var(--muted); }} .num {{ text-align:right; }}
  .nowrap {{ white-space:nowrap; }} .pos {{ color:var(--green); }} .neg {{ color:var(--red); }}
  .warn {{ color:var(--amber); }} .mono {{ font-family:ui-monospace,Menlo,monospace; }}

  .tabs {{ display:flex; flex-wrap:wrap; gap:6px; margin:18px 0 8px; position:sticky; top:0;
    background:var(--bg); padding:8px 0; z-index:5; border-bottom:1px solid var(--line); }}
  .tabbtn {{ display:inline-flex; align-items:center; gap:7px; background:var(--panel);
    color:var(--muted); border:1px solid var(--line); border-radius:999px; padding:7px 14px;
    font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; }}
  .tabbtn .dot {{ width:8px; height:8px; border-radius:50%; background:var(--c,#64748b); }}
  .tabbtn:hover {{ color:var(--ink); }}
  .tabbtn.active {{ color:var(--ink); border-color:var(--c,var(--accent));
    background:color-mix(in srgb,var(--c,var(--accent)) 14%,var(--panel)); }}

  .hbadge {{ font-size:12px; font-weight:600; padding:4px 11px; border-radius:999px; white-space:nowrap; }}
  .hbadge.ok {{ color:var(--green); background:rgba(34,197,94,.12); border:1px solid rgba(34,197,94,.35); }}
  .hbadge.bad {{ color:var(--red); background:rgba(239,68,68,.14); border:1px solid rgba(239,68,68,.45); }}
  .banner {{ background:color-mix(in srgb,var(--accent) 12%,transparent);
    border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);
    border-radius:12px; padding:12px 14px; font-size:13px; margin:16px 0; }}

  .lb-grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(205px,1fr)); }}
  .lb-card {{ background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--c);
    border-radius:14px; padding:15px; cursor:pointer; transition:transform .08s; }}
  .lb-card:hover {{ transform:translateY(-2px); }}
  .lb-card.inactive {{ opacity:.45; border-left-color:var(--line); cursor:default; }}
  .lb-top {{ display:flex; align-items:center; gap:7px; font-size:14px; }}
  .lb-medal {{ font-size:17px; }} .lb-name {{ font-weight:600; }}
  .lb-rank {{ margin-left:auto; color:var(--muted); font-size:12px; }}
  .lb-ret {{ font-size:28px; font-weight:700; margin:8px 0 6px; }}
  .lb-meta {{ display:flex; justify-content:space-between; font-size:12px; color:var(--muted); margin-top:3px; }}
  .lb-cta {{ font-size:11px; color:var(--c); margin-top:9px; text-align:right; font-weight:600; }}

  .scroll {{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; min-width:560px; }}
  th,td {{ padding:9px 11px; text-align:left; border-bottom:1px solid var(--line); }}
  th {{ background:var(--panel2); color:var(--muted); font-weight:600; font-size:11px;
    text-transform:uppercase; letter-spacing:.05em; }}
  tbody tr:hover {{ background:rgba(255,255,255,.02); }}
  td.reason {{ color:var(--muted); max-width:320px; }}

  .badge {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:700; }}
  .badge.buy {{ background:rgba(34,197,94,.15); color:var(--green); }}
  .badge.sell {{ background:rgba(239,68,68,.15); color:var(--red); }}
  .badge.hold {{ background:rgba(148,163,184,.15); color:var(--muted); }}
  .chip {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:600;
    color:var(--c); background:color-mix(in srgb,var(--c) 16%,transparent);
    border:1px solid color-mix(in srgb,var(--c) 35%,transparent); }}
  .mini-chip {{ display:inline-block; padding:1px 6px; border-radius:6px; font-size:10px;
    background:var(--panel2); border:1px solid var(--line); color:var(--muted); margin:1px; }}
  .tag {{ font-size:11px; color:var(--muted); background:var(--panel2); padding:2px 8px; border-radius:6px; }}
  .agree {{ font-weight:700; color:var(--accent); }}

  .ai-head {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;
    border-left:4px solid var(--c); padding-left:12px; margin-top:8px; }}
  .ai-style {{ color:var(--muted); font-size:12.5px; }}
  .stat-row {{ display:grid; gap:10px; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); margin-top:16px; }}
  .stat {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:11px 13px; }}
  .stat span {{ display:block; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.05em; }}
  .stat b {{ font-size:18px; }}

  .rn-grid {{ display:grid; gap:13px; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); }}
  .rn {{ background:var(--panel); border:1px solid var(--line); border-radius:13px; padding:14px; }}
  .rn-head {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:7px; }}
  .verdict {{ font-size:11px; font-weight:700; padding:2px 9px; border-radius:999px;
    background:var(--panel2); border:1px solid var(--line); }}
  .verdict.pos {{ color:var(--green); }} .verdict.warn {{ color:var(--amber); }}
  .rn-thesis {{ margin:6px 0; font-size:12.5px; line-height:1.5; }}
  .rn-risk {{ margin:6px 0 0; font-size:11.5px; color:var(--muted); }}
  .note {{ background:var(--panel2); border:1px solid var(--line); border-radius:12px;
    padding:12px 14px; font-size:12px; color:var(--muted); margin-top:30px; }}
</style></head>
<body><div class="wrap">
  <header>
    <h1><span class="spark">◆</span> BIST AI Arena</h1>
    <span class="sub">5 yapay zeka · BIST30 · 52 haftalık paper trading</span>
    <span style="margin-left:auto">{_health_badge(health)}</span>
    <span class="sub">Güncelleme <b>{now}</b> · oto-yenile 5dk</span>
  </header>

  {_tabbar(comps)}

  <section class="tab" id="tab-summary">
    <div class="banner">
      <b>{active_n} aktif yarışmacı</b> · toplam <b>{total_trades}</b> işlem ·
      XU30 <b>%{xu30:+.2f}</b> · Her AI kendi stratejisiyle otomatik işlem yapar;
      <b style="color:var(--accent)">Konsensüs (Claude)</b> şef katmanı 2+ AI'ın ortak seçtiği hisseleri araştırır.
      <span class="muted">Kartlara/sekmelere tıklayıp detaya bak.</span>
    </div>
    <h3>🏆 Liderlik</h3>
    {_leaderboard(comps, xu30)}
    <h3>⚡ Canlı işlem akışı (tüm AI'lar)</h3>
    {_trade_feed(feed)}
    <h3>🧩 Konsensüs hisseleri — 2+ AI ortak</h3>
    {_consensus_table(consensus)}
  </section>

  {ai_tabs}

  <div class="note">
    <code>orchestrator/run.py</code> her döngüde: deepseek'i kendi LLM motoruyla,
    claude/codex/microsoft'u kendi stratejileriyle ilerletir; konsensüsü hesaplar;
    Konsensüs (Claude) şef portföyünü günceller. Fiyatlar canlı (Yahoo Finance),
    haber sentiment DeepSeek LLM. Yatırım tavsiyesi değildir; gerçek emir gönderilmez.
  </div>
</div>
<script>
  function showTab(key) {{
    document.querySelectorAll('.tab').forEach(function(s) {{ s.hidden = (s.id !== 'tab-'+key); }});
    document.querySelectorAll('.tabbtn').forEach(function(b) {{
      b.classList.toggle('active', b.dataset.tab === key);
    }});
    window.scrollTo({{top:0, behavior:'smooth'}});
  }}
</script>
</body></html>"""
