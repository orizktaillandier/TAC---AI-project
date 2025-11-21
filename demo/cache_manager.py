"""
Caching Manager for API Calls and KB Searches
Reduces API costs and improves response times
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for API calls and search results"""
    
    def __init__(self, cache_file: str = "api_cache.json", default_ttl_hours: int = 24):
        """
        Initialize cache manager
        
        Args:
            cache_file: Path to cache file
            default_ttl_hours: Default time-to-live for cache entries (hours)
        """
        self.cache_file = Path(__file__).parent / "mock_data" / cache_file
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.load()
    
    def _generate_key(self, data: str) -> str:
        """Generate cache key from input data"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def load(self):
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.debug(f"Loaded {len(self.cache)} cache entries")
            else:
                self.cache = {}
                self.save()
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache = {}
    
    def save(self):
        """Save cache to file"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def get(self, key: str, ttl: Optional[timedelta] = None) -> Optional[Any]:
        """
        Get value from cache if not expired
        
        Args:
            key: Cache key
            ttl: Optional custom TTL (overrides default)
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        cached_time = datetime.fromisoformat(entry['timestamp'])
        ttl_to_use = ttl or self.default_ttl
        
        if datetime.now() - cached_time > ttl_to_use:
            # Expired, remove it
            del self.cache[key]
            self.save()
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL (overrides default)
        """
        self.cache[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'ttl_hours': (ttl or self.default_ttl).total_seconds() / 3600
        }
        self.save()
    
    def cache_api_call(self, prompt: str, api_function, *args, **kwargs) -> Any:
        """
        Cache wrapper for API calls
        
        Args:
            prompt: The input prompt/text (used for cache key)
            api_function: The API function to call
            *args, **kwargs: Arguments to pass to API function
        
        Returns:
            Cached result if available, otherwise calls API and caches result
        """
        # Generate cache key from prompt
        cache_key = self._generate_key(prompt)
        
        # Try to get from cache
        cached_result = self.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache HIT for key: {cache_key[:16]}...")
            return cached_result
        
        # Cache miss - call API
        logger.debug(f"Cache MISS for key: {cache_key[:16]}...")
        try:
            result = api_function(*args, **kwargs)
            # Cache the result
            self.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
    
    def clear_expired(self):
        """Remove all expired entries from cache"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            cached_time = datetime.fromisoformat(entry['timestamp'])
            ttl = timedelta(hours=entry.get('ttl_hours', self.default_ttl.total_seconds() / 3600))
            
            if now - cached_time > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.save()
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def clear_all(self):
        """Clear all cache entries"""
        self.cache = {}
        self.save()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.clear_expired()  # Clean up first
        
        total_entries = len(self.cache)
        total_size = len(json.dumps(self.cache))
        
        # Calculate age distribution
        now = datetime.now()
        age_distribution = {
            'less_than_1h': 0,
            '1h_to_6h': 0,
            '6h_to_24h': 0,
            'more_than_24h': 0
        }
        
        for entry in self.cache.values():
            cached_time = datetime.fromisoformat(entry['timestamp'])
            age = now - cached_time
            
            if age < timedelta(hours=1):
                age_distribution['less_than_1h'] += 1
            elif age < timedelta(hours=6):
                age_distribution['1h_to_6h'] += 1
            elif age < timedelta(hours=24):
                age_distribution['6h_to_24h'] += 1
            else:
                age_distribution['more_than_24h'] += 1
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_kb': round(total_size / 1024, 2),
            'age_distribution': age_distribution
        }

