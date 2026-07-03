# BIST AI Arena — Orchestrator

4 yapay zekayı (claude, codex, deepseek, microsoft) tek bir dashboard'da
birleştirir, ortak (konsensüs) hisseleri araştırır ve **5. yarışmacı** olarak
bir *Konsensüs (Claude)* paper portföyü yönetir.

## Ne üretir?

- **`../dashboard.html`** — tek birleşik panel: liderlik tablosu, **canlı işlem
  akışı**, konsensüs hisseleri, Claude araştırma paneli, tüm portföyler.
- **`data/consensus_portfolio.json`** — 5. yarışmacının (Konsensüs) durumu.
- **`data/snapshot.json`** — deepseek analiz motorunun anlık BIST30 görüntüsü.
- **`data/last_run.json`** — her döngünün heartbeat özeti.

## Bir döngü çalıştır

```bash
python3 orchestrator/run.py
```

Sırasıyla: deepseek + microsoft motorlarını ilerletir → analiz anlık görüntüsünü
alır → 4 AI'ı normalize eder → 2+ AI'ın ortak seçtiği hisseleri bulur →
Konsensüs portföyünü kurar/günceller (stop -%8 / hedef +%20) → araştırma notları
üretir → `dashboard.html`'i yeniden yazar. Salt stdlib, harici bağımlılık yok.

## Otomasyon

### Seçenek A — Şimdi lokalde çalışsın (macOS launchd/cron)
Seans içi (hafta içi 10:00–18:00 İstanbul) her 30 dk'da bir çalıştırmak için
crontab satırı:

```
*/30 10-17 * * 1-5  cd "<PROJE_YOLU>" && /usr/bin/python3 orchestrator/run.py >> orchestrator/data/cron.log 2>&1
```

### Seçenek B — Tam bulut (zamanlanmış Claude ajanı) — hedef mimari
1. Depoyu GitHub'a gönder (bulut ajanının koda erişmesi için gerekli).
2. Bir cron rutini kur: her döngüde `python3 orchestrator/run.py` çalıştırıp
   `dashboard.html` + `data/*` değişikliklerini commit/push eder.
3. Bulut rutini min. periyodu 1 saat; 30 dk kapsama için `:00` ve `:30`
   dakikalarında iki rutin kurulur (projenin PROJE_PLANI.md notuyla uyumlu).

## Kısıtlar / dürüstlük notu

- Fiyatlar şu an **simüle** (deepseek örnek verisi). Gerçek BIST akışı ya da
  DeepSeek API bağlanınca P&L canlanır.
- Yatırım tavsiyesi değildir; gerçek emir gönderilmez.
- AI muhakemesi abonelik (Claude) üzerinden; API kullanılmaz — tek istisna
  DeepSeek. Kantitatif katman (konsensüs, skorlama) API'siz, her yerde çalışır.
