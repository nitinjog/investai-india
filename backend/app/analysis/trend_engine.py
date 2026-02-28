"""
Technical trend scoring for ETFs/REITs/InvITs using yfinance price data.
Uses: SMA crossover, RSI, price momentum, volume trend.
Returns a 0-100 trend score.
"""
import numpy as np
import pandas as pd
from typing import Optional
import yfinance as yf
from app.cache import cache_manager

# ── Technical helpers ─────────────────────────────────────────────────────────

def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()

def _rsi(series: pd.Series, period: int = 14) -> Optional[float]:
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def _macd_signal(close: pd.Series) -> float:
    """Return +1 (bullish), 0 (neutral), -1 (bearish) MACD crossover signal."""
    if len(close) < 26:
        return 0
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        return 1   # bullish crossover
    if macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        return -1  # bearish crossover
    if macd_line.iloc[-1] > signal_line.iloc[-1]:
        return 0.5  # above signal (bullish trend)
    return -0.5

def compute_trend_score(ticker: str) -> float:
    """
    Compute 0-100 trend score for an NSE/BSE ticker.
    Combines: SMA trend, RSI, MACD, momentum.
    """
    cache_key = f"trend_{ticker}"
    cached = cache_manager.get(cache_key)
    if cached is not None:
        return cached

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if hist.empty or len(hist) < 20:
            return 50.0

        close = hist["Close"]
        volume = hist["Volume"]

        score = 50.0

        # ── SMA crossover (50 vs 200) ─────────────────────────────────────
        sma50  = _sma(close, 50).iloc[-1]
        sma200 = _sma(close, 200).iloc[-1] if len(close) >= 200 else sma50
        current = close.iloc[-1]

        if current > sma50 > sma200:
            score += 15   # strong uptrend
        elif current > sma50:
            score += 8
        elif current < sma50 < sma200:
            score -= 15   # strong downtrend
        elif current < sma50:
            score -= 8

        # ── RSI ───────────────────────────────────────────────────────────
        rsi = _rsi(close)
        if rsi is not None:
            if 40 <= rsi <= 60:
                score += 5    # neutral zone — healthy
            elif rsi < 30:
                score += 12   # oversold = potential bounce
            elif rsi > 70:
                score -= 8    # overbought

        # ── MACD ─────────────────────────────────────────────────────────
        macd_sig = _macd_signal(close)
        score += macd_sig * 10

        # ── Price momentum (20-day) ───────────────────────────────────────
        if len(close) >= 21:
            mom = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100
            if mom > 5:
                score += 8
            elif mom > 0:
                score += 3
            elif mom < -10:
                score -= 10
            elif mom < 0:
                score -= 3

        # ── Volume trend ──────────────────────────────────────────────────
        if len(volume) >= 10:
            avg_vol_recent = volume.iloc[-5:].mean()
            avg_vol_base   = volume.iloc[-30:-5].mean() if len(volume) >= 30 else volume.mean()
            if avg_vol_base > 0:
                vol_ratio = avg_vol_recent / avg_vol_base
                if vol_ratio > 1.5:
                    score += 5   # rising volume
                elif vol_ratio < 0.5:
                    score -= 5

        result = round(min(100, max(0, score)), 1)
        cache_manager.set(cache_key, result)
        return result

    except Exception as e:
        print(f"[trend_engine] Error for {ticker}: {e}")
        return 50.0

def fd_trend_score(rate_trend: str) -> float:
    """FDs have no price trend — score based on interest rate direction."""
    if rate_trend == "easing":
        return 55.0    # rates may fall — lock in now is good
    elif rate_trend == "tightening":
        return 65.0    # rates rising — wait slightly, but locking in is ok
    return 50.0
