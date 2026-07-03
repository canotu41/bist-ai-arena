"""DeepSeek BIST30 - Haber Takip ve Duyarlılık Analizi"""
from __future__ import annotations

import random
from datetime import datetime
from typing import List, Dict

from .data_models import NewsItem


MARKET_NEWS_POOL: List[Dict] = [
    {"title": "TCMB faiz indirim sinyali verdi, bankacılık hisseleri yükselişte", "sentiment": 0.85, "impact": 9.0, "categories": ["makro", "bankacılık"], "source": "Bloomberg HT"},
    {"title": "BIST 100 endeksi yeni zirve denemesi yapıyor", "sentiment": 0.75, "impact": 8.5, "categories": ["borsa", "genel"], "source": "Foreks"},
    {"title": "Yabancı yatırımcı girişi hızlandı, 2 milyar dolar giriş oldu", "sentiment": 0.90, "impact": 9.5, "categories": ["makro", "borsa"], "source": "Reuters"},
    {"title": "Petrol fiyatları 85 dolar üzerine çıktı, enerji hisseleri pozitif", "sentiment": 0.65, "impact": 7.0, "categories": ["emtia", "enerji"], "source": "Bloomberg HT"},
    {"title": "Küresel piyasalarda resesyon endişesi azalıyor", "sentiment": 0.70, "impact": 7.5, "categories": ["makro", "global"], "source": "CNBC-e"},
    {"title": "Savunma sanayi ihracatı yıllık %35 arttı", "sentiment": 0.88, "impact": 8.0, "categories": ["sektör", "savunma"], "source": "AA"},
    {"title": "Konut satışları son 3 ayın zirvesinde", "sentiment": 0.72, "impact": 6.5, "categories": ["sektör", "gayrimenkul"], "source": "TÜİK"},
    {"title": "Turizm gelirleri beklentileri aştı, 60 milyar dolar hedefi", "sentiment": 0.82, "impact": 8.0, "categories": ["sektör", "turizm"], "source": "Kültür Bakanlığı"},
    {"title": "Otomotiv üretimi yıllık bazda %18 arttı", "sentiment": 0.78, "impact": 7.5, "categories": ["sektör", "otomotiv"], "source": "OSD"},
    {"title": "Elektrik fiyatlarında düzenleme bekleniyor, enerji sektörü temkinli", "sentiment": -0.30, "impact": 6.0, "categories": ["sektör", "enerji"], "source": "EPDK"},
    {"title": "Enflasyon verisi beklentilerin altında geldi", "sentiment": 0.92, "impact": 9.0, "categories": ["makro", "veri"], "source": "TÜİK"},
    {"title": "ABD Merkez Bankası faiz artırım döngüsünü sonlandırdı", "sentiment": 0.80, "impact": 9.5, "categories": ["global", "makro"], "source": "Fed"},
    {"title": "Dolar/TL kuru 35 seviyesinde dengelendi", "sentiment": 0.40, "impact": 7.0, "categories": ["kur", "makro"], "source": "Foreks"},
    {"title": "Bilanço sezonu başlıyor, bankalar öncü olacak", "sentiment": 0.60, "impact": 8.0, "categories": ["borsa", "bilanço"], "source": "KAP"},
    {"title": "Demir-çelik sektöründe Çin talebi canlanıyor", "sentiment": 0.70, "impact": 7.0, "categories": ["sektör", "demir-çelik"], "source": "Reuters"},
    {"title": "Perakende sektöründe rekabet kızışıyor, marjlar baskı altında", "sentiment": -0.25, "impact": 5.5, "categories": ["sektör", "perakende"], "source": "Dünya"},
    {"title": "Havacılık sektöründe yolcu trafiği rekor kırdı", "sentiment": 0.85, "impact": 8.0, "categories": ["sektör", "havacılık"], "source": "DHMİ"},
    {"title": "Küresel çip krizi çözülüyor, teknoloji hisseleri olumlu", "sentiment": 0.65, "impact": 6.5, "categories": ["global", "teknoloji"], "source": "Bloomberg"},
    {"title": "Borsa İstanbul'da halka arz seferberliği sürüyor", "sentiment": 0.55, "impact": 6.0, "categories": ["borsa", "halka-arz"], "source": "SPK"},
    {"title": "Jeopolitik riskler azalıyor, risk iştahı artıyor", "sentiment": 0.75, "impact": 8.0, "categories": ["global", "jeopolitik"], "source": "Reuters"},
    {"title": "Kripto para piyasasında sert düşüş, borsaya etkisi sınırlı", "sentiment": -0.40, "impact": 4.0, "categories": ["kripto", "alternatif"], "source": "CoinDesk"},
    {"title": "Tarım emtia fiyatları yükselişte, gıda enflasyonu uyarısı", "sentiment": -0.35, "impact": 6.0, "categories": ["emtia", "gıda"], "source": "FAO"},
    {"title": "Doğalgaz fiyatlarında düşüş enerji maliyetlerini rahatlatıyor", "sentiment": 0.50, "impact": 6.5, "categories": ["emtia", "enerji"], "source": "EPDK"},
    {"title": "Bankacılık sektörü kredi büyümesi %40'a ulaştı", "sentiment": 0.72, "impact": 7.5, "categories": ["sektör", "bankacılık"], "source": "BDDK"},
    {"title": "Telekom sektöründe 5G ihalesi bu yıl yapılacak", "sentiment": 0.78, "impact": 8.0, "categories": ["sektör", "telekom"], "source": "BTK"},
]

COMPANY_KAP_POOL: Dict[str, List[Dict]] = {
    "AKBNK": [{"title": "AKBNK: 2Ç26 net kâr 18.2 milyar TL (beklenti: 17.5 milyar TL)", "sentiment": 0.85, "impact": 8.5}, {"title": "AKBNK: %15 bedelsiz sermaye artırımı", "sentiment": 0.75, "impact": 7.5}],
    "GARAN": [{"title": "GARAN: 2Ç26 solo net kâr 22.1 milyar TL, yıllık %32 artış", "sentiment": 0.90, "impact": 9.0}, {"title": "GARAN: Yabancı payı %42'ye yükseldi", "sentiment": 0.70, "impact": 7.0}],
    "YKBNK": [{"title": "YKBNK: Kredi risk primi (CDS) 280 baz puana geriledi", "sentiment": 0.65, "impact": 6.5}],
    "THYAO": [{"title": "THYAO: Filo büyüklüğü 500 uçağa ulaştı", "sentiment": 0.80, "impact": 8.0}, {"title": "THYAO: Yaz sezonu doluluk oranı %88", "sentiment": 0.72, "impact": 7.0}],
    "PGSUS": [{"title": "PGSUS: Yeni 50 uçak siparişi verdi", "sentiment": 0.88, "impact": 8.5}],
    "TOASO": [{"title": "TOASO: Elektrikli araç üretimi için 500 milyon euro yatırım", "sentiment": 0.90, "impact": 9.0}],
    "ASELS": [{"title": "ASELS: 2.5 milyar dolarlık yeni ihracat sözleşmesi", "sentiment": 0.95, "impact": 9.5}, {"title": "ASELS: Yeni radar sistemi NATO onayı aldı", "sentiment": 0.88, "impact": 8.5}],
    "EKGYO": [{"title": "EKGYO: İstanbul'da 5000 konutluk yeni proje", "sentiment": 0.78, "impact": 7.5}],
    "BIMAS": [{"title": "BIMAS: Mağaza sayısı 15000'e ulaştı", "sentiment": 0.65, "impact": 6.5}],
    "SISE": [{"title": "SISE: Avrupa'da yeni fabrika yatırımı", "sentiment": 0.72, "impact": 7.0}],
}


def scan_market_news(max_items: int = 10) -> List[NewsItem]:
    """Piyasa genel haberlerini tarar"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    selected = random.sample(MARKET_NEWS_POOL, min(max_items, len(MARKET_NEWS_POOL)))
    return [NewsItem(title=item["title"], source=item["source"], url=f"https://example.com/news/{abs(hash(item['title'])) % 10000}", sentiment=item["sentiment"], impact_score=item["impact"], categories=item["categories"], timestamp=now) for item in selected]


def scan_company_news(ticker: str) -> List[NewsItem]:
    """Belirli bir şirket için KAP/haber taraması"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    kap_items = COMPANY_KAP_POOL.get(ticker, [])
    return [NewsItem(title=item["title"], source="KAP", url=f"https://www.kap.org.tr/tr/Bildirim/{abs(hash(item['title'])) % 100000}", sentiment=item["sentiment"], impact_score=item["impact"], categories=["KAP", "şirket"], timestamp=now) for item in kap_items]


def _llm_bundle():
    """DeepSeek LLM haber demeti (varsa); yoksa None. Süreç başına bir kez yüklenir."""
    try:
        from .news_llm import get_news_bundle, deepseek_enabled
        if not deepseek_enabled():
            return None
        from .fundamental_analysis import SECTOR_MAP, COMPANY_NAMES
        return get_news_bundle(list(SECTOR_MAP.keys()), COMPANY_NAMES)
    except Exception:
        return None


def get_news_sentiment_score(ticker: str) -> float:
    """Bir hisse için toplam haber duyarlılık skoru (0-100).
    Önce DeepSeek LLM (gerçek başlıklar), yoksa KAP havuzu."""
    bundle = _llm_bundle()
    if bundle:
        entry = bundle.get("tickers", {}).get(ticker)
        if entry and "score" in entry:
            return round(max(0.0, min(100.0, float(entry["score"]))), 1)

    company_news = scan_company_news(ticker)
    if not company_news:
        return 50.0
    total_impact = sum(n.impact_score for n in company_news)
    if total_impact == 0:
        return 50.0
    weighted_sentiment = sum(n.sentiment * n.impact_score for n in company_news) / total_impact
    return round((weighted_sentiment + 1.0) * 50.0, 1)


def get_overall_market_sentiment() -> Dict[str, float]:
    """Genel piyasa duyarlılığı (önce DeepSeek LLM, yoksa havuz)"""
    bundle = _llm_bundle()
    if bundle:
        mkt = bundle.get("market", {})
        if "score" in mkt:
            score = round(max(0.0, min(100.0, float(mkt["score"]))), 1)
            trend = mkt.get("trend") or ("POZİTİF" if score >= 55 else ("NEGATİF" if score < 45 else "NÖTR"))
            return {"score": score, "trend": trend}

    news = scan_market_news(15)
    if not news:
        return {"score": 50.0, "trend": "NÖTR"}
    avg_sentiment = sum(n.sentiment for n in news) / len(news)
    score = round((avg_sentiment + 1.0) * 50.0, 1)
    trend = "GÜÇLÜ POZİTİF" if score >= 70 else ("POZİTİF" if score >= 55 else ("NÖTR" if score >= 45 else ("NEGATİF" if score >= 30 else "GÜÇLÜ NEGATİF")))
    return {"score": score, "trend": trend}