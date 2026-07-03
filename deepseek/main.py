#!/usr/bin/env python3
"""DeepSeek BIST30 AI Portföy Yönetim Sistemi - Ana Çalıştırıcı

Kullanım:
    python main.py init          # İlk portföyü oluştur
    python main.py cycle         # Bir karar döngüsü çalıştır
    python main.py simulate      # 52 haftalık simülasyon
    python main.py dashboard     # HTML dashboard oluştur
    python main.py report        # Haftalık rapor oluştur
    python main.py leaderboard   # Yarışma sıralaması göster
    python main.py all           # Tüm işlemleri sırayla yap
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# src dizinini Python yoluna ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.portfolio_manager import (
    initialize_portfolio, execute_cycle, load_portfolio,
    save_portfolio,
)
from src.simulation import run_52_week_simulation, quick_simulation_report
from src.competition import save_leaderboard, generate_weekly_report
from src.signal_generator import scan_all_companies, get_top_picks
from src.news_tracker import get_overall_market_sentiment


def cmd_init():
    """İlk portföyü oluştur"""
    print("🚀 DeepSeek BIST30 Portföyü oluşturuluyor...")
    portfolio = initialize_portfolio()
    print(f"✅ Portföy oluşturuldu!")
    print(f"   Başlangıç Sermayesi: {portfolio.initial_capital:,.0f} TL")
    print(f"   Yatırılan: {sum(p.cost_basis for p in portfolio.positions):,.2f} TL")
    print(f"   Nakit: {portfolio.cash:,.2f} TL")
    print(f"   Hisse Sayısı: {len(portfolio.positions)}")
    print(f"\n📋 Seçilen Hisseler:")
    for pos in portfolio.positions:
        print(f"   - {pos.ticker} ({pos.company_name}) | {pos.sector} | {pos.quantity} adet @ {pos.entry_price:.2f} TL")


def cmd_cycle():
    """Bir karar döngüsü çalıştır"""
    print("🔄 DeepSeek karar döngüsü başlatılıyor...")
    market = get_overall_market_sentiment()
    print(f"   Piyasa Duyarlılığı: {market['score']:.1f}/100 ({market['trend']})")

    portfolio = execute_cycle()

    print(f"\n✅ Döngü tamamlandı!")
    print(f"   Portföy Değeri: {portfolio.total_value:,.2f} TL")
    print(f"   Getiri: %{portfolio.total_return_pct:+.2f}")
    print(f"   Piyasa Rejimi: {portfolio.market_regime.value}")
    print(f"   Açık Pozisyon: {len(portfolio.positions)}")

    # Son işlemleri göster
    recent_tx = portfolio.transactions[-3:] if portfolio.transactions else []
    if recent_tx:
        print(f"\n📊 Son İşlemler:")
        for tx in recent_tx:
            print(f"   - [{tx.type}] {tx.ticker} x{tx.quantity} @ {tx.price:.2f} TL | {tx.reason[:60]}")


def cmd_simulate():
    """52 haftalık simülasyon"""
    print("🎲 52 Haftalık Monte Carlo Simülasyonu başlatılıyor...")
    print("   (Bu işlem birkaç saniye sürebilir)\n")
    report = quick_simulation_report()
    print(report)

    # Simülasyon sonucunu HTML olarak da kaydet
    from src.generate_dashboard import generate_dashboard_html
    portfolio = load_portfolio()
    html = generate_dashboard_html(portfolio, scan_all_companies(), save_leaderboard())
    dashboard_path = Path(__file__).resolve().parent / "deepseek.html"
    dashboard_path.write_text(html, encoding="utf-8")
    print(f"\n📊 Dashboard güncellendi: {dashboard_path}")


def cmd_dashboard():
    """Dashboard oluştur"""
    print("📊 DeepSeek Dashboard oluşturuluyor...")
    from src.generate_dashboard import generate_dashboard_html

    portfolio = load_portfolio()
    snapshots = scan_all_companies()
    leaderboard = save_leaderboard()

    html = generate_dashboard_html(portfolio, snapshots, leaderboard)
    dashboard_path = Path(__file__).resolve().parent / "deepseek.html"
    dashboard_path.write_text(html, encoding="utf-8")

    print(f"✅ Dashboard oluşturuldu!")
    print(f"   Dosya: {dashboard_path}")
    print(f"   Tarayıcıda açmak için: open {dashboard_path}")


def cmd_report():
    """Haftalık rapor"""
    print("📝 Haftalık rapor oluşturuluyor...")
    portfolio = load_portfolio()
    report = generate_weekly_report(portfolio)
    print(report)

    # Raporu dosyaya kaydet
    log_dir = Path(__file__).resolve().parent / "log"
    log_dir.mkdir(exist_ok=True)
    from datetime import datetime
    report_file = log_dir / f"haftalik_rapor_{datetime.now().strftime('%Y-%m-%d')}.md"
    report_file.write_text(report, encoding="utf-8")
    print(f"\n📁 Rapor kaydedildi: {report_file}")


def cmd_leaderboard():
    """Yarışma sıralaması"""
    print("🏆 BIST30 AI Yarışması - Güncel Sıralama")
    print("=" * 50)
    leaderboard = save_leaderboard()
    print(f"Hafta: {leaderboard['week']} | Tarih: {leaderboard['date']}")
    print(f"XU30 Getirisi: %{leaderboard['xu30_return']:+.2f}")
    print("-" * 50)

    for comp in leaderboard["competitors"]:
        rank_emoji = comp.get("medal", "")
        print(f"{rank_emoji} #{comp['rank']} {comp['name']}: %{comp['return']:+.2f} (Alfa: %{comp.get('alpha', 0):+.2f}) | Portföy: {comp['portfolio_value']:,.2f} TL")
    print("=" * 50)


def cmd_top_picks():
    """En iyi hisse önerileri"""
    print("🎯 DeepSeek DeepScore™ En İyi 10 Hisse")
    print("=" * 70)
    picks = get_top_picks(10)
    print(f"{'Sıra':<5} {'Hisse':<8} {'Şirket':<25} {'Sektör':<18} {'DeepScore™':<12} {'Sinyal':<14}")
    print("-" * 70)
    for i, snap in enumerate(picks, 1):
        signal_emoji = {"STRONG_BUY": "🟢", "BUY": "🟢", "HOLD": "🟡", "WEAK_HOLD": "🟠", "SELL": "🔴", "STRONG_SELL": "🔴"}
        emoji = signal_emoji.get(snap.signal.value, "⚪")
        print(f"{i:<5} {snap.ticker:<8} {snap.company_name:<25} {snap.sector:<18} {snap.deepscore:<12.1f} {emoji} {snap.signal.value:<12}")

    print("-" * 70)
    print("\n📊 Skor Kırılımı (ilk 5):")
    for snap in picks[:5]:
        print(f"  {snap.ticker}: ", end="")
        for axis, score in snap.score_breakdown.items():
            print(f"{axis}={score:.0f} ", end="")
        print()


def cmd_all():
    """Tüm işlemleri sırayla yap"""
    cmd_init()
    print("\n" + "=" * 60 + "\n")
    cmd_top_picks()
    print("\n" + "=" * 60 + "\n")
    cmd_cycle()
    print("\n" + "=" * 60 + "\n")
    cmd_leaderboard()
    print("\n" + "=" * 60 + "\n")
    cmd_dashboard()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    commands = {
        "init": cmd_init,
        "cycle": cmd_cycle,
        "simulate": cmd_simulate,
        "dashboard": cmd_dashboard,
        "report": cmd_report,
        "leaderboard": cmd_leaderboard,
        "top": cmd_top_picks,
        "all": cmd_all,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Bilinmeyen komut: {command}")
        print(f"Kullanılabilir komutlar: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()