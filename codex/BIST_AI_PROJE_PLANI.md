# BIST AI Analiz ve Haftalik Yarisma Projesi

## Amac

Borsa Istanbul hisseleri icin haber, KAP bildirimi, finansal tablo, fiyat/hacim ve teknik gostergeleri duzenli toplayan; bunlardan puanlama, izleme listesi, risk kontrollu sinyal ve haftalik performans yarismasi uretebilen bir karar destek sistemi kurmak.

Bu proje getiri garantisi vermez ve otomatik yatirim danismanligi gibi konumlanmaz. Amac; veriyi hizli okumak, disiplinli analiz yapmak, hipotezleri backtest/paper trading ile olcmek ve insan onayli karar surecini iyilestirmektir.

## Cekirdek Moduller

1. Veri toplama
   - KAP finansal tablolar, ozel durum aciklamalari ve temettu/sermaye islemleri
   - BIST fiyat, hacim, endeks ve gunluk bulten verileri
   - Sirket haberleri, makro haberler, sektor haberleri
   - TCMB faiz, kur, enflasyon ve makro veri takvimi

2. Temel analiz
   - Gelir, FAVOK, net kar, marjlar, borcluluk, ozkaynak karliligi
   - Ceyreklik ve yillik buyume karsilastirmalari
   - Sektor icinde goreli degerleme
   - Bilanco kalitesi ve tek seferlik gelir/gider bayraklari

3. Teknik analiz
   - Trend, momentum, volatilite, hacim anomalisi
   - RSI, MACD, hareketli ortalamalar, ATR, destek/direnc
   - 52 hafta yuksek/dusuk, likidite ve gap kontrolleri

4. Haber ve duygu analizi
   - Haberleri ve KAP aciklamalarini sirket/sektor/makro etkisine gore siniflandirma
   - Onem skoru, pozitif/negatif/notr ayrimi
   - Benzer gecmis olaylarin fiyat etkisi analizi

5. Sinyal ve risk motoru
   - Al/sat demek yerine puan, gerekce ve risk seviyesi uretir
   - Pozisyon boyutu, maksimum zarar, stop, hedef ve sure varsayimlari
   - Islem maliyeti, spread ve kayma hesabi

6. Backtest ve paper trading
   - Stratejilerin gecmis performans testi
   - Canli piyasada sanal portfoy ile takip
   - Benchmark: XU100, XU030, mevduat/faiz ve secilecek fonlar

7. Dashboard ve yarisma
   - 30 dakikada bir veri yenileme
   - Gun ici radar: haber, hacim, teknik kirilim, bilanco etkisi
   - Haftalik portfoy yarismasi: AI listesi, kullanici listesi, benchmark
   - Performans: getiri, maksimum dusus, isabet orani, risk/getiri

## MVP Kapsami

Ilk surumda hedef:

- BIST 30 veya BIST 50 ile baslamak
- Gunde 30 dakikada bir KAP ve fiyat/hacim taramasi
- Gunluk temel + teknik puan tablosu
- Haftalik 5-10 hisselik sanal portfoy onerisi
- Her oneride gerekce, risk, stop/izleme kosulu ve iptal kosulu
- Haftalik rapor: ne tuttu, ne yanildi, neden yanildi

## Teknoloji Onerisi

- Backend: Python, FastAPI
- Veri isleme: pandas, polars, numpy
- Teknik analiz: pandas-ta veya ta
- Zamanlayici: APScheduler veya cron
- Veritabani: PostgreSQL, zaman serisi icin TimescaleDB opsiyonel
- Cache/kuyruk: Redis
- Dashboard: Next.js veya Streamlit
- Raporlama: Markdown, PDF, e-posta/Telegram bildirimi

## Risk ve Hukuki Cerceve

- Sistem kesin getiri vaadi vermez.
- Gercek para ile otomatik emir gonderimi ilk fazda yoktur.
- Ilk asama paper trading ve insan onayli takip olmalidir.
- SPK mevzuati ve yetkili yatirim danismanligi sinirlari dikkate alinmalidir.
- Her sinyal icin veri kaynagi, zaman damgasi ve gerekce saklanmalidir.

## 52 Haftalik Basari Olcumu

Basari tek bir getiri yuzdesiyle degil, su metriklerle olculur:

- Toplam getiri
- XU100 ve XU030'a gore fazla getiri
- Maksimum dusus
- Haftalik kazanma orani
- Sharpe/Sortino benzeri risk ayarli skor
- Islem basi ortalama kar/zarar
- Haber/bilanco sinyali isabeti
- Disiplin skoru: stop ve pozisyon limiti ihlali

## Ilk 4 Hafta Yol Haritasi

1. Hafta
   - Veri kaynaklari ve sembol evreni netlestirme
   - KAP/fiyat/haber toplayici prototipi
   - Basit teknik gosterge tablosu

2. Hafta
   - Finansal tablo alanlari ve temel analiz puanlari
   - Haber/KAP onem skoru
   - Ilk dashboard

3. Hafta
   - Backtest motoru
   - Paper trading portfoyu
   - Haftalik yarisma raporu

4. Hafta
   - Risk motoru
   - Alarm sistemi
   - Strateji karsilastirma ve iyilestirme dongusu

