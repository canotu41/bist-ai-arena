#!/usr/bin/env python3
"""BIST AI Arena — Backtest + Kalibrasyon motoru.

2 yıllık gerçek fiyat verisiyle her stratejinin değerlendirme kriterlerini sınar
ve kalibre eder. Canlı sistemle AYNI gösterge/skorlama fonksiyonlarını yeniden
kullanır (deepseek/src). Geçmiş temel veri güncel-sabit, haber nötr (50) tutulur
(ücretsiz geçmiş yok) — bu yüzden backtest ağırlıkla teknik/momentum/risk +
giriş/çıkış mekaniğini doğrular.

Kullanım:
    python3 orchestrator/backtest.py          # backtest + kalibrasyon önerileri
"""
from __future__ import annotations

import json
import math
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "deepseek"))
sys.path.insert(0, str(ROOT))

from src import live_data as ld, signal_generator as sg, data_models as dm  # noqa: E402
from src.fundamental_analysis import (  # noqa: E402
    SECTOR_MAP, COMPANY_NAMES, get_fundamental_data, score_fundamental,
)
from orchestrator.strategies import STRATEGIES, score_for, passes_filter  # noqa: E402

DATA_DIR = ROOT / "orchestrator" / "data"
HIST_CACHE = DATA_DIR / "hist_cache.json"
RESULTS = DATA_DIR / "backtest_results.json"
INDEX = "XU100"
COMMISSION = 0.002
INITIAL = 50000.0
WARMUP = 210  # MA200 için ısınma günü

# deepseek'in kendi motorunun ağırlıkları (SIDEWAYS taban)
DEEPSEEK_W = {"Temel": 0.25, "Teknik": 0.30, "Haber": 0.20, "Momentum": 0.15, "Risk": 0.10}


# ---------- 1) Geçmiş veri ----------

def _fetch(sym: str, rng="2y") -> dict:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.IS"
           f"?range={rng}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    res = d["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    ts, cl, hi, lo, vo = res["timestamp"], q["close"], q["high"], q["low"], q["volume"]
    rows = {}
    for i in range(len(ts)):
        if cl[i] is None:
            continue
        rows[int(ts[i] // 86400)] = (cl[i], hi[i] or cl[i], lo[i] or cl[i], vo[i] or 0)
    return rows


def load_history() -> dict:
    if HIST_CACHE.exists():
        try:
            raw = json.loads(HIST_CACHE.read_text(encoding="utf-8"))
            if time.time() - raw.get("_ts", 0) < 24 * 3600:
                return raw["data"]
        except Exception:
            pass
    print("→ 2y geçmiş veri çekiliyor (BIST30 + XU100)...")
    data = {}
    for tk in [INDEX] + list(SECTOR_MAP.keys()):
        try:
            data[tk] = _fetch(tk)
            print(f"   {tk}: {len(data[tk])} gün")
        except Exception as e:
            print(f"   {tk}: HATA {e}")
        time.sleep(0.3)
    DATA_DIR.mkdir(exist_ok=True)
    HIST_CACHE.write_text(json.dumps({"_ts": int(time.time()), "data":
        {k: {str(d): v for d, v in rows.items()} for k, rows in data.items()}},
        ensure_ascii=False), encoding="utf-8")
    return {k: {int(d): tuple(v) for d, v in rows.items()} for k, rows in data.items()}


# ---------- 2) Günlük bileşen skorlarını yeniden kur ----------

def _light_macd(C):
    if len(C) < 27:
        return 0.0, 0.0
    macds = []
    for j in range(max(0, len(C) - 9), len(C)):
        w = C[:j + 1]
        macds.append(ld._ema(w[-60:], 12) - ld._ema(w[-60:], 26))
    line = macds[-1]
    sig = ld._ema(macds, 9) if macds else line
    return line, sig


def build_tech(tk, C, H, L, V, idx20):
    price = C[-1]

    def pct(n):
        return round((C[-1] / C[-1 - n] - 1) * 100, 2) if len(C) > n and C[-1 - n] else 0.0
    ch20 = pct(20)
    rel = round((1 + ch20 / 100) / (1 + idx20 / 100), 3) if (1 + idx20 / 100) else 1.0
    w52 = C[-252:] if len(C) >= 252 else C
    hi52, lo52 = max(w52), min(w52)
    bb_u, bb_m, bb_l = ld._bollinger(C)
    bbpos = round((price - bb_l) / (bb_u - bb_l) * 100, 1) if bb_u != bb_l else 50.0
    macd, macd_sig = _light_macd(C)
    return dm.TechnicalData(
        ticker=tk, price=price, change_1d_pct=pct(1), change_5d_pct=pct(5),
        change_20d_pct=ch20, change_60d_pct=pct(60), rsi_14=round(ld._rsi(C), 1),
        macd=round(macd, 3), macd_signal=round(macd_sig, 3), macd_histogram=round(macd - macd_sig, 3),
        bb_upper=bb_u, bb_middle=bb_m, bb_lower=bb_l, bb_position_pct=bbpos,
        ma_20=round(ld._sma(C, 20), 2), ma_50=round(ld._sma(C, 50), 2), ma_200=round(ld._sma(C, 200), 2),
        volume=0, volume_20d_avg=0, volume_ratio=round(V[-1] / (ld._sma(V, 20) or 1), 2) if V else 1.0,
        stochastic_k=ld._stochastic(H, L, C), stochastic_d=0.0, atr_14=0.0,
        atr_pct=ld._atr_pct(H, L, C),
        price_vs_52w_high_pct=round(price / hi52 * 100, 1) if hi52 else 100.0,
        price_vs_52w_low_pct=round(price / lo52 * 100, 1) if lo52 else 100.0,
        relative_strength_vs_xu30=rel)


def precompute(history):
    """Ortak takvim + her (ticker, gün) için price, breakdown, snap."""
    idx = history[INDEX]
    days = sorted(set(idx.keys()))
    # sabit temel skorlar (güncel değer, backtest boyunca sabit)
    fund_score, fk, roe = {}, {}, {}
    for tk in SECTOR_MAP:
        f = get_fundamental_data(tk)
        fund_score[tk] = score_fundamental(f)
        fk[tk], roe[tk] = f.fk_ratio, f.roe

    # index kapanış listesi — days hepsi index günü olduğu için gi ile hizalı
    idx_close_list = [idx[d][0] for d in days]

    per = {}  # tk -> {day_index_in_days: (price, breakdown, snap)}
    for tk in SECTOR_MAP:
        if tk not in history:
            continue
        rows = history[tk]
        d_sorted = sorted(rows.keys())
        C = [rows[d][0] for d in d_sorted]
        H = [rows[d][1] for d in d_sorted]
        L = [rows[d][2] for d in d_sorted]
        V = [rows[d][3] for d in d_sorted]
        day_pos = {d: i for i, d in enumerate(d_sorted)}
        out = {}
        for gi, day in enumerate(days):
            if day not in day_pos:
                continue
            i = day_pos[day]
            if i < WARMUP:
                continue
            s = slice(max(0, i - 260), i + 1)
            idx20 = (round((idx_close_list[gi] / idx_close_list[gi - 20] - 1) * 100, 2)
                     if gi >= 20 and idx_close_list[gi - 20] else 0.0)
            tech = build_tech(tk, C[s], H[s], L[s], V[s], idx20)
            bd = {"Temel": fund_score[tk], "Teknik": sg.calculate_technical_score(tech),
                  "Haber": 50.0, "Momentum": sg.calculate_momentum_score(tech),
                  "Risk": sg.calculate_risk_score(tech)}
            snap = {"price": tech.price, "rsi": tech.rsi_14, "atr_pct": tech.atr_pct,
                    "change_20d": tech.change_20d_pct, "fk": fk[tk], "roe": roe[tk],
                    "ma20": tech.ma_20, "ma50": tech.ma_50, "ma200": tech.ma_200}
            out[gi] = (tech.price, bd, snap)
        per[tk] = out
    return days, per


def deepscore(bd):
    return round(sum(bd[k] * w for k, w in DEEPSEEK_W.items()) / sum(DEEPSEEK_W.values()), 1)


# ---------- 3) Backtest motoru ----------

def run_sim(cfg, days, per, index_close, verbose=False):
    """cfg: dict(score_fn, filters, buy, sell, stop, target, max_pos, max_single, min_cash, max_sector)."""
    cash = INITIAL
    held = {}   # tk -> {entry, qty, stop, target, sector}
    values, trades, wins, losses = [], 0, 0, 0
    score_samples = []

    for gi in range(len(days)):
        # o gün fiyatı olan hisseler
        avail = {tk: per[tk][gi] for tk in per if gi in per[tk]}
        # skorla
        scored = {}
        for tk, (price, bd, snap) in avail.items():
            sc = cfg["score_fn"](bd)
            scored[tk] = (sc, price, snap)
            score_samples.append(sc)

        # 1) MTM + stop/hedef
        for tk in list(held):
            if tk not in avail:
                continue
            price = avail[tk][0]
            p = held[tk]
            if price <= p["stop"] or price >= p["target"]:
                cash += price * p["qty"] * (1 - COMMISSION)
                wins += 1 if price > p["entry"] else 0
                losses += 1 if price <= p["entry"] else 0
                del held[tk]
        # 2) skor düşüşünde çıkış
        for tk in list(held):
            if tk in scored and scored[tk][0] < cfg["sell"]:
                price = scored[tk][1]
                p = held[tk]
                cash += price * p["qty"] * (1 - COMMISSION)
                wins += 1 if price > p["entry"] else 0
                losses += 1 if price <= p["entry"] else 0
                del held[tk]

        # 3) portföy değeri (giriş öncesi)
        value = cash + sum(avail[tk][0] * held[tk]["qty"] for tk in held if tk in avail)

        # 4) girişler
        cands = sorted((tk for tk, (sc, pr, sn) in scored.items()
                        if tk not in held and sc >= cfg["buy"]
                        and (cfg["filters"] is None or passes_filter({"filters": cfg["filters"]}, sn))),
                       key=lambda t: scored[t][0], reverse=True)
        for tk in cands:
            if len(held) >= cfg["max_pos"]:
                break
            sc, price, snap = scored[tk]
            sector = SECTOR_MAP.get(tk, "-")
            sec_val = sum(avail[t][0] * held[t]["qty"] for t in held
                          if t in avail and SECTOR_MAP.get(t) == sector)
            room_sec = max(0.0, cfg["max_sector"] - (sec_val / value if value else 0))
            avail_cash = cash - value * cfg["min_cash"]
            alloc = min(value * cfg["max_single"], value * room_sec, avail_cash)
            if alloc < 300:
                continue
            qty = int(alloc // price)
            if qty < 1:
                continue
            cost = qty * price * (1 + COMMISSION)
            if cost > cash:
                continue
            cash -= cost
            held[tk] = {"entry": price, "qty": qty, "sector": sector,
                        "stop": price * (1 + cfg["stop"]), "target": price * (1 + cfg["target"])}
            trades += 1

        value = cash + sum(avail[tk][0] * held[tk]["qty"] for tk in held if tk in avail)
        values.append(value)

    # metrikler
    final = values[-1] if values else INITIAL
    total_ret = (final - INITIAL) / INITIAL * 100
    peak, mdd = INITIAL, 0.0
    for v in values:
        peak = max(peak, v)
        mdd = min(mdd, (v - peak) / peak * 100)
    rets = [(values[i] / values[i - 1] - 1) for i in range(1, len(values)) if values[i - 1]]
    sharpe = (statistics.mean(rets) / statistics.pstdev(rets) * math.sqrt(252)
              if len(rets) > 2 and statistics.pstdev(rets) else 0.0)
    win_rate = wins / (wins + losses) * 100 if (wins + losses) else 0.0
    # benchmark
    idx_days = sorted(index_close.keys())
    bench = (index_close[idx_days[-1]] / index_close[idx_days[WARMUP]] - 1) * 100 if len(idx_days) > WARMUP else 0.0
    return {
        "total_return": round(total_ret, 1), "alpha": round(total_ret - bench, 1),
        "max_drawdown": round(mdd, 1), "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 1), "trades": trades,
        "final_value": round(final, 0), "score_samples": score_samples,
    }


def cfg_for(key, buy, sell, stop, target):
    s = STRATEGIES.get(key, {})
    if key == "deepseek":
        return {"score_fn": deepscore, "filters": None, "buy": buy, "sell": sell,
                "stop": stop, "target": target, "max_pos": 8, "max_single": 0.20,
                "min_cash": 0.05, "max_sector": 0.30}
    return {"score_fn": lambda bd, _s=s: score_for(_s, bd), "filters": s.get("filters"),
            "buy": buy, "sell": sell, "stop": stop, "target": target,
            "max_pos": s["max_positions"], "max_single": s["max_single_pct"],
            "min_cash": s["min_cash_pct"], "max_sector": s["max_sector_pct"]}


def pctile(xs, p):
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * p / 100
    lo = int(math.floor(k))
    return round(xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (k - lo), 1)


def main():
    history = load_history()
    print("→ Günlük bileşen skorları yeniden kuruluyor (birkaç saniye)...")
    days, per = precompute(history)
    index_close = {gi: history[INDEX][day][0] for gi, day in enumerate(days) if day in history[INDEX]}
    bench = (list(index_close.values())[-1] / list(index_close.values())[WARMUP] - 1) * 100

    print(f"\n=== BACKTEST ({len(days)} gün, ~2y) | XU100: %{bench:+.1f} ===\n")
    strat_keys = ["claude", "codex", "microsoft", "deepseek"]

    # 1) baz skorlarla dağılım + baz backtest
    base = {}
    for k in strat_keys:
        s = STRATEGIES.get(k, {})
        buy = s.get("buy_threshold", 72 if k == "deepseek" else 62)
        sell = s.get("sell_threshold", 46)
        stop = s.get("stop_pct", -0.08)
        tgt = s.get("target_pct", 0.20)
        r = run_sim(cfg_for(k, buy, sell, stop, tgt), days, per, index_close)
        samples = r.pop("score_samples")
        base[k] = {"result": r, "buy": buy,
                   "p50": pctile(samples, 50), "p80": pctile(samples, 80),
                   "p85": pctile(samples, 85), "p90": pctile(samples, 90),
                   "max": round(max(samples), 1)}
        print(f"{k:10} MEVCUT eşik {buy}: getiri %{r['total_return']:+.1f} "
              f"alfa %{r['alpha']:+.1f} düşüş %{r['max_drawdown']:.1f} "
              f"isabet %{r['win_rate']:.0f} işlem {r['trades']} | "
              f"skor dağılımı p50={base[k]['p50']} p80={base[k]['p80']} p90={base[k]['p90']} max={base[k]['max']}")

    # 2) kalibrasyon: SEÇİCİ al (p85), NADİR çık (sat=40), GENİŞ stop / yüksek hedef
    #    -> yükselen piyasada kazananları tut, whipsaw'ı azalt. Amaç: getiriyi enbüyük
    #    (dejenere 0-işlemi engellemek için en az 5 işlem şartı).
    print("\n=== KALİBRASYON (seçici al + uzun tut) ===\n")
    calib = {}
    for k in strat_keys:
        buy = base[k]["p85"]
        sell = 40.0
        best = None
        for stop in (-0.10, -0.12, -0.15):           # ileriye dönük güvenlik: her zaman stop
            for tgt in (0.30, 0.40, 0.99):           # 0.99 = tavan yok (kazananı bırak)
                r = run_sim(cfg_for(k, buy, sell, stop, tgt), days, per, index_close)
                r.pop("score_samples")
                obj = r["total_return"] if r["trades"] >= 5 else -999
                if best is None or obj > best[0]:
                    best = (obj, stop, tgt, r)
        _, stop, tgt, r = best
        calib[k] = {"buy": buy, "sell": sell, "stop": stop, "target": tgt, "result": r}
        stop_s = "yok" if stop <= -0.9 else f"{stop:+.0%}"
        tgt_s = "yok" if tgt >= 0.99 else f"{tgt:+.0%}"
        print(f"{k:10} -> al={buy} sat={sell} stop={stop_s} hedef={tgt_s}  "
              f"=> getiri %{r['total_return']:+.1f} alfa %{r['alpha']:+.1f} "
              f"düşüş %{r['max_drawdown']:.1f} isabet %{r['win_rate']:.0f} işlem {r['trades']}")

    out = {"period_days": len(days), "benchmark_xu100": round(bench, 1),
           "generated": time.strftime("%Y-%m-%d %H:%M"),
           "base": {k: base[k]["result"] | {"buy": base[k]["buy"]} for k in strat_keys},
           "calibrated": {k: {"buy": calib[k]["buy"], "sell": calib[k]["sell"],
                              "stop": calib[k]["stop"], "target": calib[k]["target"],
                              **calib[k]["result"]} for k in strat_keys}}
    DATA_DIR.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Sonuçlar yazıldı: {RESULTS}")


if __name__ == "__main__":
    main()
