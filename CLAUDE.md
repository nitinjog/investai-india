# CLAUDE.md — Daily Investment Advisor India

## Project
Full-stack Indian investment advisor app.
See `CONTEXT.md` for complete architecture, file structure, and deployment status.

## Working Directory
`C:/Users/KGS/investai/`

## Run Commands

```bash
# Backend (port 8000)
cd C:/Users/KGS/investai/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (port 5173+)
cd C:/Users/KGS/investai/frontend
npm run dev
```

## Key Files
- `backend/app/main.py` — FastAPI entry point
- `backend/app/analysis/scoring_engine.py` — core ranking logic
- `backend/app/data/market_data.py` — 3-tier ETF price fetch (yfinance → MFapi → mock)
- `backend/app/data/mfapi_nav.py` — MFapi.in live NAV fetcher (primary on Render)
- `backend/app/data/fd_rates.py` — Static FD rates (updated Mar 2026)
- `backend/app/data/macro_data.py` — RBI/GDP/CPI data
- `frontend/src/pages/Home.jsx` — main UI form
- `frontend/src/pages/Results.jsx` — results display with data quality banner
- `frontend/src/components/ResultCard.jsx` — per-product card with Live/Est. badge
- `CONTEXT.md` — full project context, credentials, deployment steps

## Environment Variables

### Backend (`backend/.env`)
```
GEMINI_API_KEY=AIzaSyCB3z11559fbH9znLBY9Hl7DkvwHi20l9k
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (`frontend/.env`)
```
VITE_API_URL=http://localhost:8000
```

## Deployment (LIVE — see CONTEXT.md for full steps)
- GitHub repo: `https://github.com/nitinjog/investai-india`
- Backend → Render: `https://investai-india-backend.onrender.com`
- Frontend → Netlify: `https://investai-india.netlify.app`

## Tech Stack
- Python 3.13 + FastAPI + uvicorn
- React 18 + Vite 5 + Tailwind CSS 3
- Google Gemini 2.0 Flash (google-genai SDK)
- yfinance + MFapi.in for NSE ETF market data

## Coding Conventions
- Backend: Python, snake_case, Pydantic v2 models
- Frontend: JSX, Tailwind utility classes, no TypeScript
- Cache: in-memory TTL (cache_manager.py) — no Redis
- All India-specific data sources only (no US APIs)

## ETF Data Pipeline (3-tier fallback)
1. **yfinance** — batch OHLCV, works locally; blocked on Render by Yahoo Finance
2. **MFapi.in** — official AMFI NAV history; works reliably from cloud; 14/19 ETFs covered
3. **Mock data** — approximate Mar 2026 prices; last resort for REITs/InvITs/ITBEES

Each product carries `price_source` (`"live_yfinance"` | `"live_mfapi"` | `"mock"`) and `price_date`.
Response carries `data_quality` (`"live"` | `"partial"` | `"mock"`).

## MFapi Scheme Codes (hardcoded in mfapi_nav.py)
| Ticker | Code | Name |
|--------|------|------|
| GOLDBEES.NS | 140088 | Nippon India ETF Gold BeES |
| BSLGOLDETF.NS | 115127 | Aditya Birla Sun Life Gold ETF |
| AXISGOLD.NS | 113434 | Axis Gold ETF |
| SILVERBEES.NS | 149758 | Nippon India Silver ETF |
| NIFTYBEES.NS | 140084 | Nippon India ETF Nifty 50 BeES |
| SETFNIF50.NS | 135106 | SBI Nifty 50 ETF |
| JUNIORBEES.NS | 140085 | Nippon India ETF Nifty Next 50 Junior BeES |
| BANKBEES.NS | 140087 | Nippon India ETF Nifty Bank BeES |
| PHARMABEES.NS | 149008 | Nippon India Nifty Pharma ETF |
| AUTOBEES.NS | 149465 | Nippon India Nifty Auto ETF |
| INFRABEES.NS | 140102 | Nippon India ETF Nifty Infrastructure BeES |
| CONSUMBEES.NS | 128331 | Nippon India ETF Nifty India Consumption |
| PSUBNKBEES.NS | 140089 | Nippon India ETF Nifty PSU Bank BeES |
| MOM100.NS | 114456 | Motilal Oswal Nifty Midcap 100 ETF |
| ITBEES.NS | — | Not on MFapi → uses mock data |

## Macro Data (as of Mar 2026)
- RBI Repo Rate: **6.25%** (cut 25bps at Feb 2026 MPC meeting)
- CPI: ~4.95% YoY | Rate trend: easing
- FD rates: updated Mar 2026 (post rate-cut, banks reduced ~20-25bps)

## Known Gotchas
- yfinance blocked by Yahoo Finance on Render → MFapi kicks in automatically
- MFapi NAV data may show high returns for some ETFs (e.g. SILVERBEES) due to fund restructuring — this is official AMFI data
- Gemini 15 req/min free tier → magic mode uses 1 call per request only
- Windows reserved name `nul` — never create files named `nul`
- Port 8000 may have stale process → use `wmic process where "name='python.exe'" delete`

---

developed by            Nitin Nandrajog
