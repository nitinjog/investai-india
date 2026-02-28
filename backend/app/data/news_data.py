"""
News & sentiment from:
  - GDELT Project API (free, no key)
  - Indian financial RSS feeds (ET, Moneycontrol, BS, Mint)
Returns per-category sentiment scores and top headlines.
"""
import requests
import feedparser
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.cache import cache_manager

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; InvestAI/1.0; India)"}

# ── RSS Feeds ─────────────────────────────────────────────────────────────────
RSS_FEEDS = {
    "markets": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.business-standard.com/rss/markets-106.rss",
        "https://www.livemint.com/rss/markets",
    ],
    "economy": [
        "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
        "https://www.business-standard.com/rss/economy-policy-102.rss",
    ],
    "commodities": [
        "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1989812555.cms",
    ],
}

# Category → GDELT search queries
GDELT_QUERIES = {
    "gold_etf":    "gold india investment ETF bullion",
    "silver_etf":  "silver india commodity MCX",
    "nifty_etf":   "nifty india stock market equity",
    "sector_etf":  "india sector stock market equity banking IT pharma",
    "bond":        "india bond NCD yield RBI interest rate",
    "reit":        "india REIT real estate commercial property",
    "invit":       "india InvIT infrastructure power roads energy",
    "fd":          "india fixed deposit bank interest rate savings",
    "macro":       "RBI monetary policy repo rate India economy GDP",
}

# ── GDELT ─────────────────────────────────────────────────────────────────────

def fetch_gdelt_sentiment(query: str, days: int = 7) -> Dict:
    """
    Query GDELT full-text search API.
    Returns average tone (-100 to +100) and article count.
    Tone > 0 = positive, < 0 = negative.
    """
    cache_key = f"news_gdelt_{query[:30]}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    try:
        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={requests.utils.quote(query)}"
            "&mode=artlist&maxrecords=25&format=json"
        )
        resp = requests.get(url, timeout=10, headers=HEADERS)
        if resp.status_code != 200:
            return {"tone": 0, "count": 0, "headlines": []}

        data = resp.json()
        articles = data.get("articles", [])
        if not articles:
            return {"tone": 0, "count": 0, "headlines": []}

        tones = [float(a.get("tone", 0)) for a in articles if a.get("tone")]
        avg_tone = sum(tones) / len(tones) if tones else 0
        headlines = [a.get("title", "") for a in articles[:5]]

        result = {
            "tone": round(avg_tone, 2),
            "count": len(articles),
            "headlines": headlines,
            "sentiment_score": round((avg_tone + 100) / 2, 1),  # normalise to 0-100
        }
        cache_manager.set(cache_key, result)
        return result

    except Exception as e:
        print(f"[news_data] GDELT error for '{query}': {e}")
        return {"tone": 0, "count": 0, "headlines": [], "sentiment_score": 50}

# ── RSS ───────────────────────────────────────────────────────────────────────

def fetch_rss_headlines(category: str = "markets") -> List[str]:
    """Return recent headlines from India financial RSS feeds."""
    cache_key = f"news_rss_{category}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    headlines = []
    feeds = RSS_FEEDS.get(category, RSS_FEEDS["markets"])
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                if title:
                    headlines.append(title)
        except Exception as e:
            print(f"[news_data] RSS error {url}: {e}")

    headlines = headlines[:20]
    cache_manager.set(cache_key, headlines)
    return headlines

# ── Keyword sentiment ─────────────────────────────────────────────────────────

POSITIVE_WORDS = {
    "surge", "rally", "bullish", "gain", "rise", "soar", "record", "high",
    "growth", "strong", "positive", "boom", "recovery", "uptrend", "buy",
    "upgrade", "beat", "outperform", "inflow", "investment", "profit",
}
NEGATIVE_WORDS = {
    "fall", "drop", "crash", "bearish", "loss", "decline", "weak", "sell",
    "downgrade", "miss", "outflow", "risk", "inflation", "deficit", "debt",
    "recession", "fear", "concern", "cut", "slump", "volatility",
}

def _headline_sentiment(headlines: List[str]) -> float:
    """Simple keyword-based sentiment: 0-100."""
    pos = neg = 0
    for h in headlines:
        words = h.lower().split()
        pos += sum(1 for w in words if w in POSITIVE_WORDS)
        neg += sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 50.0
    return round((pos / total) * 100, 1)

# ── Public API ────────────────────────────────────────────────────────────────

def fetch_category_sentiment(category: str) -> Dict:
    """
    Returns:
      gdelt_score (0-100), rss_score (0-100),
      combined_score (0-100), headlines: List[str]
    """
    cache_key = f"news_combined_{category}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    query = GDELT_QUERIES.get(category, f"india {category} investment")
    gdelt = fetch_gdelt_sentiment(query)
    gdelt_score = gdelt.get("sentiment_score", 50)

    rss_cat = "commodities" if category in ("gold_etf", "silver_etf") else "markets"
    headlines = fetch_rss_headlines(rss_cat)
    rss_score = _headline_sentiment(headlines)

    # Weight GDELT 60%, RSS 40%
    combined = round(gdelt_score * 0.6 + rss_score * 0.4, 1)

    result = {
        "gdelt_score": gdelt_score,
        "rss_score": rss_score,
        "combined_score": combined,
        "headlines": (gdelt.get("headlines", []) + headlines)[:8],
        "article_count": gdelt.get("count", 0),
    }
    cache_manager.set(cache_key, result)
    return result

def fetch_all_sentiments() -> Dict[str, Dict]:
    """Fetch sentiment for every asset category."""
    return {cat: fetch_category_sentiment(cat) for cat in GDELT_QUERIES}
