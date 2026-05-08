"""
Redis Caching Layer
Provides caching functionality with TTL support
"""

import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as redis
from app.core.config_simple import settings


def get_cache_key(prefix: str, **kwargs) -> str:
    """
    Generate a cache key from prefix and parameters.
    
    Args:
        prefix: Base key prefix (e.g., "patients", "appointments")
        **kwargs: Additional parameters to include in key
        
    Returns:
        Formatted cache key string
    """
    if not kwargs:
        return prefix
    
    # Sort keys for consistent hashing
    params = sorted(kwargs.items())
    params_str = "-".join(f"{k}={v}" for k, v in params)
    return f"{prefix}:{params_str}"


class RedisCache:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = bool(settings.REDIS_URL)
    
    async def connect(self):
        """Connect to Redis"""
        if not self.enabled:
            return
        
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            print("Redis cache connected successfully")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.enabled = False
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "patient:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Generated cache key
        """
        # Create a deterministic string from args and kwargs
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        key_string = ":".join(key_parts)
        
        # Hash if too long (using SHA-256 for better hash quality)
        if len(key_string) > 200:
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]
            return f"{prefix}:{key_hash}"
        
        return key_string


# Global cache instance
cache = RedisCache()


def cached(
    ttl: int = 300,
    key_prefix: str = "cache",
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        key_builder: Optional custom key builder function
    
    Example:
        @cached(ttl=600, key_prefix="patient")
        async def get_patient(patient_id: UUID):
            # Expensive operation
            return patient
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache.generate_key(key_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


async def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching pattern
    
    Args:
        pattern: Key pattern to invalidate
    
    Example:
        await invalidate_cache("patient:*")
    """
    await cache.delete_pattern(pattern)
