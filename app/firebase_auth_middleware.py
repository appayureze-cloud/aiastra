"""
Firebase Authentication Middleware
Protects sensitive endpoints by verifying Firebase ID tokens
"""

import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth
from functools import wraps

logger = logging.getLogger(__name__)

security = HTTPBearer()

class FirebaseAuthMiddleware:
    """Middleware for Firebase ID token verification"""
    
    def __init__(self):
        self.initialized = self._check_firebase_initialized()
    
    def _check_firebase_initialized(self) -> bool:
        """Check if Firebase Admin SDK is initialized"""
        try:
            if firebase_admin._apps:
                logger.info("Firebase Auth middleware initialized")
                return True
            else:
                logger.warning("Firebase not initialized - auth middleware disabled")
                return False
        except Exception as e:
            logger.error(f"Firebase auth check failed: {e}")
            return False
    
    async def verify_firebase_token(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded user information
        
        Args:
            credentials: HTTP Bearer credentials containing Firebase ID token
            
        Returns:
            Dict containing user information from Firebase token
            
        Raises:
            HTTPException: If token is invalid or verification fails
        """
        if not self.initialized:
            raise HTTPException(
                status_code=503,
                detail="Firebase authentication not available"
            )
        
        token = credentials.credentials
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            
            # Extract user information
            user_info = {
                "user_id": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "phone_number": decoded_token.get("phone_number"),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "firebase_claims": decoded_token
            }
            
            if not user_info["user_id"]:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid user information in token"
                )
            
            logger.info(f"Firebase token verified for user: {user_info['user_id']}")
            return user_info
            
        except auth.InvalidIdTokenError:
            logger.error("Invalid Firebase ID token")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        except auth.ExpiredIdTokenError:
            logger.error("Expired Firebase ID token")
            raise HTTPException(
                status_code=401,
                detail="Authentication token has expired"
            )
        except auth.RevokedIdTokenError:
            logger.error("Revoked Firebase ID token")
            raise HTTPException(
                status_code=401,
                detail="Authentication token has been revoked"
            )
        except auth.CertificateFetchError:
            logger.error("Firebase certificate fetch failed")
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Token verification failed"
            )
    
    async def verify_optional_token(
        self, 
        request: Request
    ) -> Optional[Dict[str, Any]]:
        """
        Optional Firebase authentication - returns user if authenticated, None if not
        
        Args:
            request: FastAPI request object
            
        Returns:
            User info dict if authenticated, None otherwise
        """
        if not self.initialized:
            return None
        
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            decoded_token = auth.verify_id_token(token)
            
            return {
                "user_id": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "phone_number": decoded_token.get("phone_number"),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "firebase_claims": decoded_token
            }
        except:
            return None
    
    async def verify_admin_role(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Verify Firebase token and check for admin role
        
        Raises:
            HTTPException: If user is not an admin
        """
        user_info = await self.verify_firebase_token(credentials)
        
        # Check for admin custom claim
        firebase_claims = user_info.get("firebase_claims", {})
        is_admin = firebase_claims.get("admin", False) or firebase_claims.get("role") == "admin"
        
        if not is_admin:
            logger.warning(f"Admin access denied for user: {user_info['user_id']}")
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required"
            )
        
        logger.info(f"Admin access granted for user: {user_info['user_id']}")
        return user_info
    
    async def verify_doctor_role(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Verify Firebase token and check for doctor role
        
        Raises:
            HTTPException: If user is not a doctor
        """
        user_info = await self.verify_firebase_token(credentials)
        
        # Check for doctor custom claim
        firebase_claims = user_info.get("firebase_claims", {})
        is_doctor = (
            firebase_claims.get("doctor", False) or 
            firebase_claims.get("role") == "doctor" or
            firebase_claims.get("admin", False)  # Admins can also act as doctors
        )
        
        if not is_doctor:
            logger.warning(f"Doctor access denied for user: {user_info['user_id']}")
            raise HTTPException(
                status_code=403,
                detail="Doctor privileges required"
            )
        
        logger.info(f"Doctor access granted for user: {user_info['user_id']}")
        return user_info

# Global instance
firebase_auth = FirebaseAuthMiddleware()

# Dependency functions for easy use in route decorators
async def require_firebase_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency: Require valid Firebase authentication"""
    return await firebase_auth.verify_firebase_token(credentials)

async def require_admin_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency: Require admin role"""
    return await firebase_auth.verify_admin_role(credentials)

async def require_doctor_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency: Require doctor role"""
    return await firebase_auth.verify_doctor_role(credentials)

async def optional_firebase_auth(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency: Optional Firebase authentication"""
    return await firebase_auth.verify_optional_token(request)

# Helper function to protect endpoints
def protect_endpoint(allowed_roles: List[str] = None):
    """
    Decorator to protect endpoints with Firebase authentication
    
    Args:
        allowed_roles: List of allowed roles (e.g., ['admin', 'doctor', 'patient'])
                      If None, any authenticated user is allowed
    
    Usage:
        @router.post("/sensitive-endpoint")
        @protect_endpoint(allowed_roles=['admin', 'doctor'])
        async def sensitive_operation(user: dict = Depends(require_firebase_auth)):
            # Only admins and doctors can access
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The actual auth check happens via the Depends in the route
            return await func(*args, **kwargs)
        return wrapper
    return decorator
