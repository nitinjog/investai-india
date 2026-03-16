"""POST /api/recommend — main recommendation endpoint."""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.models.request  import RecommendRequest
from app.models.response import RecommendResponse, Product, Returns, Scores, MacroContext, MagicAllocation
from app.analysis.scoring_engine import score_and_rank
from app.data.macro_data  import fetch_macro_context
from app.data.gold_silver import get_gold_silver_rates
from app.data.market_data import fetch_nifty50_info, fetch_usdinr
from app.ai.magic_agent     import run_magic_agent
from app.ai.explanation_gen import _fallback_explanation as get_explanation

router = APIRouter()

def _duration_label(req: RecommendRequest) -> str:
    val = int(req.duration_value)
    unit = req.duration_unit
    if unit == "days":
        return f"{val} day{'s' if val > 1 else ''}"
    elif unit == "months":
        return f"{val} month{'s' if val > 1 else ''}"
    else:
        return f"{val} year{'s' if val > 1 else ''}"

def _build_product(raw: dict, amount: float, duration_label: str) -> Product:
    r = raw.get("returns", {})
    s = raw.get("scores", {})
    return Product(
        id=raw["id"],
        name=raw["name"],
        category=raw["category"],
        issuer=raw.get("issuer"),
        current_price=raw.get("current_price"),
        current_rate=raw.get("current_rate") or raw.get("applicable_rate"),
        current_yield=raw.get("dist_yield") or raw.get("current_yield"),
        returns=Returns(
            d1=r.get("d1"), w1=r.get("w1"), m1=r.get("m1"),
            m3=r.get("m3"), m6=r.get("m6"), y1=r.get("y1"),
        ),
        scores=Scores(
            overall=s.get("overall", 0),
            performance=s.get("performance", 0),
            trend=s.get("trend", 0),
            macro=s.get("macro", 0),
            sentiment=s.get("sentiment", 0),
            yield_score=s.get("yield_score", 0),
            stability=s.get("stability", 0),
            liquidity=s.get("liquidity", 0),
            duration_fit=s.get("duration_fit", 0),
        ),
        confidence=raw.get("confidence", 60),
        key_drivers=raw.get("key_drivers", []),
        risks=raw.get("risks", []),
        duration_suitability=raw.get("duration_suitability", ""),
        source_links=raw.get("source_links", []),
        extra={
            "explanation": get_explanation(raw),
            "price_source": raw.get("price_source", "unknown"),
            "price_date":   raw.get("price_date", ""),
        },
    )

@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    try:
        duration_days = req.duration_in_days()
        dur_label = _duration_label(req)

        # ── Score all products ─────────────────────────────────────────────
        ranked = score_and_rank(
            duration_days=duration_days,
            amount=req.amount,
            risk_appetite=req.risk_appetite or "medium",
            top_n=5,
        )

        if not ranked:
            raise HTTPException(status_code=503, detail="Unable to fetch market data. Try again shortly.")

        # ── Build macro context ────────────────────────────────────────────
        macro = fetch_macro_context()
        gold_rates = get_gold_silver_rates()
        nifty_info = fetch_nifty50_info()
        usd_inr    = fetch_usdinr()

        macro_ctx = MacroContext(
            rbi_repo_rate=macro.get("repo_rate"),
            cpi_inflation=macro.get("cpi_latest"),
            usd_inr=usd_inr,
            nifty50_pe=nifty_info.get("pe"),
            gold_price_inr=gold_rates.get("gold_per_10g"),
            silver_price_inr=gold_rates.get("silver_per_kg"),
            gdp_growth=macro.get("gdp_growth"),
        )

        # ── Magic mode ─────────────────────────────────────────────────────
        magic_alloc = None
        if req.magic_mode:
            raw_magic = run_magic_agent(
                amount=req.amount,
                duration_days=duration_days,
                duration_label=dur_label,
                products=ranked,
                macro=macro,
                risk_appetite=req.risk_appetite or "medium",
            )
            if raw_magic:
                # Attach suggested allocation % to each product
                alloc_map = {a["product_id"]: a for a in raw_magic.get("allocation", [])}
                for p in ranked:
                    if p["id"] in alloc_map:
                        a = alloc_map[p["id"]]
                        p["suggested_pct"]       = a.get("percentage")
                        p["suggested_allocation"] = a.get("amount_inr")

                magic_alloc = MagicAllocation(
                    overall_reasoning=raw_magic.get("overall_reasoning", ""),
                    confidence=raw_magic.get("confidence", 60),
                    expected_return_min=raw_magic.get("expected_return_min", 7.0),
                    expected_return_max=raw_magic.get("expected_return_max", 12.0),
                    risks=raw_magic.get("risks", []),
                )

        # ── Build response ─────────────────────────────────────────────────
        products = [_build_product(p, req.amount, dur_label) for p in ranked]

        # Determine overall data quality from price sources
        sources   = [p.get("price_source", "unknown") for p in ranked]
        live_set  = {"live_yfinance", "live_mfapi"}
        has_live  = any(s in live_set for s in sources)
        has_mock  = any(s == "mock" for s in sources)
        data_quality = "live" if (has_live and not has_mock) else ("partial" if has_live else "mock")

        price_dates = [p.get("price_date", "") for p in ranked if p.get("price_date")]
        price_as_of = price_dates[0] if price_dates else None

        return RecommendResponse(
            recommendations=products,
            macro_context=macro_ctx,
            magic_allocation=magic_alloc,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            duration_label=dur_label,
            amount=req.amount,
            data_sources=[
                "NSE India", "AMFI India", "MFapi.in", "yfinance",
                "RBI DBIE", "World Bank", "GDELT", "IBJA Rates",
                "Economic Times RSS", "Business Standard RSS",
            ],
            data_quality=data_quality,
            price_data_as_of=price_as_of,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
