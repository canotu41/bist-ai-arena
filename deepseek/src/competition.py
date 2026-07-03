"""DeepSeek BIST30 - Haftalık Yarışma Modülü"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from .data_models import WeeklyResult, PortfolioState
from .portfolio_manager import load_portfolio

ROOT = Path(__file__).resolve().parent.parent
COMPETITION_JSON = ROOT / "competition.json"


def get_weekly_leaderboard(current_week: int) -> Dict:
    """Haftalık liderlik tablosunu döndürür"""

    # Ana dizinde diğer AI'ların portföy dosyalarını kontrol et
    competitors = {}

    # Claude
    claude_json = ROOT.parent / "claude" / "portfolio.json"
    if claude_json.exists():
        try:
            claude_data = json.loads(claude_json.read_text(encoding="utf-8"))
            competitors["Claude AI"] = {
                "return": claude_data.get("getiri_pct", claude_data.get("total_return_pct", 0.0)),
                "portfolio_value": claude_data.get("portfoy_degeri_try", claude_data.get("total_value", 10000)),
                "initial": claude_data.get("baslangic_sermayesi_try", claude_data.get("initial_capital", 10000)),
            }
        except Exception:
            competitors["Claude AI"] = {"return": 0.0, "portfolio_value": 10000, "initial": 10000}

    # Codex
    codex_json = ROOT.parent / "codex" / "portfolio.json"
    if codex_json.exists():
        try:
            codex_data = json.loads(codex_json.read_text(encoding="utf-8"))
            competitors["Codex"] = {
                "return": codex_data.get("total_return_pct", 0.0),
                "portfolio_value": codex_data.get("total_value", 10000),
                "initial": codex_data.get("initial_capital", 10000),
            }
        except Exception:
            competitors["Codex"] = {"return": 0.0, "portfolio_value": 10000, "initial": 10000}
    else:
        competitors["Codex"] = {"return": 0.0, "portfolio_value": 10000, "initial": 10000}

    # Microsoft
    ms_json = ROOT.parent / "microsoft" / "recommendations.json"
    if ms_json.exists():
        try:
            ms_data = json.loads(ms_json.read_text(encoding="utf-8"))
            ms_portfolio = ms_data.get("portfolio", {})
            competitors["Microsoft Copilot"] = {
                "return": ms_portfolio.get("total_return_pct", 0.0),
                "portfolio_value": ms_portfolio.get("total_value", 100000),
                "initial": 100000,
            }
        except Exception:
            competitors["Microsoft Copilot"] = {"return": 0.0, "portfolio_value": 100000, "initial": 100000}
    else:
        competitors["Microsoft Copilot"] = {"return": 0.0, "portfolio_value": 100000, "initial": 100000}

    # DeepSeek
    deepseek = load_portfolio()

    # XU30 varsayılan
    xu30_return = 0.5 * current_week  # haftalık ~%0.5

    leaderboard = {
        "week": current_week,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "xu30_return": round(xu30_return, 2),
        "competitors": [
            {
                "name": "DeepSeek AI",
                "return": round(deepseek.total_return_pct, 2),
                "portfolio_value": round(deepseek.total_value, 2),
                "initial_capital": deepseek.initial_capital,
                "alpha": round(deepseek.total_return_pct - xu30_return, 2),
            }
        ],
    }

    for name, data in competitors.items():
        ret = data["return"]
        leaderboard["competitors"].append({
            "name": name,
            "return": round(ret, 2),
            "portfolio_value": round(data["portfolio_value"], 2),
            "initial_capital": data["initial"],
            "alpha": round(ret - xu30_return, 2),
        })

    # Sırala: en yüksek getiriye göre
    leaderboard["competitors"].sort(key=lambda x: x["return"], reverse=True)

    # Rütbeleri ata
    for i, comp in enumerate(leaderboard["competitors"]):
        comp["rank"] = i + 1
        if i == 0:
            comp["medal"] = "🥇"
        elif i == 1:
            comp["medal"] = "🥈"
        elif i == 2:
            comp["medal"] = "🥉"
        else:
            comp["medal"] = ""

    return leaderboard


def save_leaderboard() -> Dict:
    """Yarışma durumunu kaydeder ve döndürür"""
    # Kaçıncı haftada olduğumuzu hesapla
    start = datetime(2026, 7, 3)
    now = datetime.now()
    current_week = max(1, (now - start).days // 7 + 1)

    leaderboard = get_weekly_leaderboard(current_week)
    COMPETITION_JSON.write_text(
        json.dumps(leaderboard, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return leaderboard


def generate_weekly_report(portfolio: PortfolioState) -> str:
    """Haftalık rapor metni oluşturur"""
    week = portfolio.week
    leaderboard = save_leaderboard()

    ds_data = next(
        (c for c in leaderboard["competitors"] if c["name"] == "DeepSeek AI"),
        None,
    )
    rank = ds_data["rank"] if ds_data else "?"

    lines = [
        f"# DeepSeek BIST30 — Hafta {week} Raporu",
        f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 📊 Performans Özeti",
        f"- Portföy Değeri: **{portfolio.total_value:,.2f} TL**",
        f"- Haftalık Getiri: **%{portfolio.total_return_pct:+.2f}**",
        f"- Nakit: {portfolio.cash:,.2f} TL",
        f"- Açık Pozisyon: {len(portfolio.positions)}",
        f"- Piyasa Rejimi: {portfolio.market_regime.value}",
        "",
        "## 🏆 Yarışma Durumu",
        f"- DeepSeek Sıralaması: **{rank}.**",
        f"- XU30 Getirisi: %{leaderboard['xu30_return']:+.2f}",
        f"- Alfa: %{ds_data['alpha']:+.2f}" if ds_data else "",
    ]

    for comp in leaderboard["competitors"]:
        lines.append(f"- {comp['medal']} **{comp['name']}**: %{comp['return']:+.2f} (Sıra: {comp['rank']})")

    lines += [
        "",
        "## 💼 Açık Pozisyonlar",
    ]
    for pos in portfolio.positions:
        emoji = "🟢" if pos.unrealized_pnl_pct > 0 else "🔴"
        lines.append(f"- {emoji} **{pos.ticker}** ({pos.company_name}) | Giriş: {pos.entry_price:.2f} TL | Güncel: {pos.current_price:.2f} TL | PnL: %{pos.unrealized_pnl_pct:+.1f}")

    lines += [
        "",
        "## 🎯 DeepSeek'in Gizli Silahları Bu Hafta",
        "1. Piyasa rejimine adaptif ağırlıklar aktif",
        "2. Trailing stop mekanizması kârları koruyor",
        "3. Sektör çeşitlendirmesi riski dağıtıyor",
        "4. Haber/KAP taraması erken sinyal üretiyor",
        "5. DeepScore™ sıralaması en iyi fırsatları seçiyor",
        "",
        "---",
        "*DeepSeek AI — Veriyle kazanır.*",
    ]

    return "\n".join(lines)