"""GET /api/assets/{category} — returns live data for an asset category."""
from fastapi import APIRouter, HTTPException, Path
from app.data.market_data import (
    GOLD_ETFS, SILVER_ETFS, NIFTY_ETFS, SECTOR_ETFS, REITS, INVITS,
    fetch_ticker_data,
)
from app.data.fd_rates   import get_fd_rates
from app.data.gold_silver import get_gold_silver_rates
from app.data.macro_data  import fetch_macro_context

router = APIRouter()

CATEGORY_MAP = {
    "gold_etf":   GOLD_ETFS,
    "silver_etf": SILVER_ETFS,
    "nifty_etf":  NIFTY_ETFS,
    "sector_etf": SECTOR_ETFS,
    "reit":       REITS,
    "invit":      INVITS,
}

@router.get("/assets/{category}")
async def get_assets(
    category: str = Path(..., description="fd | gold_etf | silver_etf | nifty_etf | sector_etf | reit | invit | macro")
):
    category = category.lower()

    if category == "fd":
        return {"category": "fd", "products": get_fd_rates(365)}

    if category == "macro":
        macro = fetch_macro_context()
        gold  = get_gold_silver_rates()
        return {"category": "macro", "data": macro, "gold_silver": gold}

    if category not in CATEGORY_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category}. "
            f"Valid: fd, gold_etf, silver_etf, nifty_etf, sector_etf, reit, invit, macro")

    products_meta = CATEGORY_MAP[category]
    result = []
    for meta in products_meta:
        data = fetch_ticker_data(meta["id"])
        result.append({**meta, **data, "category": category})

    return {"category": category, "products": result, "count": len(result)}

@router.get("/assets")
async def list_categories():
    return {
        "categories": [
            {"id": "fd",         "label": "Fixed Deposits",         "count": 13},
            {"id": "gold_etf",   "label": "Gold ETFs",              "count": len(GOLD_ETFS)},
            {"id": "silver_etf", "label": "Silver ETFs",            "count": len(SILVER_ETFS)},
            {"id": "nifty_etf",  "label": "Nifty ETFs",             "count": len(NIFTY_ETFS)},
            {"id": "sector_etf", "label": "Sector / Thematic ETFs", "count": len(SECTOR_ETFS)},
            {"id": "reit",       "label": "REITs",                  "count": len(REITS)},
            {"id": "invit",      "label": "InvITs",                 "count": len(INVITS)},
            {"id": "macro",      "label": "Macro Indicators",       "count": 1},
        ]
    }
