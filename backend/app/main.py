"""
Daily Investment Advisor — India
FastAPI backend entry point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routers import recommend, assets

app = FastAPI(
    title="Daily Investment Advisor — India",
    description="AI-powered investment recommendations across Indian asset classes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(recommend.router, prefix="/api", tags=["Recommendations"])
app.include_router(assets.router,    prefix="/api", tags=["Assets"])

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "Daily Investment Advisor — India",
        "version": "1.0.0",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }

@app.get("/health", tags=["Health"])
async def health():
    from app.cache.cache_manager import stats
    return {"status": "healthy", "cache": stats()}

# ── __init__ stubs ────────────────────────────────────────────────────────────
# (ensure packages are importable)
