"""
Shopify Webhook Handler
Receives real-time product updates from Shopify webhooks
"""

import logging
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/shopify", tags=["Shopify Webhooks"])

def verify_shopify_webhook(data: bytes, hmac_header: str, secret: str) -> bool:
    """
    Verify Shopify webhook signature
    
    Args:
        data: Raw request body
        hmac_header: X-Shopify-Hmac-SHA256 header value
        secret: Shopify webhook secret
    
    Returns:
        bool: True if signature is valid
    """
    try:
        computed_hmac = hmac.new(
            secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_hmac, hmac_header)
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        return False

@router.post("/products/create")
async def product_created(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_topic: Optional[str] = Header(None)
):
    """Handle product creation webhook from Shopify"""
    
    # Get webhook secret from environment
    webhook_secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")
    
    if webhook_secret and x_shopify_hmac_sha256:
        # Verify webhook signature
        body = await request.body()
        if not verify_shopify_webhook(body, x_shopify_hmac_sha256, webhook_secret):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse webhook data
    data = await request.json()
    
    logger.info(f"📦 New product created: {data.get('title', 'Unknown')}")
    
    # Trigger product sync
    try:
        from app.shopify_auto_sync import shopify_auto_sync
        await shopify_auto_sync.sync_products()
        
        return {
            "success": True,
            "message": "Product sync triggered",
            "product_title": data.get("title")
        }
    except Exception as e:
        logger.error(f"Error syncing after product creation: {e}")
        return {"success": False, "error": str(e)}

@router.post("/products/update")
async def product_updated(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_topic: Optional[str] = Header(None)
):
    """Handle product update webhook from Shopify"""
    
    webhook_secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")
    
    if webhook_secret and x_shopify_hmac_sha256:
        body = await request.body()
        if not verify_shopify_webhook(body, x_shopify_hmac_sha256, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    
    logger.info(f"🔄 Product updated: {data.get('title', 'Unknown')}")
    
    # Trigger product sync
    try:
        from app.shopify_auto_sync import shopify_auto_sync
        await shopify_auto_sync.sync_products()
        
        return {
            "success": True,
            "message": "Product sync triggered",
            "product_title": data.get("title")
        }
    except Exception as e:
        logger.error(f"Error syncing after product update: {e}")
        return {"success": False, "error": str(e)}

@router.post("/products/delete")
async def product_deleted(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_topic: Optional[str] = Header(None)
):
    """Handle product deletion webhook from Shopify"""
    
    webhook_secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")
    
    if webhook_secret and x_shopify_hmac_sha256:
        body = await request.body()
        if not verify_shopify_webhook(body, x_shopify_hmac_sha256, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    
    logger.info(f"🗑️ Product deleted: {data.get('title', 'Unknown')}")
    
    # Trigger product sync
    try:
        from app.shopify_auto_sync import shopify_auto_sync
        await shopify_auto_sync.sync_products()
        
        return {
            "success": True,
            "message": "Product sync triggered after deletion",
            "product_title": data.get("title")
        }
    except Exception as e:
        logger.error(f"Error syncing after product deletion: {e}")
        return {"success": False, "error": str(e)}

@router.get("/sync/manual")
async def manual_sync():
    """Manually trigger product sync"""
    try:
        from app.shopify_auto_sync import shopify_auto_sync
        result = await shopify_auto_sync.sync_products()
        
        return result
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def sync_status():
    """Get current sync status"""
    try:
        from app.shopify_auto_sync import shopify_auto_sync
        return shopify_auto_sync.get_status()
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
