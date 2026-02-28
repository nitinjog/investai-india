"""
Plain-English explanation generator using Google Gemini.
Takes a scored product and returns a concise, investor-friendly summary.
"""
import os
from google import genai
from google.genai import types
from typing import Optional
from app.cache import cache_manager

MODEL = "gemini-2.0-flash"

def generate_product_explanation(product: dict, duration_label: str, amount: float) -> str:
    """Generate a 2-3 sentence plain-English explanation for a product."""
    cache_key = f"explain_{product['id']}_{duration_label}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return _fallback_explanation(product)

    try:
        s = product.get("scores", {})
        prompt = f"""In 2-3 plain English sentences, explain to a retail Indian investor why
{product['name']} ({product['category'].replace('_', ' ')}) is recommended for a
₹{amount:,.0f} investment for {duration_label}.

Key facts:
- Overall score: {s.get('overall', 0)}/100
- 1-year return: {product.get('returns', {}).get('y1', 'N/A')}%
- Key drivers: {', '.join(product.get('key_drivers', []))}
- Duration suitability: {product.get('duration_suitability', '')}

Keep it simple, under 60 words. No jargon. Focus on why it's a good choice right now."""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=150),
        )
        text = response.text.strip()
        cache_manager.set(cache_key, text, ttl=3600)
        return text

    except Exception as e:
        print(f"[explanation_gen] Gemini error: {e}")
        return _fallback_explanation(product)

def _fallback_explanation(product: dict) -> str:
    cat = product.get("category", "")
    s = product.get("scores", {})
    overall = s.get("overall", 0)
    name = product.get("name", "This product")

    if cat == "fd":
        rate = product.get("current_rate", 7.0)
        return (f"{name} offers {rate}% guaranteed returns with capital safety. "
                f"It scores {overall}/100 overall, making it a strong choice for capital preservation.")
    elif cat in ("gold_etf", "silver_etf"):
        return (f"{name} provides exposure to precious metals — a traditional Indian wealth store. "
                f"With score {overall}/100, it offers inflation protection and portfolio diversification.")
    elif cat == "nifty_etf":
        return (f"{name} tracks India's top 50 companies, giving broad equity exposure. "
                f"Scoring {overall}/100, it's ideal for long-term wealth creation with low cost.")
    elif cat in ("reit", "invit"):
        dy = product.get("dist_yield", 8.0)
        return (f"{name} provides {dy}% distribution yield backed by real infrastructure assets. "
                f"Scoring {overall}/100, it combines income and growth for patient investors.")
    return (f"{name} scores {overall}/100 based on performance, trends, and macro conditions. "
            f"It is well-suited for the selected investment horizon.")
