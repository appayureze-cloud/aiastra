import httpx
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LaravelClient:
    """
    Client for communicating with the Laravel Super Admin Backend
    Base URL: https://ayureze.org
    """
    
    def __init__(self):
        self.base_url = os.getenv("LARAVEL_BACKEND_URL", "https://ayureze.org/api")
        self.api_key = os.getenv("LARAVEL_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
                    json=data,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to POST to Laravel {endpoint}: {e}")
                return {"success": False, "error": str(e)}

    async def sync_prescription(self, prescription_data: Dict[str, Any]):
        """Send generated prescription to Laravel backend"""
        return await self._post("sync/prescription", prescription_data)

    async def sync_patient_vitals(self, patient_id: str, vitals: Dict[str, Any]):
        """Update patient vitals in Laravel backend"""
        return await self._post(f"patients/{patient_id}/vitals", vitals)

    async def notify_admin(self, title: str, message: str, level: str = "info"):
        """Send notification to Super Admin Dashboard"""
        return await self._post("notifications/admin", {
            "title": title,
            "message": message,
            "level": level
        })

# Global instance
laravel_client = LaravelClient()
