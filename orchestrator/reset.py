#!/usr/bin/env python3
"""Yarışma öncesi SIFIRLAMA.

Tüm portföyleri boş 50.000 TL'ye çeker ve dashboard'u TİCARET YAPMADAN yeniden
üretir. Alımlar Pazartesi ilk Actions döngüsünde, her AI kendi taramasına göre olur.

Kullanım:  python3 orchestrator/reset.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT = ORCH_DIR.parent
DATA_DIR = ORCH_DIR / "data"

sys.path.insert(0, str(ROOT))
from orchestrator import common, consensus as consensus_mod, research, dashboard, trader, run  # noqa: E402
from orchestrator.strategies import STRATEGIES  # noqa: E402


def main() -> None:
    print("🧹 Yarışma sıfırlaması — tüm portföyler boş 50.000 TL'ye çekiliyor...")

    # 1) State dosyalarını sil (cache'ler KORUNUR: canlı veri kaybolmasın)
    for p in [ROOT / "claude" / "portfolio.json", ROOT / "codex" / "portfolio.json",
              ROOT / "microsoft" / "portfolio.json", ROOT / "deepseek" / "portfolio.json",
              ROOT / "deepseek" / "competition.json",
              DATA_DIR / "consensus_portfolio.json", DATA_DIR / "last_run.json",
              DATA_DIR / "benchmark.json", DATA_DIR / "notify_state.json"]:
        if p.exists():
            p.unlink()

    # 2) Boş 50k portföyler oluştur
    for strat in STRATEGIES.values():
        pf = trader._load(strat)          # dosya yok -> initial=50000, boş
        trader._save(strat, pf)
        print(f"   ✓ {strat['name']:18} {pf['cash']:,.0f} TL nakit, 0 pozisyon")

    cpf = research._load_portfolio()      # consensus boş 50k
    research._save_portfolio(cpf)
    print(f"   ✓ {'Konsensüs (Claude)':18} {cpf['cash']:,.0f} TL nakit, 0 pozisyon")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    deepseek_empty = {
        "name": "DeepSeek BIST30 Portföy", "initial_capital": 50000.0, "cash": 50000.0,
        "positions": [], "transactions": [], "total_value": 50000.0,
        "total_return_pct": 0.0, "benchmark_return_pct": 0.0, "alpha_pct": 0.0,
        "week": 0, "current_drawdown_pct": 0.0, "max_drawdown_pct": 0.0,
        "win_rate_pct": 0.0, "market_regime": "SIDEWAYS",
        "last_updated": now, "created_date": "2026-07-06",
    }
    (ROOT / "deepseek" / "portfolio.json").write_text(
        json.dumps(deepseek_empty, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   ✓ {'DeepSeek AI':18} 50,000 TL nakit, 0 pozisyon")

    # 3) Dashboard'u TİCARET YAPMADAN üret
    snapshot = common.load_snapshot()
    health = run.data_health(snapshot)
    comps = common.load_all_competitors()
    base = [c for c in comps if c["key"] != "consensus"]
    consensus = consensus_mod.compute_consensus(base, snapshot)   # boş
    notes = research.generate_research(consensus)                 # boş
    feed = common.merged_trade_feed(comps, 50)                    # boş
    try:
        backtest = json.loads((DATA_DIR / "backtest_results.json").read_text(encoding="utf-8"))
    except Exception:
        backtest = None
    xu30 = run.get_xu30()  # benchmark başlangıcını (XU100) kurar, 0 döner
    html = dashboard.build_dashboard(comps, feed, consensus, notes, cpf, xu30,
                                     health=health, backtest=backtest)
    (ROOT / "dashboard.html").write_text(html, encoding="utf-8")
    (ROOT / "index.html").write_text(html, encoding="utf-8")

    (DATA_DIR / "last_run.json").write_text(json.dumps({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "RESET — yarışma Pazartesi başlıyor",
        "health": health,
        "active_competitors": sum(1 for c in comps if c.get("active")),
        "budget_per_ai": 50000,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✓ Sıfırlandı. Dashboard başlangıç çizgisinde. Alımlar Pazartesi Actions ile.")


if __name__ == "__main__":
    main()
