"""
Composite scoring engine — produces a 0-100 score for every investment product.

Score components & weights:
  performance  0.22  — historical returns (1d → 1y weighted)
  trend        0.15  — technical analysis (SMA/RSI/MACD)
  macro        0.15  — RBI/GDP/inflation environment
  sentiment    0.10  — news tone (GDELT + RSS)
  yield        0.13  — income yield (FD rate / dist yield / bond YTM)
  stability    0.10  — inverse of volatility
  liquidity    0.05  — trading volume / ease of exit
  duration_fit 0.10  — match between product tenure & investor horizon
"""
from typing import Dict, List, Optional
from app.analysis.duration_model import duration_score, duration_label
from app.analysis.trend_engine   import compute_trend_score, fd_trend_score
from app.analysis.sentiment_engine import get_sentiment_score
from app.data.market_data import (
    GOLD_ETFS, SILVER_ETFS, NIFTY_ETFS, SECTOR_ETFS, REITS, INVITS,
    fetch_ticker_data, fetch_all_batch,
)
from app.data.fd_rates  import get_fd_rates
from app.data.macro_data import fetch_macro_context

WEIGHTS = {
    "performance":  0.22,
    "trend":        0.15,
    "macro":        0.15,
    "sentiment":    0.10,
    "yield_score":  0.13,
    "stability":    0.10,
    "liquidity":    0.05,
    "duration_fit": 0.10,
}

# ── Normalisation helpers ─────────────────────────────────────────────────────

def _clamp(v, lo=0.0, hi=100.0) -> float:
    return max(lo, min(hi, float(v)))

def _normalise_returns(returns: dict, category: str) -> float:
    """
    Convert multi-period returns into a 0-100 performance score.
    Weights recent periods more; benchmarks vary by category.
    """
    weights = {"d1": 0.05, "w1": 0.10, "m1": 0.15, "m3": 0.20, "m6": 0.25, "y1": 0.25}
    # Category max expected returns (1y) for normalisation ceiling
    ceilings = {
        "fd": 9, "bond": 12, "gold_etf": 30, "silver_etf": 35,
        "nifty_etf": 45, "sector_etf": 55, "reit": 25, "invit": 25,
    }
    ceiling = ceilings.get(category, 30)

    weighted_sum = 0.0
    total_w = 0.0
    for period, w in weights.items():
        val = returns.get(period)
        if val is not None:
            # Scale each period's return to approximate annual rate
            annualise = {"d1": 252, "w1": 52, "m1": 12, "m3": 4, "m6": 2, "y1": 1}
            annual_est = val * annualise[period]
            normalised = _clamp((annual_est / ceiling) * 100)
            weighted_sum += normalised * w
            total_w += w

    if total_w == 0:
        return 50.0
    return round(weighted_sum / total_w, 1)

def _yield_score(product: dict, category: str) -> float:
    """0-100 yield score based on income generation."""
    if category == "fd":
        rate = product.get("applicable_rate", 7.0)
        return _clamp((rate / 9.5) * 100)   # 9.5% = ~max NBFC rate
    elif category == "bond":
        ytm = product.get("ytm", 8.0)
        return _clamp((ytm / 12.0) * 100)
    elif category == "reit":
        dy = product.get("dist_yield", 6.5)
        return _clamp((dy / 10.0) * 100)
    elif category == "invit":
        dy = product.get("dist_yield", 9.0)
        return _clamp((dy / 13.0) * 100)
    elif category in ("gold_etf", "silver_etf"):
        return 20.0   # minimal/no dividend
    elif category in ("nifty_etf", "sector_etf"):
        return 25.0   # ~1% dividend yield
    return 30.0

def _stability_score(volatility_annual: Optional[float], category: str) -> float:
    """0-100 — lower volatility = higher score."""
    category_defaults = {
        "fd": 98, "bond": 80, "reit": 62, "invit": 65,
        "gold_etf": 68, "silver_etf": 60, "nifty_etf": 58, "sector_etf": 50,
    }
    if volatility_annual is None:
        return category_defaults.get(category, 55.0)
    # vol range: 0-60% → score 100-0
    return _clamp(100 - (volatility_annual / 60) * 100)

def _liquidity_score(category: str, avg_volume: Optional[float] = None) -> float:
    base = {"fd": 20, "bond": 50, "reit": 60, "invit": 55,
            "gold_etf": 88, "silver_etf": 75, "nifty_etf": 95, "sector_etf": 72}
    score = float(base.get(category, 60))
    if avg_volume and category not in ("fd", "bond"):
        if avg_volume > 1_000_000:
            score = min(100, score + 5)
        elif avg_volume < 10_000:
            score = max(0, score - 10)
    return score

def _key_drivers(category: str, macro: dict, sentiment_score: float) -> List[str]:
    drivers = []
    if category == "fd":
        drivers = [
            f"RBI repo rate at {macro.get('repo_rate', 6.5)}% supports FD rates",
            f"CPI inflation at {macro.get('cpi_latest', 5.2)}% — real rate is positive",
            "Capital protection with guaranteed returns",
        ]
    elif category in ("gold_etf", "silver_etf"):
        drivers = [
            f"Inflation hedge — CPI at {macro.get('cpi_latest', 5.2)}%",
            "Geopolitical uncertainty drives safe-haven demand",
            "INR depreciation trend supports gold in rupee terms",
        ]
    elif category == "nifty_etf":
        drivers = [
            f"India GDP growth at {macro.get('gdp_growth', 6.4)}%",
            "Broad diversification across 50 large-cap stocks",
            "Corporate earnings recovery cycle",
        ]
    elif category == "sector_etf":
        drivers = [
            "Sector-specific momentum",
            "Policy tailwinds for targeted sectors",
            "Higher return potential vs broad market",
        ]
    elif category == "bond":
        drivers = [
            f"Yield at premium to repo rate ({macro.get('repo_rate', 6.5)}%)",
            "Capital appreciation if rates fall",
            "Fixed income predictability",
        ]
    elif category == "reit":
        drivers = [
            "Regular quarterly distributions (6-8% yield)",
            "Commercial real estate exposure",
            "Inflation-linked lease escalations",
        ]
    elif category == "invit":
        drivers = [
            "High distribution yield (8-12%)",
            "Government infrastructure spending tailwind",
            "Contracted revenues — predictable cash flows",
        ]
    if sentiment_score > 70:
        drivers.append("Positive news sentiment")
    elif sentiment_score < 35:
        drivers.append("Negative news sentiment — monitor closely")
    return drivers[:4]

def _risks(category: str, macro: dict) -> List[str]:
    base_risks = {
        "fd":          ["Premature withdrawal penalty", "Taxable interest income", "Not inflation-indexed"],
        "gold_etf":    ["No dividend income", "INR appreciation reduces returns", "Commodity price volatility"],
        "silver_etf":  ["Higher volatility than gold", "Industrial demand-driven swings", "No income yield"],
        "nifty_etf":   ["Equity market risk", "FII outflow risk", "Global recession risk"],
        "sector_etf":  ["Concentration risk", "Sector-specific regulatory risk", "Higher drawdowns than Nifty 50"],
        "bond":        ["Credit/default risk", "Interest rate risk", "Liquidity risk in secondary market"],
        "reit":        ["Interest rate sensitivity", "Vacancy risk", "SEBI regulatory changes"],
        "invit":       ["Concession renewal risk", "Government policy dependency", "Lower liquidity"],
    }
    risks = list(base_risks.get(category, ["Market risk"]))
    cpi = macro.get("cpi_latest", 5.0)
    if cpi > 6.0 and category == "fd":
        risks.insert(0, f"Real return risk — CPI {cpi}% may erode purchasing power")
    return risks[:3]

# ── Main scorer ───────────────────────────────────────────────────────────────

def score_product(product: dict, category: str, duration_days: int, macro: dict) -> dict:
    """
    Score a single product and return enriched dict with scores, drivers, risks.
    `product` must contain either ticker data (ETF) or rate data (FD/bond).
    """
    returns = product.get("returns", {})

    # Individual component scores
    performance = _normalise_returns(returns, category)
    trend        = (compute_trend_score(product["id"])
                    if category != "fd"
                    else fd_trend_score(macro.get("rate_trend", "neutral")))
    macro_score  = float(macro.get(f"{category}_macro_score",
                   macro.get("equity_macro_score", 50)))
    sentiment    = get_sentiment_score(category)
    yld          = _yield_score(product, category)
    stability    = _stability_score(product.get("volatility_annual"), category)
    liquidity    = _liquidity_score(category, product.get("avg_volume_30d"))
    dur_fit      = duration_score(category, duration_days)

    scores = {
        "performance":  round(performance, 1),
        "trend":        round(trend, 1),
        "macro":        round(macro_score, 1),
        "sentiment":    round(sentiment, 1),
        "yield_score":  round(yld, 1),
        "stability":    round(stability, 1),
        "liquidity":    round(liquidity, 1),
        "duration_fit": round(dur_fit, 1),
    }

    overall = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    overall = round(_clamp(overall), 1)

    # Confidence: based on data completeness and score consistency
    returns_filled = sum(1 for v in returns.values() if v is not None)
    data_confidence = (returns_filled / 6) * 100
    score_std = (sum((s - overall)**2 for s in scores.values()) / len(scores)) ** 0.5
    confidence = int(_clamp(data_confidence * 0.5 + (100 - score_std) * 0.5))

    return {
        **product,
        "category": category,
        "scores": {**scores, "overall": overall},
        "confidence": confidence,
        "key_drivers": _key_drivers(category, macro, sentiment),
        "risks": _risks(category, macro),
        "duration_suitability": duration_label(category, duration_days),
        "source_links": _source_links(category, product),
    }

def _source_links(category: str, product: dict) -> List[str]:
    ticker = product.get("id", "").replace(".NS", "").replace(".BO", "")
    links = []
    if category in ("gold_etf","silver_etf","nifty_etf","sector_etf","reit","invit"):
        links.append(f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}")
        links.append(f"https://www.mfapi.in/mf")
    elif category == "fd":
        links.append("https://www.bankbazaar.com/fixed-deposit-rate.html")
        links.append("https://www.paisabazaar.com/fixed-deposit/")
    elif category == "bond":
        links.append("https://www.nseindia.com/market-data/bonds-traded-in-capital-market")
    links.append("https://www.amfiindia.com/net-asset-value/nav-download")
    return links[:3]

# ── Score all products → return top N ────────────────────────────────────────

def score_and_rank(
    duration_days: int,
    amount: float,
    risk_appetite: str = "medium",
    top_n: int = 5,
) -> List[dict]:
    """
    Master function: fetch all products, score them, return top N.
    """
    macro = fetch_macro_context()
    all_products = []

    # ── ETFs (gold, silver, nifty, sector, reit, invit) ──────────────────
    batch_data = fetch_all_batch()   # single HTTP request for all tickers

    cat_map = [
        (GOLD_ETFS,   "gold_etf"),
        (SILVER_ETFS, "silver_etf"),
        (NIFTY_ETFS,  "nifty_etf"),
        (SECTOR_ETFS, "sector_etf"),
        (REITS,       "reit"),
        (INVITS,      "invit"),
    ]
    for product_list, cat in cat_map:
        for meta in product_list:
            data = batch_data.get(meta["id"])
            if not data:
                continue
            merged = {**meta, **data}
            scored = score_product(merged, cat, duration_days, macro)
            all_products.append(scored)

    # ── FDs ───────────────────────────────────────────────────────────────
    for fd in get_fd_rates(duration_days):
        rate = fd.get("applicable_rate", 7.0)
        scored = score_product(
            {
                **fd,
                "returns": {
                    "d1": None, "w1": None, "m1": None,
                    "m3": rate / 4, "m6": rate / 2, "y1": rate,
                },
                "current_price": None,
                "current_rate": rate,
                "volatility_annual": 0,
                "avg_volume_30d": None,
            },
            "fd", duration_days, macro,
        )
        all_products.append(scored)

    # ── Risk-appetite filter ──────────────────────────────────────────────
    if risk_appetite == "low":
        all_products = [p for p in all_products if p["category"] in ("fd","bond","gold_etf","reit")]
    elif risk_appetite == "high":
        all_products = [p for p in all_products if p["category"] not in ("fd",)]

    # ── Rank by overall score ─────────────────────────────────────────────
    all_products.sort(key=lambda p: p["scores"]["overall"], reverse=True)

    # ── Enforce category diversity (max 1 per category in top 5) ────────
    # Pass 1: pick the best product per unique category (up to top_n)
    seen_cats_pass1: set = set()
    diverse = []
    for p in all_products:
        cat = p["category"]
        if cat not in seen_cats_pass1:
            diverse.append(p)
            seen_cats_pass1.add(cat)
        if len(diverse) >= top_n:
            break

    # Pass 2: if fewer than top_n after dedup, fill remaining slots
    # allowing 2nd best of already-seen categories
    if len(diverse) < top_n:
        seen_cats_pass2: Dict[str, int] = {cat: 1 for cat in seen_cats_pass1}
        for p in all_products:
            if p in diverse:
                continue
            cat = p["category"]
            count = seen_cats_pass2.get(cat, 0)
            if count < 2:
                diverse.append(p)
                seen_cats_pass2[cat] = count + 1
            if len(diverse) >= top_n:
                break

    return diverse[:top_n]
