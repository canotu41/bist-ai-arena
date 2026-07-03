"""DeepSeek BIST30 - HTML Dashboard Oluşturucu"""
from __future__ import annotations

import html
import json
from datetime import datetime
from typing import List, Dict

from .data_models import PortfolioState, CompanySnapshot, Position


def generate_dashboard_html(
    portfolio: PortfolioState,
    snapshots: List[CompanySnapshot],
    leaderboard: Dict,
) -> str:
    """Tam dashboard HTML'i oluşturur"""

    # Portföy özet kartları
    cash_pct = (portfolio.cash / portfolio.total_value * 100) if portfolio.total_value > 0 else 0
    invested_pct = 100 - cash_pct
    return_color = "var(--green)" if portfolio.total_return_pct >= 0 else "var(--red)"

    # DeepScore sıralaması tablosu
    score_rows = []
    for snap in snapshots[:24]:  # Tüm BIST30 hisseleri
        signal_class = {
            "STRONG_BUY": "signal-strong-buy",
            "BUY": "signal-buy",
            "HOLD": "signal-hold",
            "WEAK_HOLD": "signal-weak",
            "SELL": "signal-sell",
            "STRONG_SELL": "signal-strong-sell",
        }.get(snap.signal.value, "signal-hold")
        signal_emoji = {"STRONG_BUY": "🟢", "BUY": "🟢", "HOLD": "🟡", "WEAK_HOLD": "🟠", "SELL": "🔴", "STRONG_SELL": "🔴"}.get(snap.signal.value, "⚪")
        score_width = min(100, snap.deepscore)
        score_color = "var(--green)" if snap.deepscore >= 75 else ("var(--amber)" if snap.deepscore >= 60 else "var(--red)")
        score_rows.append(f"""
        <tr>
          <td class="sym">{html.escape(snap.ticker)}</td>
          <td>{html.escape(snap.company_name)}</td>
          <td><span class="tag">{html.escape(snap.sector)}</span></td>
          <td class="score">{snap.deepscore:.1f}</td>
          <td><div class="bar"><span style="width:{score_width}%;background:{score_color}"></span></div></td>
          <td><span class="{signal_class}">{signal_emoji} {snap.signal.value.replace('_', ' ')}</span></td>
        </tr>""")

    # Skor kırılımı (ilk 5)
    breakdown_bars = []
    for snap in snapshots[:5]:
        bars = "".join(
            f'<div style="margin:2px 0"><span style="font-size:11px;color:var(--muted)">{axis}</span> <div class="bar" style="width:auto;display:inline-block;margin-left:8px"><span style="width:{score}%;background:var(--accent)"></span></div> <span style="font-size:11px">{score:.0f}</span></div>'
            for axis, score in snap.score_breakdown.items()
        )
        breakdown_bars.append(f"""
        <div class="breakdown-item">
          <strong>{html.escape(snap.ticker)}</strong> <span style="color:var(--muted)">DeepScore™ {snap.deepscore:.1f}</span>
          {bars}
        </div>""")

    # Yarışma sıralaması
    race_rows = []
    for comp in leaderboard.get("competitors", []):
        is_ds = comp["name"] == "DeepSeek AI"
        row_class = "racer-ds" if is_ds else ""
        ret_color = "var(--green)" if comp["return"] >= 0 else "var(--red)"
        race_rows.append(f"""
        <div class="racer-card {row_class}">
          <div class="racer-rank">{comp.get('medal', '')} #{comp['rank']}</div>
          <div class="racer-name">{html.escape(comp['name'])}{' 🔥' if is_ds else ''}</div>
          <div class="racer-return" style="color:{ret_color}">%{comp['return']:+.2f}</div>
          <div class="racer-sub">Alfa: %{comp.get('alpha', 0):+.2f} | Portföy: {comp['portfolio_value']:,.0f} TL</div>
        </div>""")

    # Açık pozisyonlar
    position_rows = []
    for pos in portfolio.positions:
        pnl_class = "pos" if pos.unrealized_pnl >= 0 else "neg"
        pnl_emoji = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
        position_rows.append(f"""
        <tr>
          <td class="sym">{html.escape(pos.ticker)}</td>
          <td>{html.escape(pos.company_name)}</td>
          <td><span class="tag">{html.escape(pos.sector)}</span></td>
          <td>{pos.entry_price:.2f}</td>
          <td>{pos.current_price:.2f}</td>
          <td>{pos.quantity}</td>
          <td class="{pnl_class}">{pnl_emoji} %{pos.unrealized_pnl_pct:+.1f}</td>
          <td>{pos.stop_loss:.2f}</td>
          <td>{pos.take_profit:.2f}</td>
        </tr>""")

    # Son işlemler
    tx_rows_html = []
    for tx in portfolio.transactions[-10:]:
        tx_class = "tx-buy" if tx.type == "BUY" else "tx-sell"
        tx_emoji = "🟢 AL" if tx.type == "BUY" else ("🔴 SAT" if tx.type == "SELL" else "🟡 KISMİ")
        tx_rows_html.append(f"""
        <div class="log-entry">
          <span class="log-time">{tx.timestamp}</span>
          <span class="{tx_class}">{tx_emoji}</span> {html.escape(tx.ticker)} x{tx.quantity} @ {tx.price:.2f} TL
          <div style="font-size:12px;color:var(--muted);margin-top:2px">{html.escape(tx.reason[:80])}</div>
        </div>""")

    market_sent = ""
    if portfolio.market_regime:
        regime_emoji = {"BULL": "🐂 BOĞA", "BEAR": "🐻 AYI", "SIDEWAYS": "↔️ YATAY", "HIGH_VOLATILITY": "⚡ VOLATİL"}
        market_sent = f'<span class="badge badge-up">{regime_emoji.get(portfolio.market_regime.value, portfolio.market_regime.value)}</span>'

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepSeek BIST30 — AI Portföy Dashboard</title>
  <style>
    :root {{
      --bg: #0a0e17;
      --card-bg: #111827;
      --panel: #161b22;
      --border: #1e293b;
      --text: #e2e8f0;
      --text-dim: #94a3b8;
      --accent: #d97757;
      --accent2: #60a5fa;
      --green: #3fb950;
      --red: #f85149;
      --amber: #d29922;
      --purple: #a855f7;
      --radius: 14px;
    }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      min-height: 100vh;
    }}
    .wrap {{ max-width: 1320px; margin: 0 auto; padding: 16px; }}

    header {{
      background: linear-gradient(135deg, #1a1f2b 0%, #0f1319 100%);
      border-bottom: 2px solid var(--accent);
      padding: 28px 0 22px;
      margin-bottom: 20px;
    }}
    .brand {{ display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
    .logo {{
      width: 50px; height: 50px; border-radius: 14px;
      background: linear-gradient(135deg, var(--accent), var(--purple));
      color: #fff; font-weight: 800; font-size: 24px;
      display: grid; place-items: center;
    }}
    h1 {{ font-size: 28px; letter-spacing: -.5px; }}
    h1 span {{ background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub {{ color: var(--text-dim); font-size: 14px; margin-top: 4px; }}

    .disclaimer {{
      margin: 16px 0; background: rgba(210,153,34,.08);
      border: 1px solid rgba(210,153,34,.3); color: #e8d9a8;
      padding: 12px 16px; border-radius: 10px; font-size: 13px;
    }}

    section {{ margin-bottom: 28px; }}
    h2 {{ font-size: 18px; margin-bottom: 8px; }}
    h2 .em {{ color: var(--accent); }}

    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(165px,1fr)); gap: 12px; }}
    .card {{
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 16px 18px;
    }}
    .card .k {{ color: var(--text-dim); font-size: 12px; text-transform: uppercase; letter-spacing: .3px; }}
    .card .v {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
    .card .v.small {{ font-size: 18px; }}

    .race-track {{ display: flex; gap: 12px; flex-wrap: wrap; }}
    .racer-card {{
      flex: 1; min-width: 220px; background: var(--card-bg);
      border: 2px solid var(--border); border-radius: var(--radius); padding: 18px;
      position: relative; transition: border-color 0.3s;
    }}
    .racer-card.racer-ds {{ border-color: var(--accent); background: rgba(217,119,87,.05); }}
    .racer-rank {{ position: absolute; top: -12px; right: 14px; font-size: 1.2rem; }}
    .racer-name {{ font-size: 1rem; font-weight: 700; }}
    .racer-return {{ font-size: 2rem; font-weight: 800; }}
    .racer-sub {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}

    .tablewrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; min-width: 600px; }}
    thead th {{
      background: #0f172a; text-align: left; padding: 12px 14px;
      font-size: 12px; text-transform: uppercase; letter-spacing: .3px; color: var(--text-dim);
      border-bottom: 1px solid var(--border); white-space: nowrap;
    }}
    tbody td {{ padding: 12px 14px; border-bottom: 1px solid var(--border); }}
    tbody tr:hover {{ background: rgba(255,255,255,.02); }}
    .sym {{ font-weight: 700; color: var(--accent2); }}
    .tag {{
      display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
      background: #1a2236; border: 1px solid var(--border); color: var(--text-dim);
    }}
    .score {{ font-weight: 700; }}
    .bar {{ height: 6px; border-radius: 4px; background: #1e293b; overflow: hidden; width: 80px; display: inline-block; }}
    .bar > span {{ display: block; height: 100%; border-radius: 4px; background: var(--accent); }}

    .signal-strong-buy {{ color: #22c55e; font-weight: 700; }}
    .signal-buy {{ color: #4ade80; }}
    .signal-hold {{ color: var(--amber); }}
    .signal-weak {{ color: #f97316; }}
    .signal-sell {{ color: var(--red); }}
    .signal-strong-sell {{ color: #ef4444; font-weight: 700; }}

    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    @media (max-width: 800px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}

    .panel {{
      background: var(--panel); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 18px 20px;
    }}
    .panel h3 {{ font-size: 15px; margin-bottom: 10px; }}

    .breakdown-item {{
      padding: 10px; border: 1px solid var(--border); border-radius: 8px;
      margin-bottom: 8px; background: #0f1319;
    }}

    .log-entry {{ padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 13px; }}
    .log-entry:last-child {{ border-bottom: none; }}
    .log-time {{ color: var(--accent2); font-weight: 600; margin-right: 8px; font-size: 12px; }}
    .tx-buy {{ color: var(--green); font-weight: 600; }}
    .tx-sell {{ color: var(--red); font-weight: 600; }}

    .pos {{ color: var(--green); font-weight: 700; }}
    .neg {{ color: var(--red); font-weight: 700; }}

    .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
    .badge-up {{ background: rgba(63,185,80,.15); color: var(--green); }}

    .live-dot {{ display: inline-block; width: 10px; height: 10px; background: var(--green); border-radius: 50%; animation: pulse 1.5s infinite; margin-right: 6px; }}
    @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.3; }} }}

    footer {{ margin-top: 40px; padding: 20px 0; border-top: 1px solid var(--border); color: var(--text-dim); font-size: 12px; text-align: center; }}
    footer a {{ color: var(--accent2); text-decoration: none; }}
  </style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="brand">
      <div class="logo">DS</div>
      <div>
        <h1><span>DeepSeek</span> BIST30 AI Portföy</h1>
        <div class="sub">DeepScore™ 5-Eksenli Kantitatif Model · 52 Hafta Yarışması · Başlangıç: 3 Temmuz 2026</div>
      </div>
      <div style="margin-left:auto;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <span class="badge badge-up"><span class="live-dot"></span>CANLI</span>
        {market_sent}
        <span style="color:var(--text-dim);font-size:12px">Son güncelleme: {now}</span>
      </div>
    </div>
    <div class="disclaimer">
      ⚠️ <strong>Bu bir yatırım tavsiyesi değildir.</strong> Getiri garantisi yoktur. Tüm işlemler 10.000 TL hipotetik sermaye ile <em>kağıt üzerinde</em> yürütülür. DeepSeek AI diğer yapay zeka modelleriyle haftalık yarışma halindedir.
    </div>
  </div>
</header>

<div class="wrap">

  <!-- PORTFÖY ÖZET KARTLARI -->
  <section>
    <div class="cards">
      <div class="card"><div class="k">Başlangıç Sermaye</div><div class="v">{portfolio.initial_capital:,.0f} ₺</div></div>
      <div class="card"><div class="k">Güncel Değer</div><div class="v">{portfolio.total_value:,.2f} ₺</div></div>
      <div class="card"><div class="k">Toplam Getiri</div><div class="v small" style="color:{return_color}">%{portfolio.total_return_pct:+.2f}</div></div>
      <div class="card"><div class="k">Nakit Tampon</div><div class="v small">{portfolio.cash:,.0f} ₺ · %{cash_pct:.0f}</div></div>
      <div class="card"><div class="k">Yatırım Oranı</div><div class="v small">%{invested_pct:.0f}</div></div>
      <div class="card"><div class="k">Hafta</div><div class="v small">{portfolio.week} / 52</div></div>
      <div class="card"><div class="k">Kazanma Oranı</div><div class="v small">%{portfolio.win_rate_pct:.0f}</div></div>
      <div class="card"><div class="k">Maks. Drawdown</div><div class="v small" style="color:var(--red)">%{portfolio.max_drawdown_pct:.2f}</div></div>
    </div>
  </section>

  <!-- 🏆 YARIŞMA SIRALAMASI -->
  <section>
    <h2><span class="em">🏆</span> Haftalık Yarışma — Hafta {leaderboard.get('week', 0)}</h2>
    <p style="color:var(--text-dim);font-size:13px;margin-bottom:12px">XU30 Getirisi: %{leaderboard.get('xu30_return', 0):+.2f} · Tarih: {leaderboard.get('date', now)}</p>
    <div class="race-track">
      {"".join(race_rows)}
    </div>
  </section>

  <!-- 📊 DEEPSCORE™ SIRALAMASI -->
  <section>
    <h2><span class="em">🎯</span> DeepScore™ BIST30 Sıralaması</h2>
    <p style="color:var(--text-dim);font-size:13px;margin-bottom:12px">5 eksenli skorlama: Temel %25 · Teknik %30 · Haber %20 · Momentum %15 · Risk %10 | Piyasa rejimine adaptif ağırlıklar</p>
    <div class="tablewrap">
      <table>
        <thead>
          <tr><th>Hisse</th><th>Şirket</th><th>Sektör</th><th>DeepScore™</th><th>Skor Bar</th><th>Sinyal</th></tr>
        </thead>
        <tbody>
          {"".join(score_rows)}
        </tbody>
      </table>
    </div>
  </section>

  <!-- 🔬 SKOR KIRILIMI -->
  <section>
    <h2><span class="em">🔬</span> Skor Kırılımı — İlk 5 Hisse</h2>
    <div class="grid2">
      {"".join(breakdown_bars)}
    </div>
  </section>

  <!-- 💼 AÇIK POZİSYONLAR -->
  <section>
    <h2><span class="em">💼</span> Açık Pozisyonlar ({len(portfolio.positions)})</h2>
    <div class="tablewrap">
      <table>
        <thead>
          <tr><th>Hisse</th><th>Şirket</th><th>Sektör</th><th>Giriş ₺</th><th>Güncel ₺</th><th>Adet</th><th>PnL</th><th>Stop</th><th>Hedef</th></tr>
        </thead>
        <tbody>
          {"".join(position_rows) if position_rows else '<tr><td colspan="9" style="text-align:center;color:var(--text-dim);padding:30px">Henüz açık pozisyon yok</td></tr>'}
        </tbody>
      </table>
    </div>
  </section>

  <!-- 📋 SON İŞLEMLER -->
  <section>
    <h2><span class="em">📋</span> Son İşlemler</h2>
    <div class="panel" style="max-height:400px;overflow-y:auto;">
      {"".join(tx_rows_html) if tx_rows_html else '<div style="color:var(--text-dim);text-align:center;padding:20px">Henüz işlem yapılmadı</div>'}
    </div>
  </section>

  <footer>
    <p>DeepSeek AI · BIST30 Kağıt Portföy · DeepScore™ Kantitatif Model</p>
    <p style="margin-top:6px">Strateji: <a href="STRATEJI.md">STRATEJI.md</a> · Portföy: <a href="portfolio.json">portfolio.json</a> · Log: <a href="log/">log/</a></p>
    <p style="margin-top:6px;color:var(--accent);font-weight:600">DeepSeek — Veriyle kazanır. 🔥</p>
  </footer>

</div>
</body>
</html>"""


def generate_simple_html(portfolio: PortfolioState) -> str:
    """Portföy yoksa basit bir HTML oluşturur"""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepSeek BIST30 — Portföy</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #0a0e17; color: #e2e8f0; padding: 40px; }}
    h1 {{ color: #d97757; }}
    .card {{ background: #111827; padding: 20px; border-radius: 12px; margin: 16px 0; }}
  </style>
</head>
<body>
  <h1>DeepSeek BIST30 AI Portföy</h1>
  <div class="card">
    <p>Portföy henüz oluşturulmadı.</p>
    <p>Başlatmak için: <code>python main.py init</code></p>
    <p>Dashboard oluşturmak için: <code>python main.py dashboard</code></p>
  </div>
</body>
</html>"""