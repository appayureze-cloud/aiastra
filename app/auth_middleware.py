"""
Authentication and Rate Limiting Middleware
For production-ready security on companion endpoints
"""

import logging
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Simple bearer token security
security = HTTPBearer(auto_error=False)


class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis or similar distributed solution
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Check rate
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Record new request
        self.requests[client_id].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Get current user from auth token (optional)
    
    For production:
    - Integrate with Firebase Auth
    - Validate JWT tokens
    - Extract user_id from token claims
    
    For development/testing:
    - Returns None (no auth required)
    - Can be enabled via env variable
    """
    # Check if auth is required
    auth_required = False  # Set to True in production
    
    if not auth_required:
        return None  # Auth not required
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Validate JWT token and extract user_id
    # For now, accept any token
    token = credentials.credentials
    
    # Example Firebase validation (implement in production):
    # try:
    #     decoded_token = verify_firebase_token(token)
    #     user_id = decoded_token['uid']
    #     return user_id
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid authentication token"
    #     )
    
    return "user_id_from_token"  # Placeholder


async def rate_limit_check(request: Request) -> None:
    """
    Rate limiting middleware
    
    Limits requests per IP address to prevent abuse
    """
    # Get client identifier (IP address)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )


async def validate_user_access(
    user_id_from_request: str,
    authenticated_user: Optional[str] = None
) -> None:
    """
    Validate that authenticated user can access the requested user's data
    
    For production:
    - Ensure user can only access their own data
    - Or has admin/doctor privileges
    """
    # If auth not required, skip validation
    if authenticated_user is None:
        return
    
    # Check if user is accessing their own data
    if user_id_from_request != authenticated_user:
        logger.warning(f"User {authenticated_user} attempted to access data for {user_id_from_request}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own data"
        )
