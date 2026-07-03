from __future__ import annotations

import html
import json
from pathlib import Path
from typing import List

from src.portfolio import Portfolio, apply_weekly_update, build_initial_portfolio
from src.strategy import Recommendation, make_recommendations


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_HTML = ROOT / "recommendations.html"
OUTPUT_JSON = ROOT / "recommendations.json"


def build_html(recommendations: List[Recommendation], portfolio: Portfolio) -> str:
    rows = []
    for item in recommendations:
        reasons = "<br>".join(f"• {html.escape(reason)}" for reason in item.reasons)
        rows.append(
            f"""
            <tr>
                <td>{html.escape(item.ticker)}</td>
                <td>{html.escape(item.company)}</td>
                <td>{html.escape(item.sector)}</td>
                <td>{item.score:.1f}</td>
                <td>{html.escape(item.label)}</td>
                <td>{reasons}</td>
            </tr>
            """
        )

    position_rows = []
    for position in portfolio.positions:
        current_price = position.current_price or position.entry_price
        pnl = (current_price - position.entry_price) * position.quantity
        position_rows.append(
            f"""
            <tr>
                <td>{html.escape(position.ticker)}</td>
                <td>{html.escape(position.company)}</td>
                <td>{position.quantity}</td>
                <td>{position.entry_price:.2f}</td>
                <td>{current_price:.2f}</td>
                <td>{pnl:.2f}</td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang=\"tr\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>BIST AI Önerileri</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #0f172a; color: #e2e8f0; }}
    h1, h2 {{ color: #f8fafc; }}
    .card {{ background: #111827; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #334155; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #1f2937; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 999px; font-weight: bold; }}
    .al {{ background: #166534; color: #dcfce7; }}
    .bekle {{ background: #92400e; color: #fef3c7; }}
    .sat {{ background: #991b1b; color: #fee2e2; }}
  </style>
</head>
<body>
  <h1>BIST AI Strateji Raporu</h1>
  <div class=\"card\">
    <p>Bu sayfa, local ortamda çalıştırılan ilk strateji motorunun öneri çıktısını göstermektedir.</p>
    <p>Proje amacı: haber, teknik ve temel verileri birleştirerek haftalık bir öneri listesi üretmek.</p>
  </div>
  <div class=\"card\">
    <h2>Hafta 1 alım kararı</h2>
    <p>Bu hafta seçilen hisseler ve toplam portföy değeri aşağıda görünür.</p>
    <p><strong>Hafta:</strong> {portfolio.week} | <strong>Başlangıç nakit:</strong> {portfolio.initial_cash:.2f} | <strong>Toplam değer:</strong> {portfolio.total_value:.2f}</p>
    <table>
      <thead>
        <tr>
          <th>Hisse</th>
          <th>Şirket</th>
          <th>Miktar</th>
          <th>Giriş Fiyatı</th>
          <th>Güncel Fiyat</th>
          <th>Kâr/Zarar</th>
        </tr>
      </thead>
      <tbody>
        {''.join(position_rows)}
      </tbody>
    </table>
  </div>
  <div class=\"card\">
    <h2>Öneri tablosu</h2>
    <table>
      <thead>
        <tr>
          <th>Hisse</th>
          <th>Şirket</th>
          <th>Sektör</th>
          <th>Skor</th>
          <th>Durum</th>
          <th>Gerekçe</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""


def main() -> None:
    recommendations = make_recommendations()
    portfolio = build_initial_portfolio(recommendations, initial_cash=100000.0, max_positions=3)
    portfolio = apply_weekly_update(portfolio)
    OUTPUT_HTML.write_text(build_html(recommendations, portfolio), encoding="utf-8")
    OUTPUT_JSON.write_text(json.dumps({"recommendations": [item.__dict__ for item in recommendations], "portfolio": {"week": portfolio.week, "total_value": portfolio.total_value, "positions": [position.__dict__ for position in portfolio.positions]}}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rapor oluşturuldu: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
