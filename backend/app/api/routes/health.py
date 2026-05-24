"""Health check route."""
from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "InstaVest API",
        "version": "0.1.0",
        "environment": settings.app_env,
        "ai_available": settings.has_ai,
        "fmp_available": settings.has_fmp,
    }
