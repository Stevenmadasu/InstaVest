"""
InstaVest — FastAPI Application Entry Point
AI-native investment research terminal.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, companies, watchlists, portfolios, thesis, signals, reports, dashboard
from app.api.routes import temporal

app = FastAPI(
    title="InstaVest API",
    description="Institutional-grade AI investment research terminal",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(companies.router, prefix="/companies", tags=["Companies"])
app.include_router(watchlists.router, prefix="/watchlists", tags=["Watchlists"])
app.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
app.include_router(thesis.router, prefix="/thesis-boards", tags=["Thesis"])
app.include_router(signals.router, prefix="/signals", tags=["Signals"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(temporal.router, tags=["Temporal Intelligence"])
