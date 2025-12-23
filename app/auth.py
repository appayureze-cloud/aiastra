"""
Auth0 Authentication Module for Astra - Ayurvedic Wellness Assistant
Handles JWT token validation and user authentication via Auth0
"""

import os
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
import requests
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")

# Check if Auth0 is configured
AUTH0_ENABLED = all([AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET])
if not AUTH0_ENABLED:
    logger.warning("Auth0 configuration not found. Auth0 authentication will be disabled.")

ALGORITHMS = ["RS256"]
AUTH0_ISSUER = f"https://{AUTH0_DOMAIN}/" if AUTH0_DOMAIN else None
AUTH0_JWKS_URL = f"{AUTH0_ISSUER}.well-known/jwks.json" if AUTH0_ISSUER else None

security = HTTPBearer()

@lru_cache()
def get_jwks() -> Dict[str, Any]:
    """Get JSON Web Key Set from Auth0"""
    try:
        response = requests.get(AUTH0_JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch authentication keys")

def get_rsa_key(token: str) -> Dict[str, Any]:
    """Extract RSA key from JWT token header"""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token header")
    
    jwks = get_jwks()
    rsa_key = {}
    
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find appropriate key")
    
    return rsa_key

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    if not AUTH0_ENABLED:
        raise HTTPException(status_code=501, detail="Auth0 authentication is not configured")
    
    try:
        rsa_key = get_rsa_key(token)
        
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=AUTH0_ISSUER
        )
        
        return payload
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    # Extract user information from JWT payload
    user_info = {
        "user_id": payload.get("sub"),
        "email": payload.get("email", payload.get("https://astra.com/email")),
        "name": payload.get("name", payload.get("https://astra.com/name")),
        "picture": payload.get("picture", payload.get("https://astra.com/picture")),
        "email_verified": payload.get("email_verified", payload.get("https://astra.com/email_verified", False))
    }
    
    if not user_info["user_id"]:
        raise HTTPException(status_code=401, detail="Invalid user information")
    
    return user_info

async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """Optional authentication - returns user if authenticated, None if not"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email", payload.get("https://astra.com/email")),
            "name": payload.get("name", payload.get("https://astra.com/name")),
            "picture": payload.get("picture", payload.get("https://astra.com/picture")),
            "email_verified": payload.get("email_verified", payload.get("https://astra.com/email_verified", False))
        }
    except:
        return None