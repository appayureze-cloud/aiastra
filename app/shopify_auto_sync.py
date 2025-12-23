"""
Shopify Product Auto-Sync Service
Automatically syncs product catalog from Shopify at regular intervals
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import os

logger = logging.getLogger(__name__)

class ShopifyAutoSync:
    """Automatic product sync service for Shopify"""
    
    def __init__(self, sync_interval_hours: int = 6):
        """
        Initialize auto-sync service
        
        Args:
            sync_interval_hours: Hours between automatic syncs (default: 6 hours)
        """
        self.sync_interval_hours = sync_interval_hours
        self.last_sync_time: Optional[datetime] = None
        self.sync_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Get sync interval from environment (default 6 hours)
        env_interval = os.getenv("SHOPIFY_SYNC_INTERVAL_HOURS")
        if env_interval:
            try:
                self.sync_interval_hours = int(env_interval)
            except ValueError:
                logger.warning(f"Invalid SHOPIFY_SYNC_INTERVAL_HOURS: {env_interval}, using default: 6")
    
    async def sync_products(self) -> dict:
        """
        Perform product sync from Shopify
        
        Returns:
            dict: Sync result with status and product count
        """
        try:
            from app.shopify_client import ShopifyClient
            from app.enhanced_product_mapper import enhanced_product_mapper
            
            logger.info("🔄 Starting Shopify product sync...")
            
            # Reinitialize ShopifyClient to refresh variant mapping
            shopify_client = ShopifyClient()
            
            # Check if ShopifyClient is in mock mode
            if hasattr(shopify_client, 'mock_mode') and shopify_client.mock_mode:
                logger.warning("⚠️ ShopifyClient is in mock mode, sync will use cached data only")
            
            # Clear and reload dynamic cache in enhanced mapper
            enhanced_product_mapper._cache_loaded = False
            enhanced_product_mapper._dynamic_cache = {}
            enhanced_product_mapper.load_dynamic_cache()
            
            product_count = len(enhanced_product_mapper._dynamic_cache)
            variant_count = len(shopify_client.sku_to_variant_map) if hasattr(shopify_client, 'sku_to_variant_map') else 0
            
            self.last_sync_time = datetime.now()
            
            logger.info(f"✅ Shopify sync completed: {product_count} products, {variant_count} variants loaded")
            
            return {
                "success": True,
                "product_count": product_count,
                "variant_count": variant_count,
                "sync_time": self.last_sync_time.isoformat(),
                "next_sync": (self.last_sync_time + timedelta(hours=self.sync_interval_hours)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Shopify sync failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "sync_time": datetime.now().isoformat()
            }
    
    async def auto_sync_loop(self):
        """Background task for automatic product syncing"""
        logger.info(f"🚀 Starting Shopify auto-sync (interval: {self.sync_interval_hours} hours)")
        
        # Initial sync on startup
        await self.sync_products()
        
        while self.is_running:
            try:
                # Wait for sync interval
                await asyncio.sleep(self.sync_interval_hours * 3600)
                
                # Perform sync
                result = await self.sync_products()
                
                if result["success"]:
                    logger.info(f"✅ Auto-sync successful: {result['product_count']} products")
                else:
                    logger.error(f"❌ Auto-sync failed: {result.get('error')}")
                    
            except asyncio.CancelledError:
                logger.info("Auto-sync loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-sync loop: {e}")
                # Continue loop even if sync fails
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def start(self):
        """Start the auto-sync background task"""
        if self.is_running:
            logger.warning("Auto-sync already running")
            return
        
        self.is_running = True
        self.sync_task = asyncio.create_task(self.auto_sync_loop())
        logger.info("✅ Shopify auto-sync service started")
    
    async def stop(self):
        """Stop the auto-sync background task"""
        self.is_running = False
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto-sync service stopped")
    
    def get_status(self) -> dict:
        """Get current sync status"""
        return {
            "is_running": self.is_running,
            "sync_interval_hours": self.sync_interval_hours,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "next_sync_time": (
                (self.last_sync_time + timedelta(hours=self.sync_interval_hours)).isoformat()
                if self.last_sync_time else None
            )
        }

# Global auto-sync instance
shopify_auto_sync = ShopifyAutoSync()
