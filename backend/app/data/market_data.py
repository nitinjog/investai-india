"""
Market data via yfinance — NSE (.NS) and BSE (.BO) tickers.
Returns historical OHLCV and computed periodic returns.
Falls back to realistic mock data if yfinance is rate-limited.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.cache import cache_manager

# ── Realistic mock data (updated Feb 2026) ────────────────────────────────────
# Used when yfinance is rate-limited. Returns are in %.
MOCK_DATA: Dict[str, dict] = {
    "GOLDBEES.NS":   {"current_price": 58.42,  "returns": {"d1": 0.23,  "w1": 1.45,  "m1": 3.21,  "m3": 8.45,  "m6": 12.34, "y1": 18.92}, "volatility_annual": 14.2, "avg_volume_30d": 850000},
    "BSLGOLDETF.NS": {"current_price": 56.80,  "returns": {"d1": 0.21,  "w1": 1.42,  "m1": 3.18,  "m3": 8.40,  "m6": 12.28, "y1": 18.85}, "volatility_annual": 14.3, "avg_volume_30d": 120000},
    "AXISGOLD.NS":   {"current_price": 21.15,  "returns": {"d1": 0.20,  "w1": 1.40,  "m1": 3.15,  "m3": 8.35,  "m6": 12.20, "y1": 18.78}, "volatility_annual": 14.5, "avg_volume_30d": 95000},
    "KOTAKGOLD.NS":  {"current_price": 22.30,  "returns": {"d1": 0.22,  "w1": 1.43,  "m1": 3.19,  "m3": 8.42,  "m6": 12.30, "y1": 18.88}, "volatility_annual": 14.1, "avg_volume_30d": 180000},
    "HDFCMFGETF.NS": {"current_price": 57.95,  "returns": {"d1": 0.23,  "w1": 1.44,  "m1": 3.20,  "m3": 8.44,  "m6": 12.32, "y1": 18.90}, "volatility_annual": 14.2, "avg_volume_30d": 210000},
    "SILVERBEES.NS": {"current_price": 88.60,  "returns": {"d1": 0.45,  "w1": 2.10,  "m1": 4.50,  "m3": 10.20, "m6": 15.80, "y1": 24.50}, "volatility_annual": 22.1, "avg_volume_30d": 420000},
    "KOTAKSILVER.NS":{"current_price": 90.20,  "returns": {"d1": 0.44,  "w1": 2.08,  "m1": 4.45,  "m3": 10.15, "m6": 15.70, "y1": 24.30}, "volatility_annual": 22.3, "avg_volume_30d": 85000},
    "NIFTYBEES.NS":  {"current_price": 250.85, "returns": {"d1": 0.35,  "w1": 1.20,  "m1": 2.80,  "m3": 6.50,  "m6": 9.80,  "y1": 15.40}, "volatility_annual": 16.5, "avg_volume_30d": 3200000},
    "ICICINIFTY.NS": {"current_price": 248.40, "returns": {"d1": 0.34,  "w1": 1.18,  "m1": 2.78,  "m3": 6.45,  "m6": 9.75,  "y1": 15.32}, "volatility_annual": 16.6, "avg_volume_30d": 450000},
    "KOTAKNIFTY.NS": {"current_price": 149.20, "returns": {"d1": 0.33,  "w1": 1.17,  "m1": 2.75,  "m3": 6.42,  "m6": 9.70,  "y1": 15.28}, "volatility_annual": 16.7, "avg_volume_30d": 280000},
    "SETFNIF50.NS":  {"current_price": 252.15, "returns": {"d1": 0.35,  "w1": 1.21,  "m1": 2.82,  "m3": 6.52,  "m6": 9.82,  "y1": 15.45}, "volatility_annual": 16.4, "avg_volume_30d": 1100000},
    "JUNIORBEES.NS": {"current_price": 680.50, "returns": {"d1": 0.42,  "w1": 1.50,  "m1": 3.40,  "m3": 8.20,  "m6": 12.50, "y1": 18.60}, "volatility_annual": 20.2, "avg_volume_30d": 180000},
    "BANKBEES.NS":   {"current_price": 490.20, "returns": {"d1": 0.55,  "w1": 1.80,  "m1": 4.20,  "m3": 9.50,  "m6": 14.20, "y1": 12.80}, "volatility_annual": 24.1, "avg_volume_30d": 920000},
    "ITBEES.NS":     {"current_price": 38.50,  "returns": {"d1": 0.28,  "w1": 1.05,  "m1": 2.40,  "m3": 5.80,  "m6": 8.90,  "y1": 22.40}, "volatility_annual": 23.5, "avg_volume_30d": 610000},
    "PHARMABEES.NS": {"current_price": 22.80,  "returns": {"d1": 0.18,  "w1": 0.95,  "m1": 2.10,  "m3": 6.20,  "m6": 11.40, "y1": 28.50}, "volatility_annual": 21.8, "avg_volume_30d": 185000},
    "AUTOBEES.NS":   {"current_price": 198.40, "returns": {"d1": 0.62,  "w1": 2.10,  "m1": 4.80,  "m3": 11.20, "m6": 16.40, "y1": 21.30}, "volatility_annual": 26.4, "avg_volume_30d": 92000},
    "INFRABEES.NS":  {"current_price": 42.60,  "returns": {"d1": 0.48,  "w1": 1.65,  "m1": 3.90,  "m3": 9.80,  "m6": 15.20, "y1": 19.80}, "volatility_annual": 25.2, "avg_volume_30d": 68000},
    "CONSUMBEES.NS": {"current_price": 88.40,  "returns": {"d1": 0.30,  "w1": 1.10,  "m1": 2.50,  "m3": 5.90,  "m6": 8.70,  "y1": 14.20}, "volatility_annual": 18.9, "avg_volume_30d": 48000},
    "PSUBNKBEES.NS": {"current_price": 62.80,  "returns": {"d1": 0.72,  "w1": 2.40,  "m1": 5.60,  "m3": 12.80, "m6": 18.60, "y1": 8.40},  "volatility_annual": 30.5, "avg_volume_30d": 380000},
    "MOM100.NS":     {"current_price": 72.50,  "returns": {"d1": 0.50,  "w1": 1.80,  "m1": 4.20,  "m3": 10.50, "m6": 16.80, "y1": 25.40}, "volatility_annual": 22.8, "avg_volume_30d": 210000},
    "EMBASSY.NS":    {"current_price": 350.80, "returns": {"d1": 0.18,  "w1": 0.65,  "m1": 1.80,  "m3": 4.20,  "m6": 6.50,  "y1": 9.80},  "volatility_annual": 12.4, "avg_volume_30d": 280000},
    "MINDSPACE.NS":  {"current_price": 320.50, "returns": {"d1": 0.15,  "w1": 0.58,  "m1": 1.65,  "m3": 3.90,  "m6": 6.10,  "y1": 8.90},  "volatility_annual": 13.1, "avg_volume_30d": 185000},
    "BROOKFIELD.NS": {"current_price": 295.20, "returns": {"d1": 0.20,  "w1": 0.72,  "m1": 2.10,  "m3": 4.80,  "m6": 7.20,  "y1": 11.40}, "volatility_annual": 14.8, "avg_volume_30d": 92000},
    "NEXUS.NS":      {"current_price": 142.60, "returns": {"d1": 0.25,  "w1": 0.85,  "m1": 2.40,  "m3": 5.50,  "m6": 8.40,  "y1": 13.20}, "volatility_annual": 15.2, "avg_volume_30d": 78000},
    "INDIGRID.NS":   {"current_price": 152.80, "returns": {"d1": 0.12,  "w1": 0.48,  "m1": 1.40,  "m3": 3.20,  "m6": 5.80,  "y1": 8.50},  "volatility_annual": 11.2, "avg_volume_30d": 145000},
    "POWERGRD.NS":   {"current_price": 98.40,  "returns": {"d1": 0.10,  "w1": 0.42,  "m1": 1.20,  "m3": 2.80,  "m6": 5.20,  "y1": 7.80},  "volatility_annual": 10.8, "avg_volume_30d": 210000},
    "IRB.NS":        {"current_price": 62.50,  "returns": {"d1": 0.15,  "w1": 0.55,  "m1": 1.60,  "m3": 3.60,  "m6": 6.40,  "y1": 9.20},  "volatility_annual": 13.5, "avg_volume_30d": 88000},
}

# ── Product Universe ─────────────────────────────────────────────────────────

GOLD_ETFS = [
    {"id": "GOLDBEES.NS",    "name": "Nippon India Gold BeES ETF",          "issuer": "Nippon India MF"},
    {"id": "BSLGOLDETF.NS",  "name": "Aditya Birla Sun Life Gold ETF",      "issuer": "ABSL MF"},
    {"id": "AXISGOLD.NS",    "name": "Axis Gold ETF",                        "issuer": "Axis MF"},
]

SILVER_ETFS = [
    {"id": "SILVERBEES.NS",  "name": "Nippon India Silver ETF BeES",         "issuer": "Nippon India MF"},
]

NIFTY_ETFS = [
    {"id": "NIFTYBEES.NS",   "name": "Nippon India ETF Nifty 50 BeES",       "issuer": "Nippon India MF"},
    {"id": "SETFNIF50.NS",   "name": "SBI ETF Nifty 50",                     "issuer": "SBI MF"},
    {"id": "JUNIORBEES.NS",  "name": "Nippon India ETF Nifty Next 50",        "issuer": "Nippon India MF"},
]

SECTOR_ETFS = [
    {"id": "BANKBEES.NS",    "name": "Nippon India ETF Bank BeES",           "issuer": "Nippon India MF",  "sector": "Banking"},
    {"id": "ITBEES.NS",      "name": "Nippon India ETF Nifty IT",            "issuer": "Nippon India MF",  "sector": "IT"},
    {"id": "PHARMABEES.NS",  "name": "Nippon India ETF Nifty Pharma",        "issuer": "Nippon India MF",  "sector": "Pharma"},
    {"id": "AUTOBEES.NS",    "name": "Nippon India ETF Nifty Auto",          "issuer": "Nippon India MF",  "sector": "Auto"},
    {"id": "INFRABEES.NS",   "name": "Nippon India ETF Nifty Infrastructure","issuer": "Nippon India MF",  "sector": "Infra"},
    {"id": "CONSUMBEES.NS",  "name": "Nippon India ETF Nifty Consumption",   "issuer": "Nippon India MF",  "sector": "FMCG/Consumption"},
    {"id": "PSUBNKBEES.NS",  "name": "Nippon India ETF PSU Bank BeES",       "issuer": "Nippon India MF",  "sector": "PSU Banking"},
    {"id": "MOM100.NS",      "name": "Motilal Oswal Nifty Midcap 100 ETF",  "issuer": "Motilal Oswal MF", "sector": "Midcap"},
]

REITS = [
    {"id": "EMBASSY.NS",     "name": "Embassy Office Parks REIT",            "issuer": "Embassy REIT",     "dist_yield": 6.5},
    {"id": "MINDSPACE.NS",   "name": "Mindspace Business Parks REIT",        "issuer": "Mindspace REIT",   "dist_yield": 6.2},
]

INVITS = [
    {"id": "INDIGRID.NS",    "name": "India Grid Trust InvIT",               "issuer": "IndiGrid",         "dist_yield": 11.5},
    {"id": "IRB.NS",         "name": "IRB InvIT Fund",                       "issuer": "IRB Infra",        "dist_yield": 8.8},
]

ALL_ETF_UNIVERSE = GOLD_ETFS + SILVER_ETFS + NIFTY_ETFS + SECTOR_ETFS + REITS + INVITS

# ── Helpers ───────────────────────────────────────────────────────────────────

def _pct_change(series: pd.Series, periods: int) -> Optional[float]:
    """Return % change over `periods` trading days, or None if insufficient data."""
    if len(series) < periods + 1:
        return None
    start = series.iloc[-(periods + 1)]
    end = series.iloc[-1]
    if start == 0 or pd.isna(start) or pd.isna(end):
        return None
    return round(((end - start) / start) * 100, 2)

def _annualised_vol(series: pd.Series) -> Optional[float]:
    """Annualised volatility (std dev of daily log returns)."""
    if len(series) < 10:
        return None
    log_ret = np.log(series / series.shift(1)).dropna()
    return round(float(log_ret.std() * np.sqrt(252) * 100), 2)

# ── Batch fetcher (avoids rate limits) ───────────────────────────────────────

_batch_cache_key = "prices_batch_all"

def _parse_ticker_from_batch(ticker: str, df_close: "pd.DataFrame", df_volume: "pd.DataFrame") -> dict:
    """Extract per-ticker metrics from a batch-downloaded DataFrame."""
    try:
        close  = df_close[ticker].dropna()
        volume = df_volume[ticker].dropna()
        if len(close) < 5:
            return {}
        result = {
            "ticker": ticker,
            "current_price": round(float(close.iloc[-1]), 2),
            "returns": {
                "d1": _pct_change(close, 1),
                "w1": _pct_change(close, 5),
                "m1": _pct_change(close, 21),
                "m3": _pct_change(close, 63),
                "m6": _pct_change(close, 126),
                "y1": _pct_change(close, 252),
            },
            "volatility_annual": _annualised_vol(close),
            "avg_volume_30d": round(float(volume.iloc[-30:].mean()), 0) if len(volume) >= 30 else None,
            "data_points": len(close),
        }
        return result
    except Exception:
        return {}

def fetch_all_batch() -> Dict[str, dict]:
    """
    Download all ETF universe tickers in a single yfinance batch call.
    Far more efficient than individual calls and avoids rate limits.
    """
    cached = cache_manager.get(_batch_cache_key)
    if cached:
        return cached

    tickers = [p["id"] for p in ALL_ETF_UNIVERSE]
    results = {}

    try:
        import yfinance as yf
        raw = yf.download(
            tickers=tickers,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="column",
        )

        if not raw.empty:
            # Multi-ticker download gives MultiIndex columns: (field, ticker)
            if isinstance(raw.columns, pd.MultiIndex):
                df_close  = raw["Close"]
                df_volume = raw["Volume"]
            else:
                df_close  = raw[["Close"]].rename(columns={"Close": tickers[0]})
                df_volume = raw[["Volume"]].rename(columns={"Volume": tickers[0]})

            for p in ALL_ETF_UNIVERSE:
                ticker = p["id"]
                if ticker in df_close.columns:
                    data = _parse_ticker_from_batch(ticker, df_close, df_volume)
                    if data:
                        results[ticker] = {**p, **data}

    except Exception as e:
        print(f"[market_data] Batch fetch error: {e}")

    # ── Fallback: fill missing tickers from mock data ─────────────────────
    if len(results) < len(tickers) // 2:
        print("[market_data] Using mock data fallback for missing tickers")
        for p in ALL_ETF_UNIVERSE:
            ticker = p["id"]
            if ticker not in results and ticker in MOCK_DATA:
                results[ticker] = {**p, **MOCK_DATA[ticker]}

    cache_manager.set(_batch_cache_key, results)
    return results

def fetch_ticker_data(ticker: str) -> dict:
    """Return cached/fetched data for a single ticker (uses batch cache)."""
    single_key = f"prices_{ticker}"
    cached = cache_manager.get(single_key)
    if cached:
        return cached

    # Try batch first (preferred)
    batch = fetch_all_batch()
    if ticker in batch:
        return batch[ticker]

    # Last resort: individual fetch
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if hist.empty:
            return {}
        close  = hist["Close"]
        volume = hist["Volume"]
        result = {
            "ticker": ticker,
            "current_price": round(float(close.iloc[-1]), 2),
            "returns": {
                "d1": _pct_change(close, 1),
                "w1": _pct_change(close, 5),
                "m1": _pct_change(close, 21),
                "m3": _pct_change(close, 63),
                "m6": _pct_change(close, 126),
                "y1": _pct_change(close, 252),
            },
            "volatility_annual": _annualised_vol(close),
            "avg_volume_30d": round(float(volume.iloc[-30:].mean()), 0) if len(volume) >= 30 else None,
            "data_points": len(close),
        }
        cache_manager.set(single_key, result)
        return result
    except Exception as e:
        print(f"[market_data] Single fetch error {ticker}: {e}")
        return {}

def fetch_all_etfs() -> Dict[str, dict]:
    return fetch_all_batch()

def fetch_nifty50_info() -> dict:
    """Fetch Nifty 50 index level for macro context."""
    cache_key = "prices_NIFTY50"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    try:
        tk = yf.Ticker("^NSEI")
        hist = tk.history(period="5d", interval="1d", auto_adjust=True)
        if hist.empty:
            return {}
        result = {
            "level": round(float(hist["Close"].iloc[-1]), 2),
            "change_1d": _pct_change(hist["Close"], 1),
        }
        cache_manager.set(cache_key, result, ttl=900)
        return result
    except Exception:
        return {}

def fetch_usdinr() -> Optional[float]:
    """Fetch USD/INR exchange rate."""
    cache_key = "prices_USDINR"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    try:
        tk = yf.Ticker("INR=X")
        hist = tk.history(period="2d", interval="1d")
        if hist.empty:
            return None
        rate = round(float(hist["Close"].iloc[-1]), 2)
        cache_manager.set(cache_key, rate, ttl=900)
        return rate
    except Exception:
        return None
