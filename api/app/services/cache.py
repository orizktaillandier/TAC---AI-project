"""
Redis cache service for performance optimization.
"""
import json
import logging
from typing import Any, Dict, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 3600
    ):
        """
        Initialize the cache service.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database
            password: Redis password
            ttl: Default TTL in seconds
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False
        )
        self.ttl = ttl
        self.enabled = True
    
    async def is_connected(self) -> bool:
        """
        Check if connected to Redis.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            return False
    
    async def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (overrides default)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            return await self.client.set(key, serialized, ex=ttl or self.ttl)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            return await self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    async def flush(self) -> bool:
        """
        Flush the entire cache.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            return await self.client.flushdb()
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")
            return False
    
    async def get_keys(self, pattern: str = "*") -> list:
        """
        Get keys matching a pattern.
        
        Args:
            pattern: Key pattern
            
        Returns:
            List of matching keys
        """
        if not self.enabled:
            return []
        
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Cache keys error for pattern {pattern}: {str(e)}")
            return []
    
    def disable(self) -> None:
        """Disable the cache."""
        self.enabled = False
    
    def enable(self) -> None:
        """Enable the cache."""
        self.enabled = True