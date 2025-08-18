"""
API router configuration.
"""
from fastapi import APIRouter

from app.api.endpoints import classification, zoho, monitoring

# API router
api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(classification.router, prefix="/classification", tags=["classification"])
api_router.include_router(zoho.router, prefix="/zoho", tags=["zoho"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])