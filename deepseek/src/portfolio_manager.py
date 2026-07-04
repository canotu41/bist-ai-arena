"""DeepSeek BIST30 - Portföy Yönetim Modülü"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .data_models import (
    PortfolioState, Position, Transaction,
    SignalType, MarketRegime, CompanySnapshot,
)
from .signal_generator import scan_all_companies, detect_market_regime
from .technical_analysis import get_technical_data
from .fundamental_analysis import SECTOR_MAP, COMPANY_NAMES

ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO_JSON = ROOT / "portfolio.json"
LOG_DIR = ROOT / "log"

# Derin öğrenme öğrenilmiş dersler (v2 için temel)
LEARNED_LESSONS = {
    "max_single_position_pct": 0.20,
    "min_cash_buffer_pct": 0.05,
    "stop_loss_pct": -0.08,
    "take_profit_pct": 0.20,
    "trailing_stop_activation_pct": 0.10,
    "trailing_stop_distance_pct": -0.05,
    "max_positions": 10,
    "max_sector_exposure": {"Bankacılık": 0.30, "Sanayi": 0.25, "Hizmet": 0.25, "Teknoloji/Savunma": 0.20},
}


def _tx_id() -> str:
    return uuid.uuid4().hex[:8].upper()


def load_portfolio() -> PortfolioState:
    """Portföyü JSON'dan yükler, yoksa yeni oluşturur"""
    if PORTFOLIO_JSON.exists():
        raw = json.loads(PORTFOLIO_JSON.read_text(encoding="utf-8"))
        positions = [
            Position(
                ticker=p["ticker"], company_name=p["company_name"], sector=p["sector"],
                entry_price=p["entry_price"], quantity=p["quantity"], entry_date=p["entry_date"],
                cost_basis=p["cost_basis"], stop_loss=p["stop_loss"], take_profit=p["take_profit"],
                trailing_stop_active=p.get("trailing_stop_active", False),
                trailing_stop_level=p.get("trailing_stop_level", 0.0),
                current_price=p.get("current_price", p["entry_price"]),
                unrealized_pnl=p.get("unrealized_pnl", 0.0),
                unrealized_pnl_pct=p.get("unrealized_pnl_pct", 0.0),
                days_held=p.get("days_held", 0),
                deepscore_at_entry=p.get("deepscore_at_entry", 0.0),
            )
            for p in raw.get("positions", [])
        ]
        transactions = [
            Transaction(**t) for t in raw.get("transactions", [])
        ]
        regime_str = raw.get("market_regime", "SIDEWAYS")
        regime = MarketRegime[regime_str] if regime_str in MarketRegime.__members__ else MarketRegime.SIDEWAYS
        return PortfolioState(
            name=raw.get("name", "DeepSeek BIST30 Portföy"),
            initial_capital=raw.get("initial_capital", 10000.0),
            cash=raw.get("cash", 10000.0),
            positions=positions,
            transactions=transactions,
            total_value=raw.get("total_value", 10000.0),
            total_return_pct=raw.get("total_return_pct", 0.0),
            benchmark_return_pct=raw.get("benchmark_return_pct", 0.0),
            alpha_pct=raw.get("alpha_pct", 0.0),
            week=raw.get("week", 0),
            current_drawdown_pct=raw.get("current_drawdown_pct", 0.0),
            max_drawdown_pct=raw.get("max_drawdown_pct", 0.0),
            win_rate_pct=raw.get("win_rate_pct", 0.0),
            market_regime=regime,
            last_updated=raw.get("last_updated", ""),
            created_date=raw.get("created_date", "2026-07-03"),
        )
    return PortfolioState()


def save_portfolio(portfolio: PortfolioState) -> None:
    """Portföyü JSON'a kaydeder"""
    portfolio.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {
        "name": portfolio.name,
        "initial_capital": portfolio.initial_capital,
        "cash": portfolio.cash,
        "positions": [
            {
                "ticker": p.ticker, "company_name": p.company_name, "sector": p.sector,
                "entry_price": p.entry_price, "quantity": p.quantity, "entry_date": p.entry_date,
                "cost_basis": p.cost_basis, "stop_loss": p.stop_loss, "take_profit": p.take_profit,
                "trailing_stop_active": p.trailing_stop_active,
                "trailing_stop_level": p.trailing_stop_level,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
                "unrealized_pnl_pct": p.unrealized_pnl_pct,
                "days_held": p.days_held,
                "deepscore_at_entry": p.deepscore_at_entry,
            }
            for p in portfolio.positions
        ],
        "transactions": [
            {
                "id": t.id, "timestamp": t.timestamp, "type": t.type,
                "ticker": t.ticker, "quantity": t.quantity, "price": t.price,
                "total_amount": t.total_amount, "commission": t.commission,
                "reason": t.reason,
                "signal_type": t.signal_type.value if hasattr(t.signal_type, 'value') else str(t.signal_type),
                "deepscore": t.deepscore,
            }
            for t in portfolio.transactions
        ],
        "total_value": portfolio.total_value,
        "total_return_pct": portfolio.total_return_pct,
        "benchmark_return_pct": portfolio.benchmark_return_pct,
        "alpha_pct": portfolio.alpha_pct,
        "week": portfolio.week,
        "current_drawdown_pct": portfolio.current_drawdown_pct,
        "max_drawdown_pct": portfolio.max_drawdown_pct,
        "win_rate_pct": portfolio.win_rate_pct,
        "market_regime": portfolio.market_regime.value,
        "last_updated": portfolio.last_updated,
        "created_date": portfolio.created_date,
    }
    PORTFOLIO_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_market_prices(portfolio: PortfolioState) -> None:
    """Güncel fiyatları çeker ve portföyü günceller"""
    total_value = portfolio.cash
    for pos in portfolio.positions:
        tech = get_technical_data(pos.ticker)
        new_price = tech.price
        # Şirket-işlemi koruması: BIST günlük marjı dar; tek döngü >%25 değişim
        # bölünme/bedelsiz/veri sıçramasıdır -> bazları ölçekle, sahte stop önle.
        old = pos.current_price or pos.entry_price
        if old and new_price and new_price > 0:
            r = new_price / old
            if r < 0.75 or r > 1.30:
                pos.entry_price = round(pos.entry_price * r, 4)
                pos.stop_loss = round(pos.stop_loss * r, 4)
                pos.take_profit = round(pos.take_profit * r, 4)
                pos.quantity = pos.quantity / r
        pos.current_price = new_price
        pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity
        pos.unrealized_pnl_pct = ((pos.current_price - pos.entry_price) / pos.entry_price) * 100
        total_value += pos.current_price * pos.quantity
    portfolio.total_value = round(total_value, 2)
    portfolio.total_return_pct = round(((total_value - portfolio.initial_capital) / portfolio.initial_capital) * 100, 2)
    # DD hesapla
    peak = portfolio.initial_capital
    for t in portfolio.transactions:
        peak = max(peak, portfolio.total_value)
    if peak > 0:
        portfolio.current_drawdown_pct = round(((portfolio.total_value - peak) / peak) * 100, 2)
        portfolio.max_drawdown_pct = min(portfolio.max_drawdown_pct, portfolio.current_drawdown_pct)


def check_stops_and_targets(portfolio: PortfolioState) -> List[Transaction]:
    """Stop-loss ve take-profit kontrollerini yapar"""
    transactions = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    positions_to_remove = []

    for pos in portfolio.positions:
        pnl_pct = pos.unrealized_pnl_pct

        # Stop-loss kontrolü
        if pnl_pct <= LEARNED_LESSONS["stop_loss_pct"] * 100:
            tx = Transaction(
                id=_tx_id(), timestamp=now, type="SELL", ticker=pos.ticker,
                quantity=pos.quantity, price=pos.current_price,
                total_amount=pos.current_price * pos.quantity,
                commission=round(pos.current_price * pos.quantity * 0.002, 2),
                reason=f"STOP-LOSS tetiklendi: %{round(pnl_pct, 2)} düşüş (limit: %{LEARNED_LESSONS['stop_loss_pct'] * 100})",
                signal_type=SignalType.SELL, deepscore=0.0,
            )
            transactions.append(tx)
            portfolio.cash += tx.total_amount - tx.commission
            positions_to_remove.append(pos)
            continue

        # Take-profit kontrolü
        if pnl_pct >= LEARNED_LESSONS["take_profit_pct"] * 100:
            sell_qty = pos.quantity // 2  # %50 sat
            if sell_qty > 0:
                tx = Transaction(
                    id=_tx_id(), timestamp=now, type="SELL_PARTIAL", ticker=pos.ticker,
                    quantity=sell_qty, price=pos.current_price,
                    total_amount=pos.current_price * sell_qty,
                    commission=round(pos.current_price * sell_qty * 0.002, 2),
                    reason=f"TAKE-PROFIT: %{round(pnl_pct, 1)} kârda %50 satış (hedef: +%{LEARNED_LESSONS['take_profit_pct'] * 100})",
                    signal_type=SignalType.HOLD, deepscore=0.0,
                )
                transactions.append(tx)
                pos.quantity -= sell_qty
                pos.cost_basis -= pos.entry_price * sell_qty
                portfolio.cash += tx.total_amount - tx.commission
                # Trailing stop aktifleştir
                pos.trailing_stop_active = True
                pos.trailing_stop_level = pos.current_price * (1 + LEARNED_LESSONS["trailing_stop_distance_pct"])

        # Trailing stop kontrolü
        if pos.trailing_stop_active and pos.current_price <= pos.trailing_stop_level:
            tx = Transaction(
                id=_tx_id(), timestamp=now, type="SELL", ticker=pos.ticker,
                quantity=pos.quantity, price=pos.current_price,
                total_amount=pos.current_price * pos.quantity,
                commission=round(pos.current_price * pos.quantity * 0.002, 2),
                reason=f"TRAILING-STOP: Fiyat {pos.trailing_stop_level:.2f} seviyesine düştü",
                signal_type=SignalType.SELL, deepscore=0.0,
            )
            transactions.append(tx)
            portfolio.cash += tx.total_amount - tx.commission
            positions_to_remove.append(pos)

    for pos in positions_to_remove:
        portfolio.positions.remove(pos)

    return transactions


def get_sector_exposure(portfolio: PortfolioState, sector: str) -> float:
    """Belirli bir sektördeki toplam pozisyon ağırlığını hesaplar"""
    if portfolio.total_value <= 0:
        return 0.0
    sector_value = sum(p.current_price * p.quantity for p in portfolio.positions if p.sector == sector)
    return sector_value / portfolio.total_value


def find_entry_opportunities(portfolio: PortfolioState, snapshots: List[CompanySnapshot]) -> List[Transaction]:
    """Yeni giriş fırsatlarını değerlendirir"""
    transactions = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    max_positions = LEARNED_LESSONS["max_positions"]

    if len(portfolio.positions) >= max_positions:
        return transactions

    # Nakit tamponu kontrolü
    min_cash = portfolio.total_value * LEARNED_LESSONS["min_cash_buffer_pct"]
    available_cash = portfolio.cash - min_cash
    if available_cash <= 0:
        return transactions

    # Mevcut pozisyon ticker'ları
    held_tickers = {p.ticker for p in portfolio.positions}

    for snap in snapshots:
        if snap.ticker in held_tickers:
            continue
        if snap.signal not in (SignalType.STRONG_BUY, SignalType.BUY):
            continue
        if snap.deepscore < 72:
            continue
        if len(portfolio.positions) >= max_positions:
            break

        # Pozisyon boyutu hesapla
        max_single = portfolio.total_value * LEARNED_LESSONS["max_single_position_pct"]
        # Sektör limiti kontrolü
        sector_limit = LEARNED_LESSONS["max_sector_exposure"].get(snap.sector, 0.25)
        current_sector_pct = get_sector_exposure(portfolio, snap.sector)
        remaining_sector_pct = max(0, sector_limit - current_sector_pct)
        max_by_sector = portfolio.total_value * remaining_sector_pct

        position_size = min(max_single, max_by_sector, available_cash)
        if position_size < 300:  # minimum işlem büyüklüğü
            continue

        price = snap.technical.price if snap.technical else 50.0
        quantity = max(1, int(position_size / price))
        total_cost = quantity * price
        commission = round(total_cost * 0.002, 2)

        if total_cost + commission > available_cash:
            quantity = max(1, int((available_cash - commission) / price))
            total_cost = quantity * price

        if quantity <= 0:
            continue

        stop_loss_price = round(price * (1 + LEARNED_LESSONS["stop_loss_pct"]), 2)
        take_profit_price = round(price * (1 + LEARNED_LESSONS["take_profit_pct"]), 2)

        pos = Position(
            ticker=snap.ticker,
            company_name=snap.company_name,
            sector=snap.sector,
            entry_price=price,
            quantity=quantity,
            entry_date=now,
            cost_basis=total_cost,
            stop_loss=stop_loss_price,
            take_profit=take_profit_price,
            current_price=price,
            deepscore_at_entry=snap.deepscore,
        )
        portfolio.positions.append(pos)
        portfolio.cash -= (total_cost + commission)

        tx = Transaction(
            id=_tx_id(), timestamp=now, type="BUY", ticker=snap.ticker,
            quantity=quantity, price=price,
            total_amount=total_cost, commission=commission,
            reason=f"DeepScore™ {snap.deepscore:.1f} ({snap.signal.value}) | Sektör: {snap.sector}",
            signal_type=snap.signal, deepscore=snap.deepscore,
        )
        transactions.append(tx)
        available_cash = portfolio.cash - min_cash

    return transactions


def execute_cycle() -> PortfolioState:
    """Bir tam karar döngüsü çalıştırır"""
    portfolio = load_portfolio()

    # 1. Güncel fiyatları çek
    update_market_prices(portfolio)

    # 2. Piyasa rejimini tespit et
    from .technical_analysis import scan_all_bist30
    all_tech = scan_all_bist30()
    portfolio.market_regime = detect_market_regime(all_tech)

    # 3. Stop/hedef kontrolleri
    stop_transactions = check_stops_and_targets(portfolio)
    portfolio.transactions.extend(stop_transactions)

    # 4. Yeni fırsatları tara
    snapshots = scan_all_companies()
    entry_transactions = find_entry_opportunities(portfolio, snapshots)
    portfolio.transactions.extend(entry_transactions)

    # 5. Güncel değeri hesapla
    portfolio.total_value = portfolio.cash + sum(
        p.current_price * p.quantity for p in portfolio.positions
    )
    portfolio.total_return_pct = round(
        ((portfolio.total_value - portfolio.initial_capital) / portfolio.initial_capital) * 100, 2
    )

    # 6. Win rate güncelle
    sell_txs = [t for t in portfolio.transactions if t.type in ("SELL", "SELL_PARTIAL")]
    if sell_txs:
        win_sells = [t for t in sell_txs if t.reason and "TAKE-PROFIT" in t.reason]
        portfolio.win_rate_pct = round(len(win_sells) / len(sell_txs) * 100, 1)

    # 7. Log yaz
    write_cycle_log(portfolio, stop_transactions + entry_transactions)

    # 8. Kaydet
    save_portfolio(portfolio)
    return portfolio


def write_cycle_log(portfolio: PortfolioState, new_transactions: List[Transaction]) -> None:
    """Döngü logunu yazar"""
    LOG_DIR.mkdir(exist_ok=True)
    now = datetime.now()
    log_file = LOG_DIR / f"{now.strftime('%Y-%m-%d_%H-%M')}_deepseek.md"

    lines = [
        f"# DeepSeek Karar Döngüsü Logu",
        f"Tarih: {now.strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Portföy Özeti",
        f"- Toplam Değer: {portfolio.total_value:.2f} TL",
        f"- Nakit: {portfolio.cash:.2f} TL",
        f"- Getiri: %{portfolio.total_return_pct:.2f}",
        f"- Piyasa Rejimi: {portfolio.market_regime.value}",
        f"- Açık Pozisyon: {len(portfolio.positions)}",
        f"",
    ]

    if new_transactions:
        lines.append("## Bu Döngüde Yapılan İşlemler")
        for t in new_transactions:
            lines.append(f"- **{t.type}** {t.ticker} x{t.quantity} @ {t.price:.2f} TL = {t.total_amount:.2f} TL")
            lines.append(f"  - Komisyon: {t.commission:.2f} TL")
            lines.append(f"  - Gerekçe: {t.reason}")
            lines.append("")
    else:
        lines.append("## Bu Döngüde İşlem Yok")
        lines.append("Stop/take-profit tetiklenmedi, yeni giriş sinyali bulunamadı.")
        lines.append("")

    lines.append("## Açık Pozisyonlar")
    for p in portfolio.positions:
        lines.append(f"- **{p.ticker}** ({p.company_name}) | Giriş: {p.entry_price:.2f} TL | Güncel: {p.current_price:.2f} TL | PnL: %{p.unrealized_pnl_pct:.1f} | Stop: {p.stop_loss:.2f} | Hedef: {p.take_profit:.2f}")
    lines.append("")

    log_file.write_text("\n".join(lines), encoding="utf-8")


def initialize_portfolio() -> PortfolioState:
    """İlk portföyü oluşturur - DeepSeek'in başlangıç seçimleri"""
    portfolio = PortfolioState()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # DeepSeek'in ilk tercihleri (en yüksek DeepScore'lu hisseler)
    # Farklı sektörlerden seçim
    initial_picks = [
        ("YKBNK", 1640.0),   # Bankacılık - düşük F/K, yüksek büyüme
        ("TOASO", 1500.0),   # Otomotiv - güçlü momentum
        ("PGSUS", 1400.0),   # Havacılık - güçlü büyüme
        ("AKSEN", 1200.0),   # Enerji - momentum
        ("SAHOL", 1200.0),   # Holding - değer
        ("ASELS", 1200.0),   # Savunma - haber katalisti
        ("CCOLA", 1000.0),   # Gıda - defansif
        ("SISE", 500.0),     # Holding - çeşitlendirme
    ]

    total_invested = 0.0
    for ticker, amount in initial_picks:
        tech = get_technical_data(ticker)
        price = tech.price
        quantity = max(1, int(amount / price))
        total_cost = quantity * price
        commission = round(total_cost * 0.002, 2)

        pos = Position(
            ticker=ticker,
            company_name=COMPANY_NAMES.get(ticker, ticker),
            sector=SECTOR_MAP.get(ticker, "Diğer"),
            entry_price=price,
            quantity=quantity,
            entry_date=now,
            cost_basis=total_cost,
            stop_loss=round(price * 0.92, 2),
            take_profit=round(price * 1.20, 2),
            current_price=price,
            deepscore_at_entry=0.0,
        )
        portfolio.positions.append(pos)
        portfolio.cash -= (total_cost + commission)
        total_invested += total_cost

        tx = Transaction(
            id=_tx_id(), timestamp=now, type="BUY", ticker=ticker,
            quantity=quantity, price=price,
            total_amount=total_cost, commission=commission,
            reason=f"DeepSeek başlangıç portföyü seçimi",
            signal_type=SignalType.BUY, deepscore=0.0,
        )
        portfolio.transactions.append(tx)

    portfolio.total_value = portfolio.cash + sum(
        p.current_price * p.quantity for p in portfolio.positions
    )
    portfolio.total_return_pct = round(
        ((portfolio.total_value - portfolio.initial_capital) / portfolio.initial_capital) * 100, 2
    )
    portfolio.last_updated = now
    save_portfolio(portfolio)

    # Başlangıç logu
    LOG_DIR.mkdir(exist_ok=True)
    init_log = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_baslangic_deepseek.md"
    lines = [
        "# DeepSeek BIST30 - Başlangıç Portföyü",
        f"Tarih: {now}",
        "",
        "## Strateji: DeepScore™ 5-Eksenli Model",
        "- Temel Analiz: %25",
        "- Teknik Analiz: %30",
        "- Haber/Katalist: %20",
        "- Momentum: %15",
        "- Risk/Volatilite: %10",
        "",
        f"## Başlangıç Sermayesi: {portfolio.initial_capital:.0f} TL",
        f"## Yatırılan Tutar: {total_invested:.2f} TL",
        f"## Nakit Tampon: {portfolio.cash:.2f} TL",
        "",
        "## Seçilen Hisseler:",
    ]
    for ticker, amount in initial_picks:
        tech = get_technical_data(ticker)
        lines.append(f"- **{ticker}** ({COMPANY_NAMES.get(ticker, '')}) | {SECTOR_MAP.get(ticker, '')} | ~{amount:.0f} TL | Giriş: {tech.price:.2f} TL")
    lines.append("")
    lines.append("## DeepSeek'in Avantajları:")
    lines.append("1. Çok katmanlı kantitatif skorlama")
    lines.append("2. Piyasa rejimine adaptif ağırlıklar")
    lines.append("3. Tight stop-loss ve trailing stop")
    lines.append("4. Sektör çeşitlendirmesi ve risk limitleri")
    lines.append("5. Haftalık öz-eleştiri ve model güncelleme")
    init_log.write_text("\n".join(lines), encoding="utf-8")

    return portfolio