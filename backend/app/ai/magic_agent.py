"""
Magic Investment Agent — uses Google Gemini to autonomously allocate funds
across top-ranked products and explain reasoning in plain English.
"""
import os
import json
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from app.cache import cache_manager

MODEL = "gemini-2.0-flash"

# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(
    amount: float,
    duration_days: int,
    duration_label: str,
    products: List[dict],
    macro: dict,
    risk_appetite: str,
) -> str:
    products_summary = []
    for i, p in enumerate(products, 1):
        s = p.get("scores", {})
        products_summary.append(
            f"{i}. {p['name']} ({p['category'].replace('_', ' ').title()})\n"
            f"   Overall score: {s.get('overall', 0)}/100\n"
            f"   1Y return: {p.get('returns', {}).get('y1', 'N/A')}%\n"
            f"   Yield: {p.get('current_rate') or p.get('current_yield') or p.get('dist_yield', 'N/A')}%\n"
            f"   Trend score: {s.get('trend', 0)}/100, Sentiment: {s.get('sentiment', 0)}/100\n"
            f"   Duration fit: {s.get('duration_fit', 0)}/100\n"
            f"   Key drivers: {', '.join(p.get('key_drivers', [])[:2])}"
        )

    macro_summary = (
        f"RBI Repo Rate: {macro.get('repo_rate', 6.5)}% ({macro.get('rate_trend', 'neutral')} cycle)\n"
        f"CPI Inflation: {macro.get('cpi_latest', 5.2)}%\n"
        f"GDP Growth: {macro.get('gdp_growth', 6.4)}%\n"
        f"Real Rate: {macro.get('real_rate', 1.3)}%"
    )

    return f"""You are an expert Indian investment advisor. A retail investor in India wants to invest.

INVESTOR PROFILE:
- Amount: ₹{amount:,.0f}
- Investment horizon: {duration_label} ({duration_days} days)
- Risk appetite: {risk_appetite}

CURRENT MACROECONOMIC ENVIRONMENT (India):
{macro_summary}

TOP RANKED INVESTMENT PRODUCTS (by quantitative score):
{chr(10).join(products_summary)}

YOUR TASK:
Based on the investor's profile and macro environment, decide the optimal allocation across these products.
You may recommend 1 product (concentrated) or a mix (diversified).

Rules:
- Allocations must sum to exactly 100%
- Minimum allocation per product: 15%
- Maximum per product: 70% (unless single-product recommendation)
- Prefer products with duration_fit > 60 for the given horizon
- Consider tax efficiency (STCG vs LTCG for ETFs, interest tax for FDs)
- FDs: interest fully taxable at slab rate
- ETFs held > 1 year: LTCG at 10% above ₹1L (equity ETFs), 20% with indexation (gold/debt)
- REITs/InvITs: 90% of distributions are tax-free dividends

Respond ONLY with valid JSON in this exact format:
{{
  "allocation": [
    {{
      "product_id": "...",
      "product_name": "...",
      "percentage": 40,
      "amount_inr": {int(amount * 0.4)},
      "reasoning": "2-3 sentence rationale"
    }}
  ],
  "overall_reasoning": "3-4 sentences explaining the overall strategy",
  "confidence": 72,
  "expected_return_min": 8.5,
  "expected_return_max": 13.0,
  "risks": ["Risk 1", "Risk 2", "Risk 3"],
  "tax_note": "Brief tax efficiency note"
}}"""

# ── Gemini call ───────────────────────────────────────────────────────────────

def run_magic_agent(
    amount: float,
    duration_days: int,
    duration_label: str,
    products: List[dict],
    macro: dict,
    risk_appetite: str = "medium",
) -> Optional[Dict]:
    """
    Call Gemini to produce allocation JSON.
    Returns parsed dict or None on failure.
    """
    cache_key = f"magic_{int(amount)}_{duration_days}_{risk_appetite}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return _fallback_allocation(products, amount)

    try:
        prompt = _build_prompt(amount, duration_days, duration_label, products, macro, risk_appetite)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
        cache_manager.set(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        print(f"[magic_agent] Gemini error: {e}")
        return _fallback_allocation(products, amount)

# ── Fallback without Gemini ───────────────────────────────────────────────────

def _fallback_allocation(products: List[dict], amount: float) -> Dict:
    """Rule-based allocation when Gemini is unavailable."""
    if not products:
        return {}

    n = min(3, len(products))
    top = products[:n]
    weights = [50, 30, 20][:n]
    # Normalise
    total_w = sum(weights)
    weights = [w / total_w * 100 for w in weights]

    allocation = []
    for prod, pct in zip(top, weights):
        allocation.append({
            "product_id":   prod["id"],
            "product_name": prod["name"],
            "percentage":   round(pct),
            "amount_inr":   round(amount * pct / 100),
            "reasoning":    f"Top ranked with overall score {prod['scores']['overall']}/100.",
        })

    return {
        "allocation": allocation,
        "overall_reasoning": "Rule-based allocation based on quantitative scores. Enable Gemini for AI-powered reasoning.",
        "confidence": 60,
        "expected_return_min": 7.0,
        "expected_return_max": 12.0,
        "risks": ["Market risk", "Inflation risk", "Liquidity risk"],
        "tax_note": "Consult a tax advisor for personalised guidance.",
    }
