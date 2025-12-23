"""
Admin Panel API Routes
Handles system configuration, logs, and dashboard stats
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from datetime import datetime

from app.config import settings
from app.database_models import get_db_dependency
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])

# --- Models ---

class SystemStats(BaseModel):
    status: str
    timestamp: str
    database_connected: bool
    model_loaded: bool
    active_sessions: int
    total_users: int
    total_doctors: int
    total_centers: int

class ConfigUpdate(BaseModel):
    settings: Dict[str, Any]

# --- Dependencies ---

def get_admin_user():
    # TODO: Implement proper admin authentication
    # For now, we'll assume a simple header or similar, or just open for dev
    # In production, this MUST be secured
    return {"role": "admin"}

# --- Routes ---

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(db: Session = Depends(get_db_dependency)):
    """Get aggregated system statistics"""
    try:
        # Database check
        try:
            db.execute(text("SELECT 1"))
            db_connected = True
        except:
            db_connected = False
            
        # Model status (from global state - risky but current implementation)
        from main_enhanced import model_inference
        model_loaded = model_inference.is_loaded() if model_inference else False
        
        # Counts
        # Note: These are raw SQL for speed/simplicity in this example, 
        # but should use ORM models in production
        try:
            users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            doctors_count = db.execute(text("SELECT COUNT(*) FROM doctors")).scalar() or 0
            centers_count = db.execute(text("SELECT COUNT(*) FROM treatment_centers")).scalar() or 0
            sessions_count = db.execute(text("SELECT COUNT(*) FROM chat_sessions WHERE updated_at > NOW() - INTERVAL '1 day'")).scalar() or 0
        except:
            users_count = 0
            doctors_count = 0
            centers_count = 0
            sessions_count = 0

        return SystemStats(
            status="operational" if db_connected else "degraded",
            timestamp=datetime.now().isoformat(),
            database_connected=db_connected,
            model_loaded=model_loaded,
            active_sessions=sessions_count,
            total_users=users_count,
            total_doctors=doctors_count,
            total_centers=centers_count
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_config(user: dict = Depends(get_admin_user)):
    """Get current system configuration (safe subset)"""
    return {
        "BASE_MODEL": settings.BASE_MODEL,
        "LORA_MODEL": settings.LORA_MODEL,
        "DEVICE": settings.DEVICE,
        "API_HOST": settings.API_HOST,
        "API_PORT": settings.API_PORT,
        "DEFAULT_TEMPERATURE": settings.DEFAULT_TEMPERATURE,
        # Don't expose secrets like keys!
    }

@router.get("/logs")
async def get_logs(lines: int = 100, user: dict = Depends(get_admin_user)):
    """Get recent application logs"""
    # This is a placeholder. In a real app, you'd read from a log file or aggregator.
    # For now, we'll return a mock or try to read a local log file if it exists.
    log_file = "app.log" 
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                return {"logs": f.readlines()[-lines:]}
        except:
            return {"logs": ["Could not read log file"]}
    return {"logs": ["Log file not found"]}
