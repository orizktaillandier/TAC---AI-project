"""
Dependencies for FastAPI endpoints.
"""
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.classifier import ClassifierService
from app.services.zoho import ZohoService
from app.services.cache import CacheService
from app.core.config import settings


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_zoho_service(db: Session = Depends(get_db)) -> ZohoService:
    """
    Get Zoho service.
    
    Args:
        db: Database session
        
    Returns:
        ZohoService instance
    """
    return ZohoService(db)


def get_cache_service() -> CacheService:
    """
    Get cache service.
    
    Returns:
        CacheService instance
    """
    if settings.USE_REDIS:
        return CacheService(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ttl=settings.CACHE_TTL
        )
    return None


def get_classifier_service(
    db: Session = Depends(get_db),
    zoho_service: ZohoService = Depends(get_zoho_service),
    cache_service: CacheService = Depends(get_cache_service)
) -> ClassifierService:
    """
    Get classifier service.
    
    Args:
        db: Database session
        zoho_service: Zoho service
        cache_service: Cache service
        
    Returns:
        ClassifierService instance
    """
    return ClassifierService(db, zoho_service, cache_service)