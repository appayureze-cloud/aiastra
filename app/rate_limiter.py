"""
Simple Rate Limiter for API endpoints
Fixed Bug #14: Added rate limiting to prevent abuse
"""

import logging
import time
from collections import defaultdict
from typing import Dict, Tuple
from threading import Lock
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """
    Simple in-memory rate limiter using sliding window
    """
    
    def __init__(self):
        # Store: client_id -> (request_times, lock)
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
    
    def is_allowed(
        self,
        client_id: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed
        
        Args:
            client_id: Unique identifier for client (IP or user ID)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            (allowed, remaining_requests)
        """
        with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            
            # Get requests for this client
            requests = self._requests[client_id]
            
            # Remove old requests outside window
            requests[:] = [req_time for req_time in requests if req_time > cutoff]
            
            # Check if under limit
            if len(requests) < max_requests:
                requests.append(now)
                return True, max_requests - len(requests)
            else:
                return False, 0
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Cleanup old client entries to prevent memory leak"""
        with self._lock:
            now = time.time()
            clients_to_remove = []
            
            for client_id, requests in self._requests.items():
                if not requests or (now - requests[-1]) > max_age_seconds:
                    clients_to_remove.append(client_id)
            
            for client_id in clients_to_remove:
                del self._requests[client_id]
            
            if clients_to_remove:
                logger.info(f"🧹 Cleaned up {len(clients_to_remove)} old rate limit entries")


# Global rate limiter instance
rate_limiter = SimpleRateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Usage:
        @router.post("/endpoint")
        @rate_limit(max_requests=10, window_seconds=60)
        async def my_endpoint(request: Request):
            ...
    
    Args:
        max_requests: Maximum requests allowed per window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        async def wrapper(*args, request: Request = None, **kwargs):
            # Get client identifier (IP address)
            client_ip = request.client.host if request and request.client else "unknown"
            
            # Check rate limit
            allowed, remaining = rate_limiter.is_allowed(
                client_id=client_ip,
                max_requests=max_requests,
                window_seconds=window_seconds
            )
            
            if not allowed:
                logger.warning(f"⚠️ Rate limit exceeded for {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Max {max_requests} requests per {window_seconds} seconds.",
                        "retry_after": window_seconds
                    }
                )
            
            # Add rate limit info to response headers (if possible)
            response = await func(*args, request=request, **kwargs)
            
            # Try to add headers if response supports it
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Window"] = str(window_seconds)
            
            return response
        
        return wrapper
    return decorator


def get_client_id(request: Request) -> str:
    """
    Get client identifier from request
    
    Checks in order:
    1. X-Forwarded-For header (behind proxy)
    2. X-Real-IP header
    3. Client IP address
    """
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    
    return request.client.host if request.client else "unknown"
