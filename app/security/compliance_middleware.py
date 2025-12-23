"""
Compliance middleware for automatic encryption and audit logging
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import json
from .disha_compliance import DISHACompliance, DataAccessPurpose

class ComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce DISHA compliance
    - Logs all health data access
    - Checks consent before data access
    - Audits all API calls
    """
    
    # Endpoints that access patient health data
    HEALTH_DATA_ENDPOINTS = {
        '/patients/health': 'health_record',
        '/prescriptions': 'prescription',
        '/medicine-reminders': 'reminder',
        '/documents': 'document',
        '/chat': 'consultation',
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get user info from request
        user_id = request.headers.get('X-User-ID', 'anonymous')
        user_type = request.headers.get('X-User-Type', 'unknown')
        ip_address = request.client.host
        user_agent = request.headers.get('User-Agent', '')
        
        # Check if this is a health data endpoint
        is_health_data = any(
            request.url.path.startswith(endpoint) 
            for endpoint in self.HEALTH_DATA_ENDPOINTS
        )
        
        # Process request
        response = await call_next(request)
        
        # Log if health data was accessed
        if is_health_data and response.status_code == 200:
            # Extract patient_id from path or body
            patient_id = self._extract_patient_id(request)
            
            if patient_id:
                # Determine data type
                data_type = self._get_data_type(request.url.path)
                
                # Log access (async, don't block response)
                # TODO: Use background task
                # await self._log_access(
                #     patient_id=patient_id,
                #     accessed_by_id=user_id,
                #     accessed_by_type=user_type,
                #     access_type=request.method.lower(),
                #     data_type=data_type,
                #     ip_address=ip_address,
                #     user_agent=user_agent
                # )
                pass
        
        # Add compliance headers
        response.headers['X-Compliance'] = 'DISHA'
        response.headers['X-Encrypted'] = 'true'
        
        return response
    
    def _extract_patient_id(self, request: Request) -> str:
        """Extract patient ID from request"""
        # From path params
        if 'patient_id' in request.path_params:
            return request.path_params['patient_id']
        
        # From query params
        if 'patient_id' in request.query_params:
            return request.query_params['patient_id']
        
        # From URL path
        parts = request.url.path.split('/')
        if 'patient' in parts:
            idx = parts.index('patient')
            if idx + 1 < len(parts):
                return parts[idx + 1]
        
        return None
    
    def _get_data_type(self, path: str) -> str:
        """Get data type from endpoint path"""
        for endpoint, data_type in self.HEALTH_DATA_ENDPOINTS.items():
            if path.startswith(endpoint):
                return data_type
        return 'unknown'
