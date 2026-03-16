from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Returns(BaseModel):
    d1: Optional[float] = None    # 1-day %
    w1: Optional[float] = None    # 1-week %
    m1: Optional[float] = None    # 1-month %
    m3: Optional[float] = None    # 3-month %
    m6: Optional[float] = None    # 6-month %
    y1: Optional[float] = None    # 1-year %

class Scores(BaseModel):
    overall: float
    performance: float
    trend: float
    macro: float
    sentiment: float
    yield_score: float
    stability: float
    liquidity: float
    duration_fit: float

class Product(BaseModel):
    id: str
    name: str
    category: str                  # fd | gold_etf | silver_etf | nifty_etf | sector_etf | bond | reit | invit
    issuer: Optional[str] = None
    current_price: Optional[float] = None   # ₹ (for ETFs/REITs)
    current_rate: Optional[float] = None    # % (for FDs/bonds)
    current_yield: Optional[float] = None   # % distribution yield (REITs/InvITs)
    returns: Returns
    scores: Scores
    confidence: int                # 0-100
    key_drivers: List[str]
    risks: List[str]
    duration_suitability: str
    suggested_allocation: Optional[float] = None   # ₹ amount (magic mode)
    suggested_pct: Optional[float] = None          # % (magic mode)
    source_links: List[str] = []
    extra: Dict[str, Any] = {}

class MacroContext(BaseModel):
    rbi_repo_rate: Optional[float] = None
    cpi_inflation: Optional[float] = None
    usd_inr: Optional[float] = None
    nifty50_pe: Optional[float] = None
    gold_price_inr: Optional[float] = None   # per 10g
    silver_price_inr: Optional[float] = None  # per kg
    gdp_growth: Optional[float] = None

class MagicAllocation(BaseModel):
    overall_reasoning: str
    confidence: int
    expected_return_min: float
    expected_return_max: float
    risks: List[str]

class RecommendResponse(BaseModel):
    recommendations: List[Product]
    macro_context: MacroContext
    magic_allocation: Optional[MagicAllocation] = None
    analysis_timestamp: str
    duration_label: str
    amount: float
    data_sources: List[str] = []
    data_quality: str = "unknown"       # "live" | "partial" | "mock"
    price_data_as_of: Optional[str] = None   # ISO date or label
