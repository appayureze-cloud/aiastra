"""
Redis-based Caching System
Replaces in-memory cache with production-ready Redis
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class RedisCache:
    """Production-grade Redis cache with fallback to in-memory"""
    
    def __init__(self):
        self.redis_client = None
        self.fallback_cache: Dict[str, Any] = {}
        self.redis_url = os.getenv("REDIS_URL")
        
        if self.redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Redis cache initialized")
            except ImportError:
                logger.warning("⚠️ redis-py not installed. Run: pip install redis")
                self.redis_client = None
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache.")
                self.redis_client = None
        else:
            logger.info("📦 No REDIS_URL found. Using in-memory cache.")
    
    def _get_key(self, namespace: str, key: str) -> str:
        """Generate namespaced key"""
        return f"ayureze:{namespace}:{key}"
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        cache_key = self._get_key(namespace, key)
        
        try:
            # Serialize value
            serialized_value = json.dumps(value)
            
            if self.redis_client:
                if ttl_seconds:
                    self.redis_client.setex(cache_key, ttl_seconds, serialized_value)
                else:
                    self.redis_client.set(cache_key, serialized_value)
                return True
            else:
                # Fallback to in-memory
                self.fallback_cache[cache_key] = {
                    "value": serialized_value,
                    "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds) if ttl_seconds else None
                }
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._get_key(namespace, key)
        
        try:
            if self.redis_client:
                value = self.redis_client.get(cache_key)
                if value:
                    return json.loads(value)
                return None
            else:
                # Fallback to in-memory
                cached = self.fallback_cache.get(cache_key)
                if not cached:
                    return None
                
                # Check expiration
                if cached.get("expires_at") and datetime.now(timezone.utc) > cached["expires_at"]:
                    del self.fallback_cache[cache_key]
                    return None
                
                return json.loads(cached["value"])
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache"""
        cache_key = self._get_key(namespace, key)
        
        try:
            if self.redis_client:
                self.redis_client.delete(cache_key)
            else:
                self.fallback_cache.pop(cache_key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._get_key(namespace, key)
        
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(cache_key))
            else:
                return cache_key in self.fallback_cache
        except Exception as e:
            logger.error(f"Cache exists check error: {e}")
            return False
    
    def get_many(self, namespace: str, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once"""
        results = {}
        
        for key in keys:
            value = self.get(namespace, key)
            if value is not None:
                results[key] = value
        
        return results
    
    def set_many(self, namespace: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        """Set multiple values at once"""
        success = True
        
        for key, value in data.items():
            if not self.set(namespace, key, value, ttl_seconds):
                success = False
        
        return success
    
    def increment(self, namespace: str, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        cache_key = self._get_key(namespace, key)
        
        try:
            if self.redis_client:
                return self.redis_client.incrby(cache_key, amount)
            else:
                # Fallback
                current = self.get(namespace, key) or 0
                new_value = current + amount
                self.set(namespace, key, new_value)
                return new_value
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    def clear_namespace(self, namespace: str) -> bool:
        """Clear all keys in a namespace"""
        try:
            if self.redis_client:
                pattern = self._get_key(namespace, "*")
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Clear from fallback cache
                prefix = f"ayureze:{namespace}:"
                keys_to_delete = [k for k in self.fallback_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.fallback_cache[key]
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

# Global instance
redis_cache = RedisCache()
