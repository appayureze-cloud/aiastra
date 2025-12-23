"""
Environment Variable Validator for Production Deployments
Ensures all required environment variables are present before startup
"""

import os
import sys
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validates environment variables for production readiness"""
    
    # Required variables for production (will cause startup failure if missing)
    REQUIRED_PRODUCTION = {
        "DATABASE_URL": "PostgreSQL connection string for patient data",
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_ANON_KEY": "Supabase anonymous/public key",
        "SHOPIFY_SHOP_URL": "Shopify store URL (e.g., store.myshopify.com)",
        "SHOPIFY_ACCESS_TOKEN": "Shopify Admin API access token",
    }
    
    # Optional but recommended variables
    RECOMMENDED = {
        "FIREBASE_SERVICE_ACCOUNT": "Firebase service account JSON for push notifications",
        "STORJ_ACCESS_KEY": "Storj access key for document storage",
        "STORJ_SECRET_KEY": "Storj secret key for document storage",
        "AUTH0_DOMAIN": "Auth0 domain for authentication",
        "AUTH0_CLIENT_ID": "Auth0 client ID",
        "REDIS_URL": "Redis URL for rate limiting and caching",
    }
    
    # Security-related variables
    SECURITY = {
        "DATA_ENCRYPTION_KEY": "32-byte encryption key for sensitive data",
        "CORS_ORIGINS": "Comma-separated list of allowed CORS origins",
    }
    
    @staticmethod
    def validate_production() -> Tuple[bool, List[str], List[str]]:
        """
        Validate environment variables for production deployment
        
        Returns:
            Tuple of (is_valid, missing_required, missing_recommended)
        """
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        missing_required = []
        missing_recommended = []
        
        # Check required variables
        for var_name, description in EnvironmentValidator.REQUIRED_PRODUCTION.items():
            value = os.getenv(var_name)
            if not value or value.strip() == "":
                missing_required.append(f"{var_name} ({description})")
                logger.error(f"❌ MISSING REQUIRED: {var_name}")
            else:
                logger.info(f"✅ {var_name}: configured")
        
        # Check recommended variables
        for var_name, description in EnvironmentValidator.RECOMMENDED.items():
            value = os.getenv(var_name)
            if not value or value.strip() == "":
                missing_recommended.append(f"{var_name} ({description})")
                logger.warning(f"⚠️  MISSING RECOMMENDED: {var_name}")
            else:
                logger.info(f"✅ {var_name}: configured")
        
        # Check security variables
        for var_name, description in EnvironmentValidator.SECURITY.items():
            value = os.getenv(var_name)
            if not value or value.strip() == "":
                logger.warning(f"⚠️  MISSING SECURITY: {var_name} ({description})")
            else:
                logger.info(f"✅ {var_name}: configured")
        
        is_valid = len(missing_required) == 0
        
        return is_valid, missing_required, missing_recommended
    
    @staticmethod
    def validate_or_exit():
        """
        Validate environment and exit if critical variables are missing in production
        """
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        logger.info(f"🔍 Environment: {environment}")
        logger.info("🔍 Validating environment variables...")
        
        is_valid, missing_required, missing_recommended = EnvironmentValidator.validate_production()
        
        if missing_required:
            logger.error("\n" + "="*70)
            logger.error("❌ PRODUCTION VALIDATION FAILED")
            logger.error("="*70)
            logger.error(f"\nMissing {len(missing_required)} REQUIRED environment variables:")
            for var in missing_required:
                logger.error(f"  • {var}")
            
            if environment == "production":
                logger.error("\n🚫 Cannot start in PRODUCTION without required variables")
                logger.error("Please set these environment variables and restart")
                sys.exit(1)
            else:
                logger.warning("\n⚠️  Development mode: continuing despite missing variables")
                logger.warning("Some features may not work correctly")
        
        if missing_recommended:
            logger.warning("\n" + "="*70)
            logger.warning("⚠️  RECOMMENDED VARIABLES MISSING")
            logger.warning("="*70)
            logger.warning(f"\nMissing {len(missing_recommended)} recommended variables:")
            for var in missing_recommended:
                logger.warning(f"  • {var}")
            logger.warning("\nThese features may not be available:")
            logger.warning("Consider configuring these for full functionality")
        
        if is_valid:
            logger.info("\n✅ All required environment variables are configured")
            logger.info("✅ System ready for production deployment")
        
        return is_valid

def validate_production_env():
    """Convenience function for backward compatibility"""
    return EnvironmentValidator.validate_or_exit()
