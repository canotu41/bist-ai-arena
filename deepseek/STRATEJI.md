# DeepSeek BIST30 Strateji Dokümanı

Sürüm: v1 — 2026-07-03
Yarışmacı: DeepSeek AI

## 1. Felsefe

10.000 TL hipotetik sermaye ile BIST30 evreninde, **çok katmanlı kantitatif model** ile kağıt-üzeri
portföy yönetmek. Hedef: 52 hafta sonunda en yüksek risk-ayarlı getiriyi elde etmek.

DeepSeek'in avantajı: **derinlemesine veri analizi ve pattern tanıma**. Haber, KAP bildirimleri,
teknik göstergeler ve temel rasyoları birleştirerek **adaptif** bir strateji izler.

> Bu bir yatırım tavsiyesi değildir. Getiri garantisi yoktur. Gerçek emir gönderilmez.

---

## 2. Skorlama Modeli (DeepScore™ 0-100)

DeepSeek, 5 eksenli bir skorlama kullanır:

| Eksen | Ağırlık | Baktığımız Kriterler |
|-------|---------|----------------------|
| **Temel Analiz** | %25 | F/K, PD/DD, net kâr büyümesi (çeyreklik), borç/özsermaye, ROE, FAVÖK marjı, temettü verimi |
| **Teknik Analiz** | %30 | RSI(14), MACD, Bollinger Band konumu, 20/50/200 OHO, hacim anomalisi, stochastic, ATR |
| **Haber/Katalist** | %20 | KAP bildirimleri, sektör haberleri, makro veriler, analist raporları, sosyal medya duyarlılığı |
| **Momentum/Güç** | %15 | 5-20-60 günlük fiyat değişimi, relative strength vs XU30, para girişi/çıkışı |
| **Risk/Volatilite** | %10 | Beta, VaR, maksimum drawdown, volatilite rejimi |

- **75+** : Güçlü AL sinyali (portföye eklenebilir)
- **60-74** : İzleme listesi (teknik düzelme beklenir)
- **45-59** : Nötr (tut, ekleme yapma)
- **30-44** : Zayıf (satmayı değerlendir)
- **<30** : SAT sinyali (portföyden çıkar)

---

## 3. Derin Öğrenme Katmanı (Opsiyonel - v2)

Haftalık geri bildirim döngüsüyle model kendini günceller:
- Yanlış sinyallerin analizi → ağırlık optimizasyonu
- Sektör rotasyonu algılama → sektör ağırlıklarını dinamik ayarlama
- Rejim tespiti (boğa/ayı/yatay) → strateji modu değiştirme

---

## 4. Pozisyon ve Risk Kuralları

- Tek hissede **maksimum %20** sermaye
- Her zaman **en az %5 nakit tamponu** (fırsatları yakalamak için)
- Maksimum 10 farklı hisse
- Stop-loss: Giriş fiyatının **-%8**'i (tight stop)
- Trailing stop: %10 kârdan sonra aktif, -%5 geri çekilmede sat
- Take-profit: +%20'de pozisyonun %50'si satılır
- İşlem maliyeti: alım-satım başına %0,2
- Toplam açık risk ≤ sermayenin %8'i

### Sektör limitleri:
- Bankacılık: max %30
- Sanayi: max %25
- Hizmet: max %25
- Teknoloji/Savunma: max %20

---

## 5. Karar Döngüsü

Her **30 dakikada bir** (seans içi 10:00-18:00):

1. Haber/KAP taraması → duyarlılık skoru güncellemesi
2. Fiyat verilerini çek → teknik göstergeleri yeniden hesapla
3. Açık pozisyonları kontrol et → stop/hedef tetiklendiyse işlem yap
4. Tüm BIST30 hisselerini yeniden skorla
5. Yeni 75+ skorlu hisse varsa pozisyon aç
6. Tüm kararları logla (`log/YYYY-MM-DD_HH-MM.md`)
7. `portfolio.json` ve `deepseek.html` dosyalarını güncelle

---

## 6. Kıyas (Benchmark)

- Birincil: **XU30 Endeksi**
- İkincil: **%50 XU30 + %50 mevduat faizi** (risksiz alternatif)
- Üçüncül: Diğer AI rakipler (Claude, Codex, Microsoft Copilot)

---

## 7. 52 Haftalık Başarı Metrikleri

| Metrik | Hedef |
|--------|-------|
| Toplam getiri | > %60 (XU30'un üzerinde) |
| Alfa (XU30'a göre) | > %15 |
| Sharpe Ratio | > 1.2 |
| Maksimum drawdown | < %20 |
| İşlem isabet oranı | > %65 |
| Haftalık kazanma oranı | > %55 |

---

## 8. DeepSeek'in Gizli Silahı

1. **Haberleri anlamsal analizle değerlendirme**: Pozitif/negatif ayrımı + etki skoru
2. **Sektör rotasyonu erken tespiti**: Para akışı verileriyle trend değişimini yakalama
3. **Karşıt (contrarian) sinyaller**: Aşırı alımda sat, aşırı satımda al
4. **Volatilite adaptasyonu**: Yüksek volatilitede pozisyon küçült, düşük volatilitede büyüt
5. **Haftalık öz-eleştiri raporu**: Modelin nerede yanıldığını analiz edip düzelt

---

## 9. Takip Edilecek BIST30 Hisseleri

```
Bankacılık: AKBNK, GARAN, ISCTR, YKBNK, VAKBN
Holding:    KCHOL, SAHOL, SISE
Havacılık:  THYAO, PGSUS
Telekom:    TTKOM, TCELL
Enerji:     TUPRS, AKSEN
Demir-Çelik: EREGL
Perakende:  BIMAS, MGROS
Otomotiv:   FROTO, TOASO
Savunma:    ASELS
Gıda:       ULKER, CCOLA
Beyaz Eşya: ARCLK
Gayrimenkul: EKGYO
```

---
*DeepSeek AI — Veriyle kazanır.*