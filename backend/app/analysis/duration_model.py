"""
Duration suitability model.
Returns a 0-100 score for how well each asset category matches the investor's horizon.
"""

# Suitability matrix: category → duration bucket → base score
_MATRIX = {
    "fd": {
        "ultra_short": 88,   # ≤30 days
        "short":       82,   # 31-90 days
        "medium_short":78,   # 91-180 days
        "medium":      72,   # 181-365 days
        "long_short":  62,   # 1-2 years
        "long":        50,   # 2-3 years
        "very_long":   40,   # 3+ years
    },
    "gold_etf": {
        "ultra_short": 40,
        "short":       55,
        "medium_short":65,
        "medium":      72,
        "long_short":  78,
        "long":        82,
        "very_long":   85,
    },
    "silver_etf": {
        "ultra_short": 35,
        "short":       50,
        "medium_short":60,
        "medium":      68,
        "long_short":  74,
        "long":        78,
        "very_long":   80,
    },
    "nifty_etf": {
        "ultra_short": 25,
        "short":       38,
        "medium_short":52,
        "medium":      65,
        "long_short":  80,
        "long":        88,
        "very_long":   93,
    },
    "sector_etf": {
        "ultra_short": 20,
        "short":       32,
        "medium_short":48,
        "medium":      60,
        "long_short":  74,
        "long":        84,
        "very_long":   88,
    },
    "bond": {
        "ultra_short": 72,
        "short":       78,
        "medium_short":82,
        "medium":      85,
        "long_short":  80,
        "long":        74,
        "very_long":   68,
    },
    "reit": {
        "ultra_short": 15,
        "short":       28,
        "medium_short":42,
        "medium":      58,
        "long_short":  72,
        "long":        82,
        "very_long":   90,
    },
    "invit": {
        "ultra_short": 12,
        "short":       25,
        "medium_short":38,
        "medium":      55,
        "long_short":  70,
        "long":        82,
        "very_long":   90,
    },
}

def _bucket(duration_days: int) -> str:
    if duration_days <= 30:
        return "ultra_short"
    elif duration_days <= 90:
        return "short"
    elif duration_days <= 180:
        return "medium_short"
    elif duration_days <= 365:
        return "medium"
    elif duration_days <= 730:
        return "long_short"
    elif duration_days <= 1095:
        return "long"
    else:
        return "very_long"

def duration_score(category: str, duration_days: int) -> float:
    bucket = _bucket(duration_days)
    return float(_MATRIX.get(category, {}).get(bucket, 50))

def duration_label(category: str, duration_days: int) -> str:
    score = duration_score(category, duration_days)
    bucket = _bucket(duration_days)
    labels = {
        "ultra_short": "≤30 days",
        "short":       "1–3 months",
        "medium_short":"3–6 months",
        "medium":      "6–12 months",
        "long_short":  "1–2 years",
        "long":        "2–3 years",
        "very_long":   "3+ years",
    }
    horizon = labels[bucket]
    if score >= 80:
        fit = "Excellent fit"
    elif score >= 65:
        fit = "Good fit"
    elif score >= 50:
        fit = "Moderate fit"
    elif score >= 35:
        fit = "Weak fit"
    else:
        fit = "Not recommended"
    return f"{fit} for {horizon} horizon"

def recommend_categories(duration_days: int, top_n: int = 3) -> list:
    """Return top-N best-matched categories for the given duration."""
    scored = [
        (cat, duration_score(cat, duration_days))
        for cat in _MATRIX
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [cat for cat, _ in scored[:top_n]]
