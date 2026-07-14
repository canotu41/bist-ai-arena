# BIST AI Arena — Backtest & Kriter Kalibrasyonu

## Neden
Stratejilerin değerlendirme kriterleri (ağırlık/eşik/filtre/stop-hedef) başta elle
seçilmişti; hiç backtest edilmemişti. Bu belge, kriterleri **2 yıllık gerçek geçmiş
veriyle** sınayıp kalibre etme çalışmasını özetler.

## Yöntem
- **Veri:** Yahoo Finance, BIST30 + XU100 endeksi, ~2 yıl (~500 işlem günü), günlük.
- **Skor yeniden kurma:** Her geçmiş gün için teknik/momentum/risk bileşen skorları,
  canlı sistemle **AYNI fonksiyonlarla** (`deepseek/src`) o güne kadarki fiyat
  penceresinden hesaplandı.
- **Simülasyon:** Her strateji 50.000 TL'den, kendi skoru + filtresi + stop/hedef/eşik
  kurallarıyla gün gün oynatıldı; %0,2 işlem maliyeti. Ölçülenler: toplam getiri,
  XU100'e karşı alfa, maksimum düşüş, isabet oranı, işlem sayısı.
- **Kalibrasyon:** (1) Al eşiği, her stratejinin gerçek skor **dağılımının ~85.
  yüzdeliğine** oturtuldu (seçicilik). (2) Çıkış eşiği düşük (40) → nadir skor-çıkışı.
  (3) Stop/hedef küçük ızgara taramasıyla (stop {-10,-12,-15%}, hedef {+30,+40,tavan-yok})
  getiriyi enbüyükleyen seçildi. Kimlik (ağırlıklar/filtreler) korundu.

## Ana bulgu (dürüst)
- **Eski (keyfi) kriterler değer yok ediyordu:** 2 yılda claude -%13, codex +%2,
  microsoft +%21, deepseek %0 (bar 72 hiç ulaşılamadı) — hepsi XU100'ün (**+%46**)
  çok altında. Sıkı stop + sık skor-çıkışı, yükselen piyasada kazananları erken satıp
  trendi kaçırıyordu.
- **Kalibre kriterler ("seçici al + uzun tut"):** microsoft +%44 (alfa ~-%1),
  deepseek +%39, codex +%26, claude +%19. Hâlâ güçlü boğa endeksini yenmiyorlar
  (gerçekçi) ama artık değer yok etmiyor, endeksi makul takip ediyor, düşüş kontrollü.

## Uygulanan kalibre kriterler
| AI | Al eşiği | Sat | Stop | Hedef |
|----|----|----|----|----|
| Claude | 65 | 40 | -%10 | tavan yok |
| Codex | 62 | 40 | -%10 | +%40 |
| Microsoft | 70 | 40 | -%10 | +%40 |
| DeepSeek | 62 | 40 | -%10 | +%35 |

Ek: F/K skorlama aralığı gerçek BIST'e çekildi ve aykırı F/K (negatif/>60, ör. EREGL
598) sınırlandı; benchmark artık **gerçek canlı XU100**.

## Kısıtlar
- Geçmiş **temel veri güncel-sabit**, **haber nötr (50)** tutuldu (ücretsiz geçmiş yok)
  → backtest ağırlıkla teknik/momentum/risk + giriş-çıkış mekaniğini doğrular; temel/haber
  eksenleri yalnız dağılım + sağlamlaştırmayla kalibre edildi.
- Kalibrasyon **in-sample** (aynı 2 yıl) → aşırı-uyum riski vardır; ileriye dönük
  güvenlik için her stratejide **her zaman bir stop** bırakıldı.
- Bu bir **eğitim/simülasyon** çalışmasıdır; yatırım tavsiyesi değildir.

Güncel sonuçlar: `orchestrator/data/backtest_results.json` ve dashboard "Kriterler" paneli.
Yeniden çalıştırma: `python3 orchestrator/backtest.py`.
