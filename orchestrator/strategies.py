"""Her klasör-AI'ın KENDİ strateji kimliği (kendi STRATEJI.md'sinden türetildi).

Hepsi aynı canlı-veriden gelen bileşen skorlarını (Temel/Teknik/Haber/Momentum/Risk)
KENDİ ağırlıkları, eşikleri ve risk kurallarıyla birleştirir → farklı portföyler.
deepseek burada YOK; o kendi LLM'li motorunda (deepseek/main.py) kalır."""
from __future__ import annotations

# axis'ler snapshot breakdown ile birebir: Temel, Teknik, Haber, Momentum, Risk
STRATEGIES = {
    "claude": {
        "key": "claude", "name": "Claude AI", "folder": "claude",
        "initial": 10000.0,
        "style": "Temel ağırlıklı, disiplinli swing (%40 temel / %35 teknik / %25 haber)",
        "weights": {"Temel": 0.40, "Teknik": 0.35, "Haber": 0.25, "Momentum": 0.0, "Risk": 0.0},
        "buy_threshold": 63.0, "sell_threshold": 46.0,
        "max_single_pct": 0.20, "min_cash_pct": 0.10, "max_sector_pct": 0.40,
        "max_positions": 8, "stop_pct": -0.09, "target_pct": 0.18,
    },
    "codex": {
        "key": "codex", "name": "Codex", "folder": "codex",
        "initial": 10000.0,
        "style": "Önce risk, sonra kalite, sonra momentum (%35 temel / %30 teknik / %20 haber / %15 risk)",
        "weights": {"Temel": 0.35, "Teknik": 0.30, "Haber": 0.20, "Momentum": 0.0, "Risk": 0.15},
        "buy_threshold": 67.0, "sell_threshold": 48.0,
        "max_single_pct": 0.15, "min_cash_pct": 0.10, "max_sector_pct": 0.30,
        "max_positions": 8, "stop_pct": -0.07, "target_pct": 0.15,
    },
    "microsoft": {
        "key": "microsoft", "name": "Microsoft Copilot", "folder": "microsoft",
        "initial": 10000.0,
        "style": "Teknik/momentum ağırlıklı (%50 teknik / %35 temel / %15 haber)",
        "weights": {"Temel": 0.35, "Teknik": 0.35, "Haber": 0.15, "Momentum": 0.15, "Risk": 0.0},
        "buy_threshold": 61.0, "sell_threshold": 45.0,
        "max_single_pct": 0.25, "min_cash_pct": 0.05, "max_sector_pct": 0.45,
        "max_positions": 6, "stop_pct": -0.10, "target_pct": 0.20,
    },
}


def score_for(strategy: dict, breakdown: dict) -> float:
    """Bir hissenin bu stratejiye göre skoru (0-100)."""
    w = strategy["weights"]
    total_w = sum(w.values()) or 1.0
    s = sum(breakdown.get(axis, 50.0) * weight for axis, weight in w.items())
    return round(s / total_w, 1)
