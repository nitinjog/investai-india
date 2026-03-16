"""
Market data — NSE (.NS) ETF prices and returns.

Data source priority:
  1. yfinance batch download (full 1-year OHLCV history)
  2. MFapi.in (official AMFI NAV history — reliable from cloud hosts)
  3. Mock data (static fallback — labelled "mock" so UI can warn user)

Falls back gracefully so the app always returns a result.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.cache import cache_manager

# ── Realistic mock data (approximate — used only when live feeds fail) ─────────
# price_source = "mock" so the frontend can show an "estimated" badge.
MOCK_DATA_DATE = "2026-02-15"   # approximate data vintage
def _mock(price, returns, vol, vol30d):
    return {"current_price": price, "returns": returns, "volatility_annual": vol,
            "avg_volume_30d": vol30d, "price_source": "mock", "price_date": MOCK_DATA_DATE}

MOCK_DATA: Dict[str, dict] = {
    # Gold ETFs — gold ~₹88,000/10g (Mar 2026)
    "GOLDBEES.NS":   _mock(65.20,  {"d1": 0.25,  "w1": 1.52,  "m1": 3.40,  "m3": 9.20,  "m6": 14.10, "y1": 21.50}, 14.2, 850000),
    "BSLGOLDETF.NS": _mock(63.50,  {"d1": 0.23,  "w1": 1.50,  "m1": 3.36,  "m3": 9.15,  "m6": 14.00, "y1": 21.40}, 14.3, 120000),
    "AXISGOLD.NS":   _mock(23.80,  {"d1": 0.22,  "w1": 1.48,  "m1": 3.32,  "m3": 9.10,  "m6": 13.90, "y1": 21.30}, 14.5, 95000),
    "KOTAKGOLD.NS":  _mock(25.10,  {"d1": 0.24,  "w1": 1.51,  "m1": 3.38,  "m3": 9.18,  "m6": 14.05, "y1": 21.45}, 14.1, 180000),
    "HDFCMFGETF.NS": _mock(64.80,  {"d1": 0.25,  "w1": 1.53,  "m1": 3.42,  "m3": 9.22,  "m6": 14.12, "y1": 21.52}, 14.2, 210000),
    # Silver ETF
    "SILVERBEES.NS": _mock(98.40,  {"d1": 0.50,  "w1": 2.30,  "m1": 5.10,  "m3": 11.40, "m6": 17.50, "y1": 27.20}, 22.1, 420000),
    "KOTAKSILVER.NS":_mock(99.80,  {"d1": 0.48,  "w1": 2.28,  "m1": 5.05,  "m3": 11.35, "m6": 17.40, "y1": 27.00}, 22.3, 85000),
    # Nifty ETFs — Nifty 50 ~22,800 (Mar 2026)
    "NIFTYBEES.NS":  _mock(228.50, {"d1": 0.30,  "w1": 1.10,  "m1": 2.40,  "m3": 5.80,  "m6": 8.50,  "y1": 13.20}, 16.5, 3200000),
    "ICICINIFTY.NS": _mock(226.20, {"d1": 0.29,  "w1": 1.08,  "m1": 2.38,  "m3": 5.75,  "m6": 8.45,  "y1": 13.12}, 16.6, 450000),
    "KOTAKNIFTY.NS": _mock(135.80, {"d1": 0.28,  "w1": 1.06,  "m1": 2.35,  "m3": 5.70,  "m6": 8.40,  "y1": 13.05}, 16.7, 280000),
    "SETFNIF50.NS":  _mock(229.80, {"d1": 0.31,  "w1": 1.12,  "m1": 2.42,  "m3": 5.82,  "m6": 8.52,  "y1": 13.25}, 16.4, 1100000),
    "JUNIORBEES.NS": _mock(640.20, {"d1": 0.38,  "w1": 1.35,  "m1": 3.10,  "m3": 7.40,  "m6": 11.20, "y1": 16.80}, 20.2, 180000),
    # Sector ETFs
    "BANKBEES.NS":   _mock(448.60, {"d1": 0.45,  "w1": 1.55,  "m1": 3.60,  "m3": 8.20,  "m6": 12.10, "y1": 10.50}, 24.1, 920000),
    "ITBEES.NS":     _mock(42.80,  {"d1": 0.35,  "w1": 1.20,  "m1": 2.80,  "m3": 6.80,  "m6": 10.40, "y1": 24.80}, 23.5, 610000),
    "PHARMABEES.NS": _mock(25.40,  {"d1": 0.22,  "w1": 1.05,  "m1": 2.40,  "m3": 7.00,  "m6": 12.80, "y1": 30.20}, 21.8, 185000),
    "AUTOBEES.NS":   _mock(185.20, {"d1": 0.55,  "w1": 1.85,  "m1": 4.20,  "m3": 9.80,  "m6": 14.20, "y1": 18.40}, 26.4, 92000),
    "INFRABEES.NS":  _mock(39.80,  {"d1": 0.42,  "w1": 1.45,  "m1": 3.40,  "m3": 8.60,  "m6": 13.20, "y1": 17.10}, 25.2, 68000),
    "CONSUMBEES.NS": _mock(82.50,  {"d1": 0.28,  "w1": 1.00,  "m1": 2.20,  "m3": 5.20,  "m6": 7.80,  "y1": 12.40}, 18.9, 48000),
    "PSUBNKBEES.NS": _mock(58.40,  {"d1": 0.65,  "w1": 2.15,  "m1": 4.90,  "m3": 11.00, "m6": 15.80, "y1": 6.20},  30.5, 380000),
    "MOM100.NS":     _mock(68.20,  {"d1": 0.45,  "w1": 1.62,  "m1": 3.80,  "m3": 9.20,  "m6": 14.80, "y1": 22.10}, 22.8, 210000),
    # REITs
    "EMBASSY.NS":    _mock(318.50, {"d1": 0.15,  "w1": 0.55,  "m1": 1.50,  "m3": 3.60,  "m6": 5.80,  "y1": 8.20},  12.4, 280000),
    "MINDSPACE.NS":  _mock(290.80, {"d1": 0.12,  "w1": 0.48,  "m1": 1.35,  "m3": 3.30,  "m6": 5.20,  "y1": 7.50},  13.1, 185000),
    "BROOKFIELD.NS": _mock(268.40, {"d1": 0.18,  "w1": 0.62,  "m1": 1.80,  "m3": 4.20,  "m6": 6.50,  "y1": 10.20}, 14.8, 92000),
    "NEXUS.NS":      _mock(130.20, {"d1": 0.22,  "w1": 0.75,  "m1": 2.10,  "m3": 4.80,  "m6": 7.50,  "y1": 11.80}, 15.2, 78000),
    # InvITs
    "INDIGRID.NS":   _mock(140.50, {"d1": 0.10,  "w1": 0.42,  "m1": 1.20,  "m3": 2.80,  "m6": 5.20,  "y1": 7.80},  11.2, 145000),
    "POWERGRD.NS":   _mock(90.20,  {"d1": 0.08,  "w1": 0.36,  "m1": 1.05,  "m3": 2.40,  "m6": 4.60,  "y1": 6.90},  10.8, 210000),
    "IRB.NS":        _mock(57.80,  {"d1": 0.12,  "w1": 0.48,  "m1": 1.40,  "m3": 3.20,  "m6": 5.80,  "y1": 8.50},  13.5, 88000),
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
        close = df_close[ticker].dropna()
        if len(close) < 5:
            return {}
        avg_vol = None
        if not df_volume.empty and ticker in df_volume.columns:
            vol = df_volume[ticker].dropna()
            if len(vol) >= 30:
                avg_vol = round(float(vol.iloc[-30:].mean()), 0)
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
            "avg_volume_30d": avg_vol,
            "data_points": len(close),
            "price_source": "live_yfinance",
            "price_date": close.index[-1].strftime("%d %b %Y") if hasattr(close.index[-1], 'strftime') else "",
        }
        return result
    except Exception:
        return {}

def fetch_all_batch() -> Dict[str, dict]:
    """
    Fetch all ETF universe prices/returns using a three-tier fallback:
      1. yfinance batch (full OHLCV history — best when available)
      2. MFapi.in     (official AMFI NAV history — works from cloud hosts)
      3. Mock data    (static approximation — last resort)
    """
    cached = cache_manager.get(_batch_cache_key)
    if cached:
        return cached

    tickers = [p["id"] for p in ALL_ETF_UNIVERSE]
    results: Dict[str, dict] = {}

    # ── Tier 1: yfinance batch ─────────────────────────────────────────────
    try:
        raw = yf.download(
            tickers=tickers,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="column",
        )

        if not raw.empty and isinstance(raw.columns, pd.MultiIndex):
            # Handle both (Price, Ticker) and (Ticker, Price) MultiIndex orderings
            level0 = raw.columns.get_level_values(0).unique().tolist()
            if "Close" in level0:
                df_close  = raw["Close"]
                df_volume = raw["Volume"] if "Volume" in level0 else pd.DataFrame()
            else:
                # Swap levels (newer yfinance versions changed the order)
                swapped   = raw.swaplevel(axis=1).sort_index(axis=1)
                level0s   = swapped.columns.get_level_values(0).unique().tolist()
                df_close  = swapped["Close"]  if "Close"  in level0s else pd.DataFrame()
                df_volume = swapped["Volume"] if "Volume" in level0s else pd.DataFrame()

            for p in ALL_ETF_UNIVERSE:
                ticker = p["id"]
                if not df_close.empty and ticker in df_close.columns:
                    data = _parse_ticker_from_batch(ticker, df_close, df_volume)
                    if data:
                        results[ticker] = {**p, **data}

        elif not raw.empty and not isinstance(raw.columns, pd.MultiIndex):
            # Single-ticker edge case
            df_close  = raw[["Close"]].rename(columns={"Close": tickers[0]})
            df_volume = raw[["Volume"]].rename(columns={"Volume": tickers[0]}) if "Volume" in raw.columns else pd.DataFrame()
            data = _parse_ticker_from_batch(tickers[0], df_close, df_volume)
            if data:
                results[tickers[0]] = {**{p["id"]: p for p in ALL_ETF_UNIVERSE}.get(tickers[0], {}), **data}

        yf_count = len(results)
        if yf_count:
            print(f"[market_data] yfinance: {yf_count}/{len(tickers)} tickers")

    except Exception as e:
        print(f"[market_data] yfinance batch error: {e}")

    # ── Tier 2: MFapi.in for still-missing ETF tickers ────────────────────
    missing_after_yf = [p["id"] for p in ALL_ETF_UNIVERSE if p["id"] not in results]
    if missing_after_yf:
        try:
            from app.data.mfapi_nav import fetch_all_from_mfapi
            mfapi_data = fetch_all_from_mfapi(missing_after_yf)
            meta_map   = {p["id"]: p for p in ALL_ETF_UNIVERSE}
            for ticker, data in mfapi_data.items():
                results[ticker] = {**meta_map.get(ticker, {}), **data}
            if mfapi_data:
                print(f"[market_data] MFapi: {len(mfapi_data)} additional tickers")
        except Exception as e:
            print(f"[market_data] MFapi fallback error: {e}")

    # ── Tier 3: Mock data for still-missing tickers ────────────────────────
    missing_after_mfapi = [p for p in ALL_ETF_UNIVERSE if p["id"] not in results]
    if missing_after_mfapi:
        print(f"[market_data] Mock fallback for {len(missing_after_mfapi)} tickers")
        for p in missing_after_mfapi:
            ticker = p["id"]
            if ticker in MOCK_DATA:
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
