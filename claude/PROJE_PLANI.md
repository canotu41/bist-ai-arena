# Claude BIST AI Analiz ve Haftalık Yarışma Projesi

## Amaç

BIST30 hisseleri için haber, KAP bildirimi, temel ve teknik göstergeleri düzenli aralıklarla tarayan;
bunlardan hipotetik (kağıt üzerinde) bir portföy yöneten ve haftalık performansı XU30 karşısında ölçen
bir karar destek sistemi.

Bu proje getiri garantisi vermez, yatırım danışmanlığı değildir ve gerçek para ile emir göndermez.

## Kapsam (v1)

- Evren: BIST30
- Başlangıç sermayesi: 10.000 TL (hipotetik)
- Seans penceresi: 10:00-18:00 İstanbul (hafta içi)
- Karar döngüsü: seans içinde düzenli kontrol noktaları + haftalık özet rapor
- Karar biçimi: al / sat / tut, gerekçe, veri kaynağı, risk notu ve pozisyon boyutu ile birlikte loglanır
- Kıyas: XU30 endeksi, ve varsa kullanıcının kendi seçimleri

## Platform kısıtları (önemli)

Bu proje 52 hafta boyunca insan müdahalesi olmadan sürmesi gerektiği için tek uygun mekanizma
**bulut rutinleri** (RemoteTrigger / Claude cron routines). Yerel `CronCreate` mekanizması yalnızca
bu oturum içinde yaşar ve 7 gün sonra otomatik silinir — 52 haftalık bir proje için uygun değildir.

Bulut rutinlerinin iki kısıtı var:

1. **Minimum periyot 1 saattir**, tam 30 dakikalık aralık desteklenmiyor. Çözüm: aynı işi yapan iki
   rutün, biri `:00` biri `:30` dakikalarında tetiklenecek şekilde kurulup birlikte gerçek 30 dakikalık
   kapsama sağlanabilir.
2. **Bulut oturumlarının yerel diske erişimi yoktur.** Portföy durumu ve loglar oturumlar arasında
   kalıcı olmalı, bu da bir Git deposu (GitHub) gerektirir — her çalışma depoyu çekip günceller ve
   commit/push eder. Bu proje henüz bir git deposu değil; kuruluma başlamadan önce bir depo
   oluşturulmalı veya mevcut bir depo bağlanmalıdır.

## Karar mantığı (her kontrol noktasında)

1. Son kontrolden bu yana BIST30 şirketleri için KAP/haber taraması (WebSearch)
2. Fiyat/hacim ve basit teknik durum değerlendirmesi (trend, RSI benzeri momentum okuması)
3. Açık pozisyonlar için stop/hedef kontrolü
4. Yeni fırsat varsa pozisyon boyutlandırma (tek hissede max %20 sermaye, nakit tamponu korunur)
5. Kararın gerekçesi, kaynağı ve zaman damgası `log/` altına yazılır
6. `portfolio.json` güncellenir

## Haftalık rapor içeriği

- Dönem başı/sonu portföy değeri, getiri %
- XU30 karşısında fazla getiri
- Yapılan işlemler ve isabet durumu
- Haftanın öne çıkan gerekçe hataları ("ne yanıldı, neden yanıldı")
- Bir sonraki hafta için izleme listesi

## Risk çerçevesi

- Kesin getiri vaadi yok.
- Gerçek para ile otomatik emir yok, olmayacak.
- Her sinyal veri kaynağı ve zaman damgası ile saklanır.
