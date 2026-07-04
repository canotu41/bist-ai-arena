#!/usr/bin/env python3
"""BIST AI Arena — Orchestrator (şef).

Bir döngü:
  1. deepseek'i kendi LLM'li motoruyla ilerlet (izole subprocess)
  2. canlı analiz anlık görüntüsünü (bileşen skorları) JSON'a dök
  3. claude / codex / microsoft'u KENDİ stratejileriyle ilerlet (trader.py)
  4. konsensüs (2+ AI ortak) hisseleri hesapla
  5. Konsensüs (Claude) — şef portföyünü kur/güncelle
  6. araştırma notları üret
  7. sekmeli birleşik dashboard.html + index.html üret + heartbeat

Kullanım:  python3 orchestrator/run.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT = ORCH_DIR.parent
DATA_DIR = ORCH_DIR / "data"
DASHBOARD_HTML = ROOT / "dashboard.html"

sys.path.insert(0, str(ROOT))
from orchestrator import (  # noqa: E402
    common, consensus as consensus_mod, research, dashboard, trader,
)
from orchestrator.strategies import STRATEGIES  # noqa: E402


def _run(cmd, cwd, pythonpath=None, label=""):
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = str(pythonpath)
    try:
        r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True,
                           text=True, timeout=180)
        ok = r.returncode == 0
        print(f"  {'✓' if ok else '✗'} {label}"
              + ("" if ok else f"  ({(r.stderr or '').strip().splitlines()[-1:]})"))
        return ok
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        return False


def advance_deepseek() -> None:
    print("→ deepseek (kendi LLM motoru) ilerletiliyor...")
    _run([sys.executable, "main.py", "cycle"], ROOT / "deepseek", label="deepseek cycle")


def dump_snapshot() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / "snapshot.json"
    ok = _run([sys.executable, str(ORCH_DIR / "_snapshot_dump.py"), str(out)],
              ROOT / "deepseek", pythonpath=ROOT / "deepseek", label="canlı snapshot")
    if not ok and not out.exists():
        out.write_text("[]", encoding="utf-8")


def data_health(snapshot: dict) -> dict:
    """Veri tazeliği: canlı fiyat oranı + haber kaynağı."""
    import time
    total = len(snapshot)
    priced = sum(1 for s in snapshot.values() if s.get("price"))
    live = 0
    try:
        lc = json.loads((ROOT / "deepseek" / "data" / "live_cache.json").read_text(encoding="utf-8"))
        live = sum(1 for v in lc.values()
                   if isinstance(v, dict) and v.get("_source") == "live"
                   and time.time() - v.get("_ts", 0) < 86400)
    except Exception:
        pass
    news_llm = False
    try:
        nc = json.loads((ROOT / "deepseek" / "data" / "news_cache.json").read_text(encoding="utf-8"))
        news_llm = nc.get("_source") == "deepseek-llm" and time.time() - nc.get("_ts", 0) < 6 * 3600
    except Exception:
        pass
    ok = priced > 0 and live >= max(1, total // 2)
    return {"ok": ok, "live": live, "total": total, "priced": priced, "news_llm": news_llm}


def get_xu30() -> float:
    try:
        comp = json.loads((ROOT / "deepseek" / "competition.json").read_text(encoding="utf-8"))
        return float(comp.get("xu30_return", 0.5))
    except Exception:
        return 0.5


def main() -> None:
    print(f"=== BIST AI Arena döngüsü — {datetime.now():%Y-%m-%d %H:%M} ===")
    advance_deepseek()
    dump_snapshot()

    snapshot = common.load_snapshot()
    xu30 = get_xu30()
    health = data_health(snapshot)
    print(f"→ Veri sağlığı: {'CANLI' if health['ok'] else '⚠ DEGRADE'} "
          f"(canlı {health['live']}/{health['total']}, haber={'LLM' if health['news_llm'] else 'havuz'})")

    # 3) claude / codex / microsoft — her biri kendi stratejisiyle
    print("→ claude / codex / microsoft kendi stratejileriyle ilerletiliyor...")
    for key, strat in STRATEGIES.items():
        pf = trader.run_strategy(strat, snapshot)
        print(f"  ✓ {strat['name']:18} {pf['total_value']:>10,.0f} TL  (%{pf['return_pct']:+.2f})  "
              f"{len(pf['positions'])} pozisyon")

    # 4) konsensüs (kendi portföyüm hariç yarışmacılardan)
    base_comps = [c for c in common.load_all_competitors() if c["key"] != "consensus"]
    consensus = consensus_mod.compute_consensus(base_comps, snapshot)
    print(f"→ Konsensüs (2+ AI): {', '.join(c['ticker'] for c in consensus) or 'yok'}")

    # 5) şef portföyü + 6) araştırma
    pf = research.sync_consensus_portfolio(consensus, snapshot)
    notes = research.generate_research(consensus)
    print(f"  ✓ Konsensüs (Claude) {pf['total_value']:>10,.0f} TL  (%{pf['return_pct']:+.2f})  "
          f"{len(pf['positions'])} pozisyon")

    # 7) dashboard
    comps = common.load_all_competitors()
    feed = common.merged_trade_feed(comps, limit=50)
    html = dashboard.build_dashboard(comps, feed, consensus, notes, pf, xu30, health=health)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")
    (ROOT / "index.html").write_text(html, encoding="utf-8")

    (DATA_DIR / "last_run.json").write_text(json.dumps({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "health": health,
        "active_competitors": sum(1 for c in comps if c.get("active")),
        "consensus_tickers": [c["ticker"] for c in consensus],
        "leaderboard": sorted(
            [{"name": c["name"], "return_pct": c["return_pct"]} for c in comps if c.get("active")],
            key=lambda x: x["return_pct"], reverse=True),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # Sağlık bozuksa bildirim (kanal kuruluysa; değilse sessiz no-op)
    if not health["ok"]:
        try:
            from orchestrator import notify
            notify.send("⚠ BIST AI Arena: veri DEGRADE — canlı fiyat %d/%d, döngü %s"
                        % (health["live"], health["total"], datetime.now().strftime("%H:%M")))
        except Exception:
            pass

    print(f"✓ Dashboard yazıldı: {DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
