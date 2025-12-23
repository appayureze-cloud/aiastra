"""
Background Tasks for Railway Deployment
Handles scheduled tasks like medicine reminders and Shopify sync
"""
import asyncio
import schedule
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_medicine_reminders():
    """
    Send medicine reminders to all patients
    Runs at 8 AM and 8 PM daily
    """
    try:
        logger.info("🔔 Starting medicine reminder service...")
        
        # Import here to avoid circular imports
        from app.medicine_reminder_service import send_all_reminders
        
        # Send all reminders
        result = await send_all_reminders()
        
        logger.info(f"✅ Medicine reminders sent: {result.get('sent', 0)} patients")
        
    except Exception as e:
        logger.error(f"❌ Error sending medicine reminders: {e}", exc_info=True)

async def run_shopify_sync():
    """
    Sync Shopify products to database
    Runs every 6 hours
    """
    try:
        logger.info("🛒 Starting Shopify product sync...")
        
        # Import here to avoid circular imports
        from app.shopify_client import ShopifyClient
        
        # Initialize Shopify client
        shopify = ShopifyClient()
        
        # Sync all products
        products = await shopify.get_all_products()
        
        logger.info(f"✅ Shopify sync complete: {len(products)} products")
        
    except Exception as e:
        logger.error(f"❌ Error syncing Shopify: {e}", exc_info=True)

def schedule_tasks():
    """
    Schedule all background tasks
    """
    logger.info("📅 Scheduling background tasks...")
    
    # Medicine reminders - 8 AM and 8 PM
    schedule.every().day.at("08:00").do(
        lambda: asyncio.run(run_medicine_reminders())
    )
    schedule.every().day.at("20:00").do(
        lambda: asyncio.run(run_medicine_reminders())
    )
    logger.info("✅ Medicine reminders scheduled: 8:00 AM, 8:00 PM")
    
    # Shopify sync - Every 6 hours
    schedule.every(6).hours.do(
        lambda: asyncio.run(run_shopify_sync())
    )
    logger.info("✅ Shopify sync scheduled: Every 6 hours")
    
    # Run initial sync on startup
    logger.info("🚀 Running initial Shopify sync...")
    asyncio.run(run_shopify_sync())

def run_scheduler():
    """
    Main scheduler loop
    """
    logger.info("=" * 50)
    logger.info("🤖 Background Tasks Worker Started")
    logger.info("=" * 50)
    
    # Schedule all tasks
    schedule_tasks()
    
    # Main loop
    logger.info("⏰ Scheduler running... (Press Ctrl+C to stop)")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("👋 Shutting down background tasks worker...")
            break
            
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}", exc_info=True)
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    run_scheduler()
