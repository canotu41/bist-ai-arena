"""deepseek'in analiz motorunu izole çalıştırıp BIST30 anlık görüntüsünü
JSON'a döker. cwd=deepseek ile çağrılır (böylece `from src...` çalışır).

Kullanım:  python3 _snapshot_dump.py <cikti_json_yolu>
"""
import json
import sys


def main(out_path: str) -> None:
    from src.signal_generator import scan_all_companies

    snapshots = scan_all_companies()
    rows = []
    for s in snapshots:
        t = s.technical
        f = s.fundamental
        rows.append({
            "ticker": s.ticker,
            "company": s.company_name,
            "sector": s.sector,
            "deepscore": s.deepscore,
            "signal": s.signal.value,
            "breakdown": s.score_breakdown,
            "price": getattr(t, "price", 0.0) if t else 0.0,
            "rsi": getattr(t, "rsi_14", 0.0) if t else 0.0,
            "change_20d": getattr(t, "change_20d_pct", 0.0) if t else 0.0,
            "ma20": getattr(t, "ma_20", 0.0) if t else 0.0,
            "ma50": getattr(t, "ma_50", 0.0) if t else 0.0,
            "ma200": getattr(t, "ma_200", 0.0) if t else 0.0,
            "atr_pct": getattr(t, "atr_pct", 0.0) if t else 0.0,
            "fk": getattr(f, "fk_ratio", 0.0) if f else 0.0,
            "roe": getattr(f, "roe", 0.0) if f else 0.0,
            "net_profit_growth": getattr(f, "net_profit_growth_qoq", 0.0) if f else 0.0,
        })

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(sys.argv[1])
