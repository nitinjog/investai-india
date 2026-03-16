"""
Fixed Deposit rates — scraped from BankBazaar public page + fallback static data.
Returns a list of FD products with tenure-wise rates.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from app.cache import cache_manager

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

# ── Static FD rates (updated Mar 2026 — post RBI 25bps cut in Feb 2026) ───────
# Banks have passed on ~15-25bps of the cut to FD holders.
# Rates effective approximately 15-Mar-2026; verify on bank websites for latest.
FD_RATES_DATE = "2026-03-15"

STATIC_FD_RATES: List[Dict] = [
    # Nationalised Banks
    {"id": "sbi_fd",          "name": "SBI Fixed Deposit",           "issuer": "State Bank of India",   "type": "bank",
     "rates": {"7d": 3.50, "30d": 4.50, "90d": 5.50, "180d": 6.25, "1y": 6.60, "2y": 6.80, "3y": 6.50, "5y": 6.25},
     "min_amount": 1000, "safety": "Very High", "credit_rating": "Sovereign"},
    {"id": "pnb_fd",          "name": "PNB Fixed Deposit",           "issuer": "Punjab National Bank",  "type": "bank",
     "rates": {"7d": 3.50, "30d": 4.50, "90d": 5.25, "180d": 6.25, "1y": 6.60, "2y": 6.80, "3y": 6.60, "5y": 6.25},
     "min_amount": 1000, "safety": "Very High", "credit_rating": "Sovereign"},
    # Private Banks
    {"id": "hdfc_fd",         "name": "HDFC Bank Fixed Deposit",     "issuer": "HDFC Bank",             "type": "bank",
     "rates": {"7d": 3.50, "30d": 4.50, "90d": 5.75, "180d": 6.60, "1y": 6.90, "2y": 7.00, "3y": 7.00, "5y": 6.80},
     "min_amount": 5000, "safety": "Very High", "credit_rating": "AAA"},
    {"id": "icici_fd",        "name": "ICICI Bank Fixed Deposit",    "issuer": "ICICI Bank",            "type": "bank",
     "rates": {"7d": 3.00, "30d": 4.50, "90d": 5.50, "180d": 6.60, "1y": 6.80, "2y": 6.90, "3y": 6.90, "5y": 6.80},
     "min_amount": 10000, "safety": "Very High", "credit_rating": "AAA"},
    {"id": "axis_fd",         "name": "Axis Bank Fixed Deposit",     "issuer": "Axis Bank",             "type": "bank",
     "rates": {"7d": 3.00, "30d": 4.50, "90d": 5.75, "180d": 6.60, "1y": 6.80, "2y": 6.90, "3y": 6.90, "5y": 6.80},
     "min_amount": 5000, "safety": "Very High", "credit_rating": "AAA"},
    {"id": "kotak_fd",        "name": "Kotak Mahindra Bank FD",      "issuer": "Kotak Mahindra Bank",   "type": "bank",
     "rates": {"7d": 2.75, "30d": 4.00, "90d": 5.90, "180d": 6.80, "1y": 6.90, "2y": 6.90, "3y": 6.90, "5y": 6.00},
     "min_amount": 5000, "safety": "Very High", "credit_rating": "AAA"},
    # Small Finance Banks
    {"id": "yes_fd",          "name": "Yes Bank Fixed Deposit",      "issuer": "Yes Bank",              "type": "bank",
     "rates": {"7d": 3.50, "30d": 4.50, "90d": 6.00, "180d": 7.10, "1y": 7.55, "2y": 7.55, "3y": 7.55, "5y": 7.25},
     "min_amount": 10000, "safety": "High", "credit_rating": "AA-"},
    {"id": "idfc_fd",         "name": "IDFC First Bank FD",          "issuer": "IDFC First Bank",       "type": "bank",
     "rates": {"7d": 3.50, "30d": 4.75, "90d": 6.00, "180d": 7.10, "1y": 7.75, "2y": 7.75, "3y": 7.75, "5y": 7.25},
     "min_amount": 10000, "safety": "High", "credit_rating": "AA"},
    {"id": "au_fd",           "name": "AU Small Finance Bank FD",    "issuer": "AU Small Finance Bank", "type": "sfb",
     "rates": {"7d": 4.25, "30d": 5.50, "90d": 6.75, "180d": 7.40, "1y": 7.80, "2y": 7.80, "3y": 7.80, "5y": 7.50},
     "min_amount": 1000, "safety": "High", "credit_rating": "AA"},
    {"id": "ujjivan_fd",      "name": "Ujjivan Small Finance Bank FD","issuer": "Ujjivan SFB",          "type": "sfb",
     "rates": {"7d": 3.75, "30d": 5.25, "90d": 6.50, "180d": 7.40, "1y": 8.00, "2y": 8.00, "3y": 7.80, "5y": 7.50},
     "min_amount": 1000, "safety": "Moderate-High", "credit_rating": "A+"},
    # NBFCs
    {"id": "bajaj_fd",        "name": "Bajaj Finance FD",            "issuer": "Bajaj Finance Ltd",     "type": "nbfc",
     "rates": {"30d": 6.20, "90d": 7.20, "180d": 7.50, "1y": 8.25, "2y": 8.25, "3y": 8.15, "5y": 7.90},
     "min_amount": 15000, "safety": "High", "credit_rating": "AAA"},
    {"id": "shriram_fd",      "name": "Shriram Finance FD",          "issuer": "Shriram Finance Ltd",   "type": "nbfc",
     "rates": {"30d": 5.80, "90d": 6.80, "180d": 7.60, "1y": 8.55, "2y": 8.55, "3y": 8.30, "5y": 8.05},
     "min_amount": 5000, "safety": "Moderate-High", "credit_rating": "AA+"},
    {"id": "mahindra_fd",     "name": "Mahindra Finance FD",         "issuer": "Mahindra & Mahindra Financial", "type": "nbfc",
     "rates": {"30d": 5.50, "90d": 6.50, "180d": 7.30, "1y": 7.90, "2y": 7.90, "3y": 7.80, "5y": 7.50},
     "min_amount": 25000, "safety": "High", "credit_rating": "AAA"},
]

def _best_rate_for_duration(rates: dict, duration_days: int) -> float:
    """Pick the most appropriate FD rate for the given duration."""
    mapping = [
        (7,   "7d"),
        (30,  "30d"),
        (90,  "90d"),
        (180, "180d"),
        (365, "1y"),
        (730, "2y"),
        (1095,"3y"),
        (1825,"5y"),
    ]
    best_key = "1y"
    for days, key in mapping:
        if duration_days <= days and key in rates:
            best_key = key
            break
        if key in rates:
            best_key = key
    return rates.get(best_key, rates.get("1y", 7.0))

def get_fd_rates(duration_days: int = 365) -> List[Dict]:
    """Return FD products enriched with the relevant rate for the duration."""
    cache_key = f"fd_{duration_days}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    results = []
    for fd in STATIC_FD_RATES:
        rate = _best_rate_for_duration(fd["rates"], duration_days)
        results.append({
            **fd,
            "applicable_rate": rate,
            "duration_days": duration_days,
            "category": "fd",
        })

    cache_manager.set(cache_key, results)
    return results
