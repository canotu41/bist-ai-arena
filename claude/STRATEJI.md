# Claude BIST30 Strateji Dokümanı

Sürüm: v1 — 2026-07-03

## 1. Amaç ve felsefe

10.000 TL hipotetik sermaye ile BIST30 evreninde, disiplinli ve gerekçeli bir kağıt-üzeri
(paper trading) portföy yönetmek. Hedef: 52 hafta boyunca XU30 endeksini **risk-ayarlı** olarak
geçmek. Tek bir getiri yüzdesi değil, tutarlılık ve düşük hata önemlidir.

> Bu bir yatırım tavsiyesi değildir. Getiri garantisi yoktur. Gerçek emir gönderilmez.

## 2. Hisse evreni

BIST30. Likidite en yüksek, haber akışı en yoğun 30 şirket. Bu, hem veri güvenilirliğini hem de
gün içi giriş/çıkış varsayımlarının gerçekçiliğini artırır.

## 3. Skorlama modeli (0-100)

Her hisse üç eksende puanlanır, ağırlıklı toplam alınır:

| Eksen | Ağırlık | Neye bakar |
|---|---|---|
| Temel | %40 | F/K, PD/DD, net kâr ve ciro büyümesi, borçluluk, özkaynak kârlılığı, marj trendi |
| Teknik | %35 | Trend (50/200 gün OHO), momentum (RSI benzeri), hacim anomalisi, 52h yüksek/düşük konumu |
| Haber/katalist | %25 | KAP bildirimleri, bilanço sürprizi, sektör/makro haber önem skoru, pozitif/negatif ayrımı |

- 70+ : güçlü aday (alım için değerlendirilir)
- 50-70 : izleme
- <50 : uzak dur / sat adayı

## 4. Pozisyon ve risk kuralları

- Tek hissede **maksimum %20** sermaye.
- Her zaman **en az %10 nakit tamponu** korunur.
- Her pozisyon için giriş anında **stop** (tipik -%8/-%10) ve **hedef** tanımlanır.
- Portföy başına toplam açık risk sermayenin %6'sını aşmaz (stop'a göre hesap).
- İşlem maliyeti varsayımı: alım-satım başına **%0,2** (komisyon + kayma) düşülür.
- Gün içi al-sat yalnızca net katalist + teknik kırılım birlikte varsa yapılır; aksi halde swing tutulur.

## 5. Karar döngüsü (her kontrol noktası)

1. Son kontrolden bu yana KAP/haber taraması (WebSearch).
2. Fiyat/teknik durum güncellemesi, skorların yenilenmesi.
3. Açık pozisyonlarda stop/hedef kontrolü → gerekirse çıkış.
4. Yeni 70+ skor ve nakit varsa → boyutlandırılmış giriş.
5. Karar gerekçesi + kaynak + zaman damgası `log/` altına yazılır.
6. `portfolio.json` ve `claude.html` güncellenir.

## 6. Kıyas (benchmark)

- Birincil: **XU30** endeksi.
- İkincil: mevduat/para piyasası getirisi (risksiz kıyas).
- Kullanıcının kendi seçtiği portföy (haftalık yarışma).

## 7. Başarı metrikleri (52 hafta)

Toplam getiri • XU30'a göre fazla getiri (alfa) • Maksimum düşüş • Haftalık kazanma oranı •
İşlem isabet oranı • Sharpe benzeri risk-ayarlı skor • Stop/limit ihlali sayısı (disiplin).

## 8. Bilinen kısıtlar (dürüstlük notu)

- Gerçek zamanlı tick verisi yok; fiyatlar web aramasıyla gecikmeli/özet gelebilir. Giriş/çıkış
  fiyatları "kontrol anındaki en iyi bilinen fiyat" varsayımıyla işlenir.
- 52 hafta boyunca insansız 30dk'lık otomasyon için bulut rutini + kalıcı depo gerekir; bu sürüm
  local çalışır, güncellemeler manuel/oturum bazlı tetiklenir.
