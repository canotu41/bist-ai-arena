# Claude BIST AI Projesi

Bu klasör Claude'un BIST haber, bilanço, teknik analiz ve haftalık yarışma projesi için çalışma alanıdır.

## Çalışma ilkeleri

- Getiri garantisi yoktur; sistem karar destek, analiz ve paper trading odaklidir.
- Gerçek para ile emir gönderimi yoktur ve olmayacaktır.
- Her sinyal gerekçe, veri kaynağı, risk, iptal koşulu ve performans sonucu ile kaydedilir.
- Diğer yapay zekalar kendi klasörlerinde çalışır (bkz. `../codex/`); bu klasördeki tüm dosyalar Claude'a aittir.

## İlk hedef

BIST 30 için seans saatlerinde (10:00-18:00 İstanbul) düzenli aralıklarla haber, KAP ve fiyat/teknik gösterge taraması yapmak; 10.000 TL hipotetik sermaye ile kağıt üzerinde portföy yönetmek ve haftalık raporla performansı ölçmek.

## İçerik

- `PROJE_PLANI.md` — kapsam, yöntem ve platform kısıtları
- `portfolio.json` — güncel hipotetik portföy durumu
- `log/` — her kontrol noktasında alınan kararların gerekçeli kaydı
- `raporlar/` — haftalık performans raporları
