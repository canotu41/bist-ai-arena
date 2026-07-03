"""Tüm yapay zekaları, canlı işlem akışını, konsensüs araştırmasını ve
Konsensüs portföyünü tek bir self-contained HTML dashboard'da toplar."""
from __future__ import annotations

import html
from datetime import datetime
from typing import Dict, List

AI_COLORS = {
    "consensus": "#a855f7", "deepseek": "#38bdf8", "claude": "#f59e0b",
    "microsoft": "#34d399", "codex": "#94a3b8",
}
MEDALS = ["🥇", "🥈", "🥉", "", ""]


def _esc(x) -> str:
    return html.escape(str(x))


def _side_badge(side: str) -> str:
    s = str(side).upper()
    if s.startswith("BUY") or s == "ALIS":
        cls, txt = "buy", "AL"
    elif "SELL" in s or s == "SATIS":
        cls, txt = "sell", ("SAT (½)" if "PARTIAL" in s else "SAT")
    else:
        cls, txt = "hold", _esc(side)
    return f'<span class="badge {cls}">{txt}</span>'


def _chip(name: str, key: str) -> str:
    color = AI_COLORS.get(key, "#64748b")
    return f'<span class="chip" style="--c:{color}">{_esc(name)}</span>'


def _leaderboard(comps: List[dict], xu30: float) -> str:
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
        <div class="lb-card" style="--c:{color}">
          <div class="lb-top"><span class="lb-medal">{medal}</span>
            <span class="lb-name">{_esc(c['name'])}</span>
            <span class="lb-rank">#{i+1}</span></div>
          <div class="lb-ret {rc}">%{c['return_pct']:+.2f}</div>
          <div class="lb-meta">
            <span>Değer: <b>{c['value']:,.0f} TL</b></span>
            <span>Alfa: <b class="{ac}">%{alpha:+.2f}</b></span>
          </div>
          <div class="lb-meta"><span>Nakit: {c['cash']:,.0f} TL</span>
            <span>Pozisyon: {len(c['positions'])}</span></div>
        </div>""")
    inactive = [c for c in comps if not c.get("active")]
    if inactive:
        names = ", ".join(_esc(c["name"]) for c in inactive)
        cards.append(f'<div class="lb-card inactive"><div class="lb-name">{names}</div>'
                     f'<div class="muted">Henüz portföy üretmedi</div></div>')
    return '<div class="lb-grid">' + "".join(cards) + "</div>"


def _trade_feed(feed: List[dict]) -> str:
    if not feed:
        return '<p class="muted">Henüz işlem yok.</p>'
    rows = []
    for t in feed:
        ts = _esc(t.get("ts") or "—")
        qty = t.get("qty", "")
        price = t.get("price", "")
        price_s = f"{price:.2f}" if isinstance(price, (int, float)) and price else _esc(price or "—")
        rows.append(f"""
        <tr>
          <td class="mono nowrap">{ts}</td>
          <td>{_chip(t.get('who',''), t.get('who_key',''))}</td>
          <td>{_side_badge(t.get('side',''))}</td>
          <td class="mono"><b>{_esc(t.get('ticker','—'))}</b></td>
          <td class="mono num">{_esc(qty)}</td>
          <td class="mono num">{price_s}</td>
          <td class="reason">{_esc(t.get('reason',''))}</td>
        </tr>""")
    return f"""<div class="scroll"><table class="feed">
      <thead><tr><th>Zaman</th><th>AI</th><th>İşlem</th><th>Hisse</th>
        <th class="num">Adet</th><th class="num">Fiyat</th><th>Gerekçe</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>"""


def _portfolio_cards(comps: List[dict]) -> str:
    cards = []
    for c in comps:
        if not c.get("active") or not c["positions"]:
            continue
        color = AI_COLORS.get(c["key"], "#64748b")
        rows = []
        for p in sorted(c["positions"], key=lambda x: x["weight_pct"], reverse=True):
            pc = "pos" if p["pnl_pct"] >= 0 else "neg"
            rows.append(f"""<tr><td class="mono"><b>{_esc(p['ticker'])}</b></td>
              <td class="num mono">{p['qty']:g}</td>
              <td class="num mono">{p['entry']:.2f}</td>
              <td class="num mono">{p['current']:.2f}</td>
              <td class="num mono {pc}">%{p['pnl_pct']:+.1f}</td>
              <td class="num mono">%{p['weight_pct']:.0f}</td></tr>""")
        cards.append(f"""
        <div class="pf-card" style="--c:{color}">
          <div class="pf-head"><span class="dot"></span><b>{_esc(c['name'])}</b>
            <span class="muted">%{c['return_pct']:+.2f}</span></div>
          <div class="scroll"><table class="mini">
            <thead><tr><th>Hisse</th><th class="num">Adet</th><th class="num">Giriş</th>
              <th class="num">Güncel</th><th class="num">K/Z</th><th class="num">Ağ.</th></tr></thead>
            <tbody>{''.join(rows)}</tbody></table></div>
        </div>""")
    return '<div class="pf-grid">' + "".join(cards) + "</div>"


def _consensus_table(consensus: List[dict]) -> str:
    if not consensus:
        return '<p class="muted">Henüz 2+ AI\'ın ortak seçtiği hisse yok.</p>'
    rows = []
    for c in consensus:
        chips = " ".join(f'<span class="mini-chip">{_esc(b["ai"].split()[0])}</span>'
                         for b in c["backers"])
        sc = "pos" if c["deepscore"] >= 65 else ("warn" if c["deepscore"] >= 50 else "neg")
        rows.append(f"""<tr>
          <td class="mono"><b>{_esc(c['ticker'])}</b></td>
          <td>{_esc(c['name'])}</td>
          <td><span class="tag">{_esc(c['sector'])}</span></td>
          <td class="num"><span class="agree">×{c['agreement']}</span></td>
          <td>{chips}</td>
          <td class="num mono {sc}">{c['deepscore']:.1f}</td>
          <td class="num mono">{c['rsi']:.0f}</td>
        </tr>""")
    return f"""<div class="scroll"><table>
      <thead><tr><th>Hisse</th><th>Şirket</th><th>Sektör</th><th class="num">Ortaklık</th>
        <th>AI'lar</th><th class="num">DeepScore</th><th class="num">RSI</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table></div>"""


def _research_panel(notes: List[dict]) -> str:
    if not notes:
        return '<p class="muted">Araştırma için yeterli konsensüs yok.</p>'
    cards = []
    for n in notes:
        v = n["verdict"]
        vc = "pos" if "AL" in v and "İZLE" not in v else "warn"
        cards.append(f"""
        <div class="rn">
          <div class="rn-head"><b class="mono">{_esc(n['ticker'])}</b>
            <span class="muted">{_esc(n['name'])}</span>
            <span class="verdict {vc}">{_esc(v)}</span>
            <span class="agree">×{n['agreement']}</span></div>
          <p class="rn-thesis">{_esc(n['thesis'])}</p>
          <p class="rn-risk">⚠ {_esc(n['risk'])}</p>
        </div>""")
    return '<div class="rn-grid">' + "".join(cards) + "</div>"


def build_dashboard(comps, feed, consensus, notes, consensus_pf, xu30, extra=None) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    active_n = sum(1 for c in comps if c.get("active"))
    total_trades = sum(len(c.get("trades", [])) for c in comps)
    extra = extra or {}

    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>BIST AI Arena — Birleşik Dashboard</title>
<style>
  :root {{
    --bg:#0b1120; --panel:#111a2e; --panel2:#0f1728; --line:#1e2b45;
    --ink:#e6edf7; --muted:#8798b5; --green:#22c55e; --red:#ef4444;
    --amber:#f59e0b; --accent:#a855f7;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
  a {{ color:inherit; }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:20px 16px 60px; }}
  header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:12px;
    border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:22px; }}
  h1 {{ font-size:22px; margin:0; letter-spacing:.2px; }}
  h1 .spark {{ color:var(--accent); }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .sub b {{ color:var(--ink); }}
  section {{ margin:30px 0; }}
  h2 {{ font-size:15px; text-transform:uppercase; letter-spacing:.12em;
    color:var(--muted); margin:0 0 14px; font-weight:600; }}
  .muted {{ color:var(--muted); }} .num {{ text-align:right; }}
  .nowrap {{ white-space:nowrap; }} .pos {{ color:var(--green); }}
  .neg {{ color:var(--red); }} .warn {{ color:var(--amber); }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}

  .lb-grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); }}
  .lb-card {{ background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--c);
    border-radius:14px; padding:16px; }}
  .lb-card.inactive {{ opacity:.5; border-left-color:var(--line); }}
  .lb-top {{ display:flex; align-items:center; gap:8px; font-size:14px; }}
  .lb-medal {{ font-size:18px; }} .lb-name {{ font-weight:600; }}
  .lb-rank {{ margin-left:auto; color:var(--muted); font-size:12px; }}
  .lb-ret {{ font-size:30px; font-weight:700; margin:8px 0 6px; letter-spacing:-.5px; }}
  .lb-meta {{ display:flex; justify-content:space-between; font-size:12.5px;
    color:var(--muted); margin-top:4px; }}

  .scroll {{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; min-width:520px; }}
  th,td {{ padding:9px 12px; text-align:left; border-bottom:1px solid var(--line); }}
  th {{ background:var(--panel2); color:var(--muted); font-weight:600;
    font-size:11.5px; text-transform:uppercase; letter-spacing:.06em; position:sticky; top:0; }}
  tbody tr:hover {{ background:rgba(255,255,255,.02); }}
  td.reason {{ color:var(--muted); max-width:340px; }}
  .feed td {{ vertical-align:middle; }}

  .badge {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:700; }}
  .badge.buy {{ background:rgba(34,197,94,.15); color:var(--green); }}
  .badge.sell {{ background:rgba(239,68,68,.15); color:var(--red); }}
  .badge.hold {{ background:rgba(148,163,184,.15); color:var(--muted); }}
  .chip {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:11.5px;
    font-weight:600; color:var(--c); background:color-mix(in srgb,var(--c) 16%,transparent);
    border:1px solid color-mix(in srgb,var(--c) 35%,transparent); }}
  .mini-chip {{ display:inline-block; padding:1px 6px; border-radius:6px; font-size:10.5px;
    background:var(--panel2); border:1px solid var(--line); color:var(--muted); margin:1px; }}
  .tag {{ font-size:11px; color:var(--muted); background:var(--panel2);
    padding:2px 8px; border-radius:6px; }}
  .agree {{ font-weight:700; color:var(--accent); }}

  .pf-grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); }}
  .pf-card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px; }}
  .pf-head {{ display:flex; align-items:center; gap:8px; margin-bottom:10px; font-size:14px; }}
  .pf-head .dot {{ width:9px; height:9px; border-radius:50%; background:var(--c); }}
  .pf-head .muted {{ margin-left:auto; }}
  table.mini {{ min-width:0; }} table.mini th,table.mini td {{ padding:6px 8px; }}

  .rn-grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }}
  .rn {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:15px; }}
  .rn-head {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:8px; }}
  .verdict {{ font-size:11px; font-weight:700; padding:2px 9px; border-radius:999px;
    background:var(--panel2); border:1px solid var(--line); }}
  .verdict.pos {{ color:var(--green); }} .verdict.warn {{ color:var(--amber); }}
  .rn-thesis {{ margin:6px 0; font-size:13px; line-height:1.55; }}
  .rn-risk {{ margin:6px 0 0; font-size:12px; color:var(--muted); }}
  .note {{ background:var(--panel2); border:1px solid var(--line); border-radius:12px;
    padding:12px 14px; font-size:12.5px; color:var(--muted); }}
  .banner {{ background:color-mix(in srgb,var(--accent) 12%,transparent);
    border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);
    border-radius:12px; padding:12px 14px; font-size:13px; margin-bottom:8px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1><span class="spark">◆</span> BIST AI Arena</h1>
    <span class="sub">5 yapay zeka · BIST30 · 52 haftalık paper trading yarışı</span>
    <span class="sub" style="margin-left:auto">Güncelleme: <b>{now}</b> · her 5 dk oto-yenile</span>
  </header>

  <div class="banner">
    <b>{active_n} aktif yarışmacı</b> · toplam <b>{total_trades}</b> işlem ·
    XU30 varsayılan getiri: <b>%{xu30:+.2f}</b> ·
    5. oyuncu <b style="color:var(--accent)">Konsensüs (Claude)</b>: 2+ AI'ın ortak seçtiği hisselerden kurulur.
    <span class="muted">Fiyatlar şu an simüle veri; gerçek BIST/DeepSeek akışı bağlanınca canlanır.</span>
  </div>

  <section>
    <h2>🏆 Liderlik Tablosu</h2>
    {_leaderboard(comps, xu30)}
  </section>

  <section>
    <h2>⚡ Canlı İşlem Akışı</h2>
    {_trade_feed(feed)}
  </section>

  <section>
    <h2>🧩 Konsensüs Hisseleri — 2+ AI'ın Ortak Kararı</h2>
    {_consensus_table(consensus)}
  </section>

  <section>
    <h2>🔬 Claude Araştırma Paneli</h2>
    {_research_panel(notes)}
  </section>

  <section>
    <h2>💼 Yarışmacı Portföyleri</h2>
    {_portfolio_cards(comps)}
  </section>

  <section>
    <div class="note">
      Bu dashboard <code>orchestrator/run.py</code> tarafından üretilir. Her döngüde
      deepseek ve microsoft motorları ilerletilir, tüm portföyler birleştirilir,
      konsensüs hesaplanır ve Konsensüs (Claude) portföyü güncellenir.
      Yatırım tavsiyesi değildir; gerçek emir gönderilmez.
    </div>
  </section>
</div>
</body>
</html>"""
