#!/usr/bin/env python3
"""BIST AI Arena — Orchestrator.

Bir döngü:
  1. deepseek ve microsoft motorlarını ilerlet (best-effort, izole subprocess)
  2. deepseek analiz anlık görüntüsünü JSON'a dök
  3. tüm yarışmacıları normalize et
  4. konsensüs (2+ AI ortak) hisseleri hesapla
  5. Konsensüs (Claude) portföyünü kur/güncelle  -> 5. yarışmacı
  6. araştırma notları üret
  7. tek birleşik dashboard.html üret + heartbeat yaz

Kullanım:  python3 orchestrator/run.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT = ORCH_DIR.parent
DATA_DIR = ORCH_DIR / "data"
DASHBOARD_HTML = ROOT / "dashboard.html"

sys.path.insert(0, str(ROOT))
from orchestrator import common, consensus as consensus_mod, research, dashboard  # noqa: E402


def _run(cmd, cwd, pythonpath=None, label=""):
    import os
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = str(pythonpath)
    try:
        r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True,
                           text=True, timeout=120)
        ok = r.returncode == 0
        print(f"  {'✓' if ok else '✗'} {label}"
              + ("" if ok else f"  ({(r.stderr or '').strip().splitlines()[-1:] })"))
        return ok
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        return False


def advance_engines() -> None:
    print("→ Motorlar ilerletiliyor...")
    _run([sys.executable, "main.py", "cycle"], ROOT / "deepseek", label="deepseek cycle")
    _run([sys.executable, "-c",
          "import sys; sys.path.insert(0,'.'); "
          "from src.generate_report import main; main()"],
         ROOT / "microsoft", pythonpath=ROOT / "microsoft", label="microsoft report")


def dump_snapshot() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / "snapshot.json"
    ok = _run([sys.executable, str(ORCH_DIR / "_snapshot_dump.py"), str(out)],
              ROOT / "deepseek", pythonpath=ROOT / "deepseek", label="deepseek snapshot")
    if not ok and not out.exists():
        out.write_text("[]", encoding="utf-8")


def get_xu30() -> float:
    try:
        comp = json.loads((ROOT / "deepseek" / "competition.json").read_text(encoding="utf-8"))
        return float(comp.get("xu30_return", 0.5))
    except Exception:
        return 0.5


def main() -> None:
    print(f"=== BIST AI Arena döngüsü — {datetime.now():%Y-%m-%d %H:%M} ===")
    advance_engines()
    dump_snapshot()

    snapshot = common.load_snapshot()
    xu30 = get_xu30()

    # Konsensüs, kendi portföyü hariç yarışmacılardan hesaplanır
    base_comps = [c for c in common.load_all_competitors() if c["key"] != "consensus"]
    consensus = consensus_mod.compute_consensus(base_comps, snapshot)
    print(f"→ Konsensüs hisseleri (2+ AI): {', '.join(c['ticker'] for c in consensus) or 'yok'}")

    # 5. yarışmacı: Konsensüs (Claude) portföyü
    pf = research.sync_consensus_portfolio(consensus, snapshot)
    notes = research.generate_research(consensus)

    # Dashboard için TÜM yarışmacıları (konsensüs dahil) yeniden yükle
    comps = common.load_all_competitors()
    feed = common.merged_trade_feed(comps, limit=40)

    html = dashboard.build_dashboard(comps, feed, consensus, notes, pf, xu30)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")

    # Heartbeat
    (DATA_DIR / "last_run.json").write_text(json.dumps({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_competitors": sum(1 for c in comps if c.get("active")),
        "consensus_tickers": [c["ticker"] for c in consensus],
        "consensus_portfolio_value": pf["total_value"],
        "consensus_return_pct": pf["return_pct"],
        "trades_in_feed": len(feed),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"→ Konsensüs portföyü: {pf['total_value']:,.2f} TL (%{pf['return_pct']:+.2f}), "
          f"{len(pf['positions'])} pozisyon")
    print(f"✓ Dashboard yazıldı: {DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
