# Daily Investment Advisor — India
## Project Context (Session Snapshot — Mar 2026)

---

## What Was Built

A full-stack AI-powered investment advisor web app for Indian retail investors.

**User flow:**
1. User enters investment amount (₹), duration (days/months/years), risk appetite
2. Backend fetches live data from Indian financial sources
3. Scores 40+ products across 7 asset classes using an 8-factor quantitative model
4. Returns top 5 ranked recommendations with scores, returns, drivers, risks
5. Optional "Magic Mode": Gemini AI allocates funds and explains reasoning
6. Results page shows a data quality banner (Live / Partial / Estimated) and per-card Live/Est. badge

---

## Tech Stack

| Layer | Tech | Hosting |
|-------|------|---------|
| Frontend | React 18 + Vite + Tailwind CSS | Netlify |
| Backend | Python 3.13 + FastAPI | Render |
| AI | Google Gemini 2.0 Flash | Gemini API |
| Data | yfinance, MFapi.in, AMFI, RBI DBIE, GDELT, RSS | Free / no key |

---

## Project Structure

```
C:/Users/KGS/investai/
├── .gitignore
├── CONTEXT.md                  ← this file
├── CLAUDE.md                   ← Claude Code instructions
│
├── backend/
│   ├── .env                    ← GEMINI_API_KEY set here (local only)
│   ├── .env.example
│   ├── requirements.txt
│   ├── render.yaml             ← Render deployment config
│   └── app/
│       ├── main.py             ← FastAPI entry point, CORS config
│       ├── models/
│       │   ├── request.py      ← RecommendRequest pydantic model
│       │   └── response.py     ← RecommendResponse, Product, Scores, etc.
│       ├── cache/
│       │   └── cache_manager.py ← In-memory TTL cache (no Redis needed)
│       ├── data/
│       │   ├── market_data.py  ← 3-tier ETF fetch: yfinance → MFapi → mock
│       │   ├── mfapi_nav.py    ← MFapi.in live NAV fetcher (primary on Render)
│       │   ├── fd_rates.py     ← FD rates (updated Mar 2026, post rate cut)
│       │   ├── macro_data.py   ← RBI DBIE + World Bank + MOSPI
│       │   ├── news_data.py    ← GDELT + India RSS feeds (ET, BS, Mint)
│       │   └── gold_silver.py  ← IBJA scraping + yfinance fallback
│       ├── analysis/
│       │   ├── scoring_engine.py  ← Master scorer, calls all sub-engines
│       │   ├── trend_engine.py    ← SMA/RSI/MACD technical analysis
│       │   ├── sentiment_engine.py ← GDELT + RSS headline sentiment
│       │   └── duration_model.py  ← Duration-suitability matrix
│       ├── ai/
│       │   ├── magic_agent.py     ← Gemini allocation agent
│       │   └── explanation_gen.py ← Per-product explanation (fallback mode)
│       └── routers/
│           ├── recommend.py    ← POST /api/recommend
│           └── assets.py       ← GET /api/assets/{category}
│
└── frontend/
    ├── .env                    ← VITE_API_URL=http://localhost:8000
    ├── .env.example
    ├── package.json            ← React 18, Vite 5, Tailwind 3, Recharts
    ├── vite.config.js          ← Proxy /api → localhost:8000
    ├── tailwind.config.js      ← Custom colors: saffron, indgreen, navy, gold
    ├── netlify.toml            ← Netlify build + redirect config
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx             ← Routes: / and /results
        ├── index.css           ← Tailwind + custom component classes
        ├── components/
        │   ├── Navbar.jsx
        │   ├── InvestForm.jsx  ← Amount + duration presets + risk + magic toggle
        │   ├── MagicToggle.jsx ← Gemini AI mode toggle
        │   ├── ResultCard.jsx  ← Per-product card; shows Live/Est. badge on price
        │   ├── ScoreBar.jsx    ← Score visualizer + ScoreGrid
        │   ├── ReturnsTable.jsx ← 1D/1W/1M/3M/6M/1Y returns
        │   └── LoadingState.jsx ← Animated loading steps
        ├── pages/
        │   ├── Home.jsx        ← Landing page with form + feature list
        │   └── Results.jsx     ← Results page; data quality banner + macro strip
        ├── hooks/
        │   └── useRecommendations.js ← axios POST hook
        └── utils/
            └── formatters.js   ← formatINR, formatPct, categoryLabel, etc.
```

---

## API Endpoints

```
GET  /                         → health check
GET  /health                   → cache stats
GET  /docs                     → Swagger UI
POST /api/recommend            → main recommendation endpoint
GET  /api/assets/{category}   → list products in category
GET  /api/assets              → list all categories
```

### POST /api/recommend

Request:
```json
{
  "amount": 100000,
  "duration_value": 1,
  "duration_unit": "years",     // "days" | "months" | "years"
  "magic_mode": false,
  "risk_appetite": "medium"    // "low" | "medium" | "high"
}
```

Response: `RecommendResponse` with top 5 `Product` objects, `MacroContext`, optional `MagicAllocation`,
plus `data_quality` (`"live"` | `"partial"` | `"mock"`) and `price_data_as_of` (date string).

Each `Product.extra` carries `price_source` and `price_date` for per-card display.

---

## Scoring Engine — 8 Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| performance | 22% | Weighted 1d–1y returns vs category ceiling |
| trend | 15% | SMA50/200 crossover, RSI, MACD, volume |
| macro | 15% | RBI rate env, GDP, CPI per asset class |
| sentiment | 10% | GDELT tone + RSS keyword scoring |
| yield_score | 13% | FD rate / dist yield / bond YTM |
| stability | 10% | Inverse of annualised volatility |
| liquidity | 5% | Volume-based, category defaults |
| duration_fit | 10% | Duration-suitability matrix |

---

## Asset Universe

### ETFs (NSE tickers)
- **Gold:** GOLDBEES.NS, BSLGOLDETF.NS, AXISGOLD.NS
- **Silver:** SILVERBEES.NS
- **Nifty 50:** NIFTYBEES.NS, SETFNIF50.NS, JUNIORBEES.NS
- **Sector:** BANKBEES.NS, ITBEES.NS, PHARMABEES.NS, AUTOBEES.NS, INFRABEES.NS, CONSUMBEES.NS, PSUBNKBEES.NS, MOM100.NS
- **REITs:** EMBASSY.NS, MINDSPACE.NS
- **InvITs:** INDIGRID.NS, IRB.NS

### Fixed Deposits (rates updated Mar 2026)
SBI, PNB, HDFC, ICICI, Axis, Kotak, Yes Bank, IDFC First, AU SFB, Ujjivan SFB, Bajaj Finance, Shriram Finance, Mahindra Finance

---

## ETF Data Pipeline — 3-Tier Fallback

| Tier | Source | Coverage | When Used |
|------|--------|----------|-----------|
| 1 | **yfinance** | All 19 tickers — full OHLCV 1Y | Works locally; blocked on Render |
| 2 | **MFapi.in** | 14 ETFs (not REITs/InvITs/ITBEES) | Primary on Render |
| 3 | **Mock data** | All tickers — approx Mar 2026 prices | Last resort only |

`price_source` field on each product: `"live_yfinance"` | `"live_mfapi"` | `"mock"`

### MFapi.in AMFI Scheme Codes (hardcoded in mfapi_nav.py)
| Ticker | AMFI Code |
|--------|-----------|
| GOLDBEES.NS | 140088 |
| BSLGOLDETF.NS | 115127 |
| AXISGOLD.NS | 113434 |
| SILVERBEES.NS | 149758 |
| NIFTYBEES.NS | 140084 |
| SETFNIF50.NS | 135106 |
| JUNIORBEES.NS | 140085 |
| BANKBEES.NS | 140087 |
| PHARMABEES.NS | 149008 |
| AUTOBEES.NS | 149465 |
| INFRABEES.NS | 140102 |
| CONSUMBEES.NS | 128331 |
| PSUBNKBEES.NS | 140089 |
| MOM100.NS | 114456 |

---

## Data Sources (all free, India-specific)

| Source | Data | Key? |
|--------|------|------|
| yfinance | NSE/BSE OHLCV, 1Y history | No |
| **MFapi.in** | ETF NAV history (primary on Render) | No |
| AMFI India | Daily NAV (MFapi mirrors this) | No |
| RBI DBIE | Repo rate, CPI, forex | No |
| World Bank API | India GDP, macro | No |
| MOSPI | CPI, IIP | No |
| GDELT Project API | News sentiment (−100 to +100) | No |
| Economic Times RSS | India market news | No |
| Business Standard RSS | India market news | No |
| Livemint RSS | India market news | No |
| ibjarates.com | Gold/Silver INR (scraped) | No |
| **Google Gemini 2.0 Flash** | Magic AI mode | **YES** |

---

## Macro Snapshot (as of Mar 2026)

| Indicator | Value | Source |
|-----------|-------|--------|
| RBI Repo Rate | **6.25%** | RBI MPC cut 25bps in Feb 2026 |
| CPI Inflation | ~4.95% YoY | RBI/MOSPI |
| GDP Growth | ~6.4% | World Bank estimate |
| Rate Trend | Easing | First cut since 2020 |
| FD Rates | Reduced ~20-25bps | Banks passing on rate cut |

---

## API Keys

| Key | Variable | Status |
|-----|----------|--------|
| Gemini API | `GEMINI_API_KEY` | Set in `backend/.env` |

**Gemini key:** stored in `backend/.env` (not committed to git)
**Note:** Free tier = 15 req/min, 1,500 req/day. Magic mode uses 1 call/request.

---

## GitHub Credentials (for deployment)

| Field | Value |
|-------|-------|
| GitHub username | `nitinjog` |
| GitHub PAT | *(stored locally — not committed)* |
| Target repo | `https://github.com/nitinjog/investai-india` |
| Netlify token | *(stored locally — not committed)* |
| Render API key | *(stored locally — not committed)* |

---

## Deployment Status (as of Mar 2026 — COMPLETE)

| Step | Status | Notes |
|------|--------|-------|
| GitHub repo created | ✅ Done | `nitinjog/investai-india` |
| Git init + commit | ✅ Done | branch: `main` |
| GitHub push | ✅ Done | `https://github.com/nitinjog/investai-india` |
| Render deploy | ✅ LIVE | `https://investai-india-backend.onrender.com` |
| Netlify deploy | ✅ LIVE | `https://investai-india.netlify.app` |
| Live data fix | ✅ Done | MFapi.in added as tier-2 source (Mar 2026) |

### Live URLs
- **Frontend:** https://investai-india.netlify.app
- **Backend API:** https://investai-india-backend.onrender.com
- **Swagger docs:** https://investai-india-backend.onrender.com/docs

### Render service details
- Service ID: `srv-d6hv703uibrs73a52lh0`
- Region: Singapore
- Python: 3.11.9 (set via PYTHON_VERSION env var)
- Auto-deploy: enabled (pushes to main trigger redeploy)

### Netlify site details
- Site ID: `fe5270c6-3a76-4800-a17b-0680256cd802`
- VITE_API_URL baked into build: `https://investai-india-backend.onrender.com`

### To redeploy (after code changes):
```bash
# Push code → Render auto-redeploys backend
cd C:/Users/KGS/investai
git add -A && git commit -m "..." && git push

# Rebuild + redeploy frontend to Netlify
cd frontend
npm run build
npx netlify deploy --prod --dir=dist --auth=nfp_HmaiUAx63QNdoc5bByzydvuWLi6zBaKi06ab --site=fe5270c6-3a76-4800-a17b-0680256cd802
```

---

## Local Run Commands

```bash
# Terminal 1 — Backend
cd C:/Users/KGS/investai/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd C:/Users/KGS/investai/frontend
npm run dev
# Opens at http://localhost:5173 (or next available port)

# API health check
curl http://localhost:8000/
curl http://localhost:8000/docs   # Swagger UI

# Test recommendation
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"amount":100000,"duration_value":1,"duration_unit":"years","magic_mode":false,"risk_appetite":"medium"}'
```

---

## Known Issues / Watch Points

1. **yfinance blocked on Render** — Yahoo Finance blocks Render server IPs.
   App now falls back to MFapi.in (tier 2) for 14/19 ETFs automatically.
   REITs, InvITs, and ITBEES still use mock data on Render.

2. **MFapi high returns for some ETFs** — SILVERBEES shows ~164% 1y return due to
   possible fund restructuring in the NAV history. This is official AMFI data.
   The split-detection logic in mfapi_nav.py clips old pre-split data.

3. **Gemini rate limit** — Free tier: 15 req/min. If hit, Magic mode falls back
   to rule-based allocation. Wait 1 min and retry.

4. **Gemini per-product explanations disabled** — To save quota, per-product
   Gemini explanations use `_fallback_explanation()` (rule-based). Only the
   Magic mode allocation uses a live Gemini call.

5. **Mock data** — `MOCK_DATA` dict in `market_data.py` has approximate Mar 2026
   prices. Updated periodically. Frontend shows "Est." badge when mock is used.

6. **Sector ETF tickers** — Only Nippon India BeES series confirmed working on NSE.
   Removed: KOTAKGOLD, KOTAKNIFTY, ICICINIFTY, KOTAKSILVER, POWERGRD, NEXUS,
   HDFCMFGETF, BROOKFIELD (delisted or wrong ticker on yfinance/MFapi).

7. **Windows `nul` reserved name** — Never create files named `nul` on Windows.

---

## Features NOT yet built (future scope)

- [ ] Bond/NCD data (NSE bond platform scraper)
- [ ] Screener.in integration for ETF factsheets
- [ ] Historical recommendation tracking
- [ ] Portfolio allocation pie chart (Recharts)
- [ ] PDF export of recommendations
- [ ] WhatsApp/Email alert for daily top picks
- [ ] Multi-language support (Hindi)
- [ ] Dark mode
- [ ] Live FD rate scraping (currently static Mar 2026)
- [ ] Live REIT/InvIT prices when yfinance is unavailable

---

developed by            Nitin Nandrajog
