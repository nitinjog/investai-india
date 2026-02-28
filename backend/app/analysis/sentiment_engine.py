"""
Sentiment scoring layer.
Combines GDELT tone scores + RSS keyword analysis per asset category.
Output: 0-100 sentiment score per category.
"""
from typing import Dict
from app.data.news_data import fetch_category_sentiment

# Fallback neutral if news fetch fails
NEUTRAL = {"combined_score": 50, "headlines": [], "gdelt_score": 50, "rss_score": 50}

def get_sentiment_score(category: str) -> float:
    """Return 0-100 sentiment score for an asset category."""
    try:
        data = fetch_category_sentiment(category)
        return float(data.get("combined_score", 50))
    except Exception:
        return 50.0

def get_sentiment_data(category: str) -> Dict:
    """Full sentiment data including headlines."""
    try:
        return fetch_category_sentiment(category)
    except Exception:
        return NEUTRAL.copy()

def headlines_for(category: str) -> list:
    data = get_sentiment_data(category)
    return data.get("headlines", [])
