"""Şirket-işlemi (bölünme / bedelsiz / büyük temettü) koruması.

Neden güvenli: BIST'te günlük fiyat marjı dardır (çoğu hissede ±%10 civarı).
Bu yüzden bir hissenin TEK döngüde |değişimi| ~%25'i aşıyorsa bu GERÇEK bir
alım-satım hareketi OLAMAZ; bölünme/bedelsiz ya da veri sıçramasıdır.

Böyle bir durumda pozisyonun bazları (giriş, stop, hedef, adet) oranla yeniden
ölçeklenir → değer ve K/Z sürekliliği korunur, sahte stop-loss VEYA sahte kâr
oluşmaz. 52 haftalık en büyük veri-bütünlüğü riski budur.
"""
from __future__ import annotations

from typing import Optional

# Tek döngü değişim eşiği: bu bandın dışı = şirket işlemi/sıçrama
LOW = 0.75    # yeni/eski < 0.75  (>%25 düşüş: örn. %100 bedelsiz ≈ -%50)
HIGH = 1.30   # yeni/eski > 1.30  (ters split vb.)


def anomaly_ratio(old_price: float, new_price: float) -> Optional[float]:
    """Fiyat sıçraması varsa oran (yeni/eski), yoksa None."""
    try:
        old_price = float(old_price)
        new_price = float(new_price)
    except (TypeError, ValueError):
        return None
    if old_price <= 0 or new_price <= 0:
        return None
    r = new_price / old_price
    if r < LOW or r > HIGH:
        return r
    return None


def adjust(pos: dict, r: float, entry="entry", qty="qty",
           stop="stop", target="target") -> None:
    """Pozisyon bazlarını r oranıyla yeniden ölçekle (değer/K-Z sürekliliği)."""
    if pos.get(entry):
        pos[entry] = round(pos[entry] * r, 4)
    if pos.get(stop):
        pos[stop] = round(pos[stop] * r, 4)
    if pos.get(target):
        pos[target] = round(pos[target] * r, 4)
    if pos.get(qty):
        pos[qty] = round(pos[qty] / r, 4)  # split: fiyat yarılır, adet ikiye katlanır


def note(ticker: str, r: float) -> str:
    kind = "bölünme/bedelsiz" if r < 1 else "ters-split/düzeltme"
    return f"⚠ ŞİRKET İŞLEMİ ({kind}) algılandı ({ticker}): bazlar ×{r:.3f} ayarlandı, stop tetiklenmedi"
