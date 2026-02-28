"""
Gold & Silver spot prices in INR from:
  - IBJA rates (ibjarates.com) — official RBI-mandated benchmark
  - yfinance fallback (GOLDBEES.NS NAV ≈ gold price proxy)
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from app.cache import cache_manager

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
}

# ── IBJA scraper ──────────────────────────────────────────────────────────────

def _scrape_ibja() -> Optional[Dict]:
    """Scrape current gold & silver rate from ibjarates.com."""
    try:
        resp = requests.get("https://ibjarates.com/", headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")

        # IBJA publishes rates in a table — parse gold 999 and silver 999
        gold_inr = silver_inr = None

        # Look for rate table rows
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                text = " ".join(cells).lower()
                if "999" in text and "gold" in text:
                    for cell in cells:
                        cleaned = cell.replace(",", "").replace("₹", "").strip()
                        try:
                            val = float(cleaned)
                            if 50000 < val < 200000:   # reasonable gold per 10g range
                                gold_inr = val
                        except ValueError:
                            pass
                if "silver" in text and "999" in text:
                    for cell in cells:
                        cleaned = cell.replace(",", "").replace("₹", "").strip()
                        try:
                            val = float(cleaned)
                            if 50000 < val < 200000:   # silver per kg
                                silver_inr = val
                        except ValueError:
                            pass

        if gold_inr:
            return {"gold_per_10g": gold_inr, "silver_per_kg": silver_inr, "source": "IBJA"}
        return None

    except Exception as e:
        print(f"[gold_silver] IBJA scrape error: {e}")
        return None

# ── yfinance fallback ─────────────────────────────────────────────────────────

def _from_yfinance() -> Dict:
    """Use GOLDBEES NAV as gold price proxy (1 unit ≈ 1g gold)."""
    try:
        import yfinance as yf
        tk = yf.Ticker("GOLDBEES.NS")
        hist = tk.history(period="2d", interval="1d", auto_adjust=True)
        if not hist.empty:
            nav_per_unit = float(hist["Close"].iloc[-1])
            # GOLDBEES tracks ~0.01g/unit — scale to 10g
            # Actual: 1 unit ≈ 1/100th of 10g gold, so 10g = 100 units
            gold_10g = round(nav_per_unit * 100, 2)
            return {"gold_per_10g": gold_10g, "silver_per_kg": None, "source": "yfinance/GOLDBEES proxy"}
    except Exception:
        pass
    # Final fallback: last known rate
    return {"gold_per_10g": 82500.0, "silver_per_kg": 96000.0, "source": "static fallback"}

# ── Public API ────────────────────────────────────────────────────────────────

def get_gold_silver_rates() -> Dict:
    cache_key = "gold_rates"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    rates = _scrape_ibja() or _from_yfinance()
    cache_manager.set(cache_key, rates)
    return rates
