"""
Supabase connection helper for Astra
"""

import os
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                logger.warning("Supabase credentials not found in environment")
                return None
            
            _supabase_client = create_client(url, key)
            logger.info("✅ Supabase client initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            return None
    
    return _supabase_client
