"""
MFapi.in — Live NAV history for Indian ETFs (free, no auth).

Used as primary fallback when yfinance is rate-limited on cloud hosts.
Returns data in the same format as market_data.py so the rest of the
pipeline is unaffected.

API docs: https://api.mfapi.in
"""
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.cache import cache_manager

MFAPI_BASE = "https://api.mfapi.in/mf"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; InvestAI/1.0)",
    "Accept": "application/json",
}

# Hardcoded AMFI scheme codes (verified Mar 2026).
# Using direct codes avoids the unreliable MFapi search endpoint and is faster.
# ITBEES is not available in MFapi — will fall back to mock data for that ticker.
TICKER_SCHEME_CODES: Dict[str, int] = {
    "GOLDBEES.NS":   140088,   # Nippon India ETF Gold BeES
    "BSLGOLDETF.NS": 115127,   # Aditya Birla Sun Life Gold ETF
    "AXISGOLD.NS":   113434,   # Axis Gold ETF
    "SILVERBEES.NS": 149758,   # Nippon India Silver ETF
    "NIFTYBEES.NS":  140084,   # Nippon India ETF Nifty 50 BeES
    "SETFNIF50.NS":  135106,   # SBI Nifty 50 ETF
    "JUNIORBEES.NS": 140085,   # Nippon India ETF Nifty Next 50 Junior BeES
    "BANKBEES.NS":   140087,   # Nippon India ETF Nifty Bank BeES
    # ITBEES.NS: not available on MFapi — falls back to mock data
    "PHARMABEES.NS": 149008,   # Nippon India Nifty Pharma ETF
    "AUTOBEES.NS":   149465,   # Nippon India Nifty Auto ETF
    "INFRABEES.NS":  140102,   # Nippon India ETF Nifty Infrastructure BeES
    "CONSUMBEES.NS": 128331,   # Nippon India ETF Nifty India Consumption
    "PSUBNKBEES.NS": 140089,   # Nippon India ETF Nifty PSU Bank BeES
    "MOM100.NS":     114456,   # Motilal Oswal Nifty Midcap 100 ETF
}

# Keep this for reference (used in fetch_all_from_mfapi eligibility check)
TICKER_SEARCH_MAP: Dict[str, str] = {t: "" for t in TICKER_SCHEME_CODES}

# REITs and InvITs are NOT mutual funds — MFapi won't have them
MFAPI_UNSUPPORTED = {"EMBASSY.NS", "MINDSPACE.NS", "INDIGRID.NS", "IRB.NS", "ITBEES.NS"}


# ── Scheme code lookup ────────────────────────────────────────────────────────

def _get_scheme_code(ticker: str) -> Optional[int]:
    """Return hardcoded scheme code for a ticker, or None if not available."""
    return TICKER_SCHEME_CODES.get(ticker)


# ── NAV history helpers ───────────────────────────────────────────────────────

def _parse_nav_series(nav_data: List[Dict]) -> pd.Series:
    """
    Convert MFapi NAV list [{date: "16-03-2026", nav: "67.45"}, ...]
    to a pandas Series sorted ascending by date.
    MFapi returns dates as DD-MM-YYYY (e.g. "13-03-2026").
    """
    rows = []
    for entry in nav_data:
        try:
            # MFapi uses DD-MM-YYYY format; use dayfirst=True to parse safely
            date = pd.to_datetime(entry["date"], dayfirst=True)
            nav  = float(entry["nav"])
            rows.append((date, nav))
        except (ValueError, KeyError):
            continue
    if not rows:
        return pd.Series(dtype=float)
    rows.sort(key=lambda x: x[0])
    dates, navs = zip(*rows)
    return pd.Series(list(navs), index=pd.DatetimeIndex(dates))


def _pct_change(series: pd.Series, periods: int) -> Optional[float]:
    if len(series) < periods + 1:
        return None
    start = series.iloc[-(periods + 1)]
    end   = series.iloc[-1]
    if start == 0 or pd.isna(start) or pd.isna(end):
        return None
    return round(((end - start) / start) * 100, 2)


def _annualised_vol(series: pd.Series) -> Optional[float]:
    if len(series) < 10:
        return None
    # Use at most the last 2 years to avoid distortion from historical
    # fund restructuring / unit splits in older NAV data
    recent = series.iloc[-504:] if len(series) > 504 else series
    log_ret = np.log(recent / recent.shift(1)).dropna()
    # Exclude extreme outliers (>50% daily move = likely a split event)
    log_ret = log_ret[log_ret.abs() < 0.50]
    if len(log_ret) < 10:
        return None
    return round(float(log_ret.std() * np.sqrt(252) * 100), 2)


# ── Single ticker fetch ───────────────────────────────────────────────────────

def fetch_ticker_from_mfapi(ticker: str) -> dict:
    """
    Fetch current NAV + historical returns for one ETF ticker from MFapi.in.
    Returns a dict matching market_data.py format, or {} on failure.
    Price/returns are cached for 1 hour.
    """
    if ticker in MFAPI_UNSUPPORTED:
        return {}

    cache_key = f"mfapi_nav_{ticker}"
    cached = cache_manager.get(cache_key)
    if cached is not None:
        return cached

    scheme_code = _get_scheme_code(ticker)
    if not scheme_code:
        return {}

    try:
        resp = requests.get(
            f"{MFAPI_BASE}/{scheme_code}",
            headers=HEADERS,
            timeout=8,
        )
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("status") != "SUCCESS" or not data.get("data"):
            return {}

        close = _parse_nav_series(data["data"])
        if len(close) < 5:
            return {}

        # Detect and exclude historical split events by looking for log-returns
        # exceeding 50% in a single day (these are restructuring events, not real returns).
        # Filter out zero/negative NAV values first to avoid divide-by-zero.
        close = close[close > 0]
        if len(close) < 5:
            return {}
        with np.errstate(divide="ignore", invalid="ignore"):
            log_ret_all = np.log(close / close.shift(1)).dropna()
        log_ret_all = log_ret_all[np.isfinite(log_ret_all)]
        split_dates = log_ret_all[log_ret_all.abs() > 0.50].index
        if len(split_dates) > 0:
            last_split = split_dates[-1]
            # Use only data after the last known restructuring event
            close = close[close.index > last_split]

        if len(close) < 5:
            return {}

        result = {
            "ticker":           ticker,
            "current_price":    round(float(close.iloc[-1]), 4),
            "returns": {
                "d1": _pct_change(close, 1),
                "w1": _pct_change(close, 5),
                "m1": _pct_change(close, 21),
                "m3": _pct_change(close, 63),
                "m6": _pct_change(close, 126),
                "y1": _pct_change(close, 252),
            },
            "volatility_annual": _annualised_vol(close),
            "avg_volume_30d":    None,   # NAV data has no volume
            "data_points":       len(close),
            "price_source":      "live_mfapi",
            "price_date":        close.index[-1].strftime("%d %b %Y"),
        }
        cache_manager.set(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        print(f"[mfapi] NAV fetch error {ticker} (scheme {scheme_code}): {e}")
        return {}


# ── Batch fetch (parallel) ────────────────────────────────────────────────────

def fetch_all_from_mfapi(tickers: List[str], max_workers: int = 5) -> Dict[str, dict]:
    """
    Fetch NAV data for multiple tickers in parallel.
    Returns {ticker: data_dict} for successfully fetched tickers only.
    """
    eligible = [t for t in tickers if t in TICKER_SEARCH_MAP]
    if not eligible:
        return {}

    results: Dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(fetch_ticker_from_mfapi, t): t
            for t in eligible
        }
        for future in as_completed(future_to_ticker, timeout=15):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                if data:
                    results[ticker] = data
            except Exception as e:
                print(f"[mfapi] Parallel fetch error {ticker}: {e}")

    live_count = len(results)
    if live_count:
        print(f"[mfapi] Fetched {live_count}/{len(eligible)} tickers from MFapi.in")

    return results
