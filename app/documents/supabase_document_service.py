"""
Supabase Document Service
Uses Supabase REST API instead of direct PostgreSQL connection
"""

import os
import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SupabaseDocumentService:
    """Service for managing documents using Supabase REST API"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"{self.supabase_url}/rest/v1"
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
    
    async def create_document(self, document_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new document record"""
        if not self.enabled:
            logger.error("Supabase not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/documents",
                    headers=self.headers,
                    json=document_data,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return result[0] if isinstance(result, list) else result
                else:
                    logger.error(f"Failed to create document: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return None
    
    async def get_documents_by_patient(
        self,
        patient_id: str,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents for a patient"""
        if not self.enabled:
            logger.error("Supabase not configured")
            return []
        
        try:
            # Build query
            query = f"patient_id=eq.{patient_id}&is_active=eq.true&is_deleted=eq.false"
            if doc_type:
                query += f"&doc_type=eq.{doc_type}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/documents?{query}&order=created_at.desc",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get documents: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        if not self.enabled:
            logger.error("Supabase not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/documents?document_id=eq.{document_id}&is_active=eq.true",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    return results[0] if results else None
                else:
                    logger.error(f"Failed to get document: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    async def update_document(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update document metadata"""
        if not self.enabled:
            logger.error("Supabase not configured")
            return False
        
        try:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/documents?document_id=eq.{document_id}",
                    headers=self.headers,
                    json=updates,
                    timeout=30.0
                )
                
                return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def increment_download_count(self, document_id: str) -> bool:
        """Increment download count and update last accessed"""
        if not self.enabled:
            return False
        
        try:
            # Get current document
            doc = await self.get_document_by_id(document_id)
            if not doc:
                return False
            
            # Update counts
            updates = {
                'download_count': (doc.get('download_count', 0) or 0) + 1,
                'last_accessed': datetime.now(timezone.utc).isoformat()
            }
            
            return await self.update_document(document_id, updates)
        except Exception as e:
            logger.error(f"Error incrementing download count: {e}")
            return False
    
    async def mark_as_shared(
        self,
        document_id: str,
        shared_via: str = 'link'
    ) -> bool:
        """Mark document as shared"""
        if not self.enabled:
            return False
        
        try:
            doc = await self.get_document_by_id(document_id)
            if not doc:
                return False
            
            updates = {
                'is_shared': True,
                'shared_via': shared_via,
                'share_count': (doc.get('share_count', 0) or 0) + 1
            }
            
            return await self.update_document(document_id, updates)
        except Exception as e:
            logger.error(f"Error marking as shared: {e}")
            return False
    
    async def soft_delete_document(self, document_id: str) -> bool:
        """Soft delete a document"""
        if not self.enabled:
            return False
        
        updates = {
            'is_deleted': True,
            'is_active': False,
            'deleted_at': datetime.now(timezone.utc).isoformat()
        }
        
        return await self.update_document(document_id, updates)
    
    async def hard_delete_document(self, document_id: str) -> bool:
        """Permanently delete a document record"""
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/documents?document_id=eq.{document_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def check_table_exists(self) -> bool:
        """Check if documents table exists"""
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/documents?limit=1",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking table: {e}")
            return False


# Global instance
supabase_document_service = SupabaseDocumentService()
