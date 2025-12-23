"""
Document Management API Routes
Handles upload, download, listing, and sharing of medical documents via Storj
Uses Supabase REST API instead of direct database connection
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
import uuid
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from app.documents.supabase_document_service import supabase_document_service
from app.storj_client import StorjClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Import custom WhatsApp client for document sharing
def get_whatsapp_client():
    """Get custom WhatsApp client for document sharing"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        return CustomWhatsAppClient()
    except Exception as e:
        logger.error(f"Failed to initialize custom WhatsApp client: {e}")
        return None

# Initialize Storj client
try:
    storj_client = StorjClient()
    logger.info("Storj client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Storj client: {e}")
    storj_client = None

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    patient_id: str = Form(..., description="Patient ID"),
    doc_type: str = Form(..., description="Document type (prescription, lab_report, xray, etc.)"),
    description: Optional[str] = Form(None, description="Document description"),
    uploaded_by: Optional[str] = Form(None, description="Uploader ID (doctor/admin)"),
    related_prescription_id: Optional[str] = Form(None)
):
    """Upload a medical document to Storj decentralized storage with Supabase metadata"""
    
    if not storj_client:
        raise HTTPException(status_code=500, detail="Storj storage not configured")
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Generate unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload to Storj
            metadata = {
                'document-id': document_id,
                'description': description or ''
            }
            
            storj_key = storj_client.upload_document(
                file_path=tmp_file_path,
                patient_id=patient_id,
                doc_type=doc_type,
                metadata=metadata
            )
            
            if not storj_key:
                raise HTTPException(status_code=500, detail="Failed to upload to Storj")
            
            # Create database record using Supabase REST API
            doc_data = {
                "document_id": document_id,
                "patient_id": patient_id,
                "doc_type": doc_type,
                "original_filename": file.filename,
                "storj_object_key": storj_key,
                "file_size": len(content),
                "content_type": file.content_type or 'application/octet-stream',
                "uploaded_by": uploaded_by,
                "description": description,
                "related_prescription_id": related_prescription_id,
                "is_active": True,
                "is_deleted": False,
                "download_count": 0,
                "share_count": 0,
                "is_shared": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            doc_record = await supabase_document_service.create_document(doc_data)
            
            if not doc_record:
                raise HTTPException(status_code=500, detail="Failed to save document metadata")
            
            logger.info(f"Document uploaded successfully: {document_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "storj_key": storj_key,
                "filename": file.filename,
                "size": len(content),
                "doc_type": doc_type,
                "patient_id": patient_id,
                "uploaded_at": doc_record.get('created_at')
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}")
async def list_patient_documents(
    patient_id: str,
    doc_type: Optional[str] = Query(None, description="Filter by document type")
):
    """List all documents for a specific patient"""
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        documents = await supabase_document_service.get_documents_by_patient(
            patient_id=patient_id,
            doc_type=doc_type
        )
        
        return {
            "success": True,
            "patient_id": patient_id,
            "count": len(documents),
            "documents": [
                {
                    "document_id": doc.get("document_id"),
                    "filename": doc.get("original_filename"),
                    "doc_type": doc.get("doc_type"),
                    "description": doc.get("description"),
                    "file_size": doc.get("file_size"),
                    "content_type": doc.get("content_type"),
                    "uploaded_by": doc.get("uploaded_by"),
                    "uploaded_at": doc.get("created_at"),
                    "download_count": doc.get("download_count", 0),
                    "is_shared": doc.get("is_shared", False),
                    "share_count": doc.get("share_count", 0),
                    "related_prescription_id": doc.get("related_prescription_id")
                }
                for doc in documents
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{document_id}")
async def download_document(document_id: str):
    """Download a document from Storj"""
    
    if not storj_client:
        raise HTTPException(status_code=500, detail="Storj storage not configured")
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Get document record
        doc_record = await supabase_document_service.get_document_by_id(document_id)
        
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Download from Storj to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(doc_record['original_filename']).suffix) as tmp_file:
            tmp_file_path = tmp_file.name
        
        success = storj_client.download_document(
            object_key=doc_record['storj_object_key'],
            download_path=tmp_file_path
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to download from Storj")
        
        # Update access tracking
        await supabase_document_service.increment_download_count(document_id)
        
        # Stream file to client
        def iterfile():
            try:
                with open(tmp_file_path, 'rb') as f:
                    yield from f
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
        
        return StreamingResponse(
            iterfile(),
            media_type=doc_record['content_type'] or 'application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{doc_record["original_filename"]}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/share-link/{document_id}")
async def generate_share_link(
    document_id: str,
    expiration_hours: int = Query(24, description="Link expiration in hours")
):
    """Generate a time-limited shareable download link"""
    
    if not storj_client:
        raise HTTPException(status_code=500, detail="Storj storage not configured")
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Get document record
        doc_record = await supabase_document_service.get_document_by_id(document_id)
        
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate pre-signed URL
        share_url = storj_client.generate_download_url(
            object_key=doc_record['storj_object_key'],
            expiration_hours=expiration_hours
        )
        
        if not share_url:
            raise HTTPException(status_code=500, detail="Failed to generate share link")
        
        # Update sharing tracking
        await supabase_document_service.mark_as_shared(document_id, shared_via='link')
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": doc_record['original_filename'],
            "share_url": share_url,
            "expires_in_hours": expiration_hours,
            "expires_at": (datetime.now(timezone.utc).timestamp() + (expiration_hours * 3600))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate share link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    permanent: bool = Query(False, description="Permanently delete from Storj (default: soft delete)")
):
    """Delete a document (soft delete by default)"""
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        doc_record = await supabase_document_service.get_document_by_id(document_id)
        
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if permanent and storj_client:
            # Permanently delete from Storj
            success = storj_client.delete_document(doc_record['storj_object_key'])
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete from Storj")
            
            # Remove from database
            success = await supabase_document_service.hard_delete_document(document_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete from database")
        else:
            # Soft delete
            success = await supabase_document_service.soft_delete_document(document_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete document")
        
        return {
            "success": True,
            "document_id": document_id,
            "delete_type": "permanent" if permanent else "soft",
            "message": "Document deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{document_id}")
async def get_document_metadata(document_id: str):
    """Get document metadata without downloading"""
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        doc_record = await supabase_document_service.get_document_by_id(document_id)
        
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Also get metadata from Storj
        storj_metadata = None
        if storj_client:
            storj_metadata = storj_client.get_document_metadata(doc_record['storj_object_key'])
        
        return {
            "success": True,
            "document_id": doc_record['document_id'],
            "patient_id": doc_record['patient_id'],
            "filename": doc_record['original_filename'],
            "doc_type": doc_record['doc_type'],
            "description": doc_record.get('description'),
            "file_size": doc_record['file_size'],
            "content_type": doc_record['content_type'],
            "uploaded_by": doc_record.get('uploaded_by'),
            "uploaded_at": doc_record['created_at'],
            "download_count": doc_record.get('download_count', 0),
            "last_accessed": doc_record.get('last_accessed'),
            "is_shared": doc_record.get('is_shared', False),
            "share_count": doc_record.get('share_count', 0),
            "related_prescription_id": doc_record.get('related_prescription_id'),
            "storj_metadata": storj_metadata,
            "additional_metadata": doc_record.get('doc_metadata')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/share-whatsapp/{document_id}")
async def share_document_via_whatsapp(
    document_id: str,
    phone_number: str = Query(..., description="WhatsApp number (e.g., 916380176373)"),
    message: Optional[str] = Query(None, description="Custom message to send with document"),
    expiration_hours: int = Query(24, description="Link expiration in hours")
):
    """Share document via WhatsApp with time-limited download link"""
    
    if not storj_client:
        raise HTTPException(status_code=500, detail="Storj storage not configured")
    
    if not supabase_document_service.enabled:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Get document record
        doc_record = await supabase_document_service.get_document_by_id(document_id)
        
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate pre-signed URL
        share_url = storj_client.generate_download_url(
            object_key=doc_record['storj_object_key'],
            expiration_hours=expiration_hours
        )
        
        if not share_url:
            raise HTTPException(status_code=500, detail="Failed to generate share link")
        
        # Prepare WhatsApp message
        doc_type_emoji = {
            'prescription': '💊',
            'lab_report': '🧪',
            'xray': '🩻',
            'mri': '🏥',
            'ct_scan': '🏥',
            'report': '📋',
            'default': '📄'
        }
        
        emoji = doc_type_emoji.get(doc_record['doc_type'], doc_type_emoji['default'])
        
        if message:
            whatsapp_message = message
        else:
            whatsapp_message = f"""
{emoji} *Your Medical Document is Ready!*

📁 *Document:* {doc_record['original_filename']}
📝 *Type:* {doc_record['doc_type'].replace('_', ' ').title()}

🔗 *Download Link:* 
{share_url}

⏱️ *Link expires in {expiration_hours} hours*

_Click the link above to download your document securely._

- AyurEze Healthcare Team 🌿
            """.strip()
        
        # Send via WhatsApp using custom client
        try:
            whatsapp_client = get_whatsapp_client()
            
            if whatsapp_client:
                result = await whatsapp_client.send_document_link(
                    patient_phone=phone_number,
                    patient_name="Patient",
                    document_type=doc_record['doc_type'],
                    document_url=share_url,
                    expiry_hours=expiration_hours
                )
                
                # Update sharing tracking
                await supabase_document_service.mark_as_shared(document_id, shared_via='whatsapp')
                
                return {
                    "success": True,
                    "document_id": document_id,
                    "filename": doc_record['original_filename'],
                    "phone_number": phone_number,
                    "share_url": share_url,
                    "expires_in_hours": expiration_hours,
                    "whatsapp_sent": True,
                    "whatsapp_response": result
                }
            else:
                # WhatsApp client not available, return link only
                return {
                    "success": True,
                    "document_id": document_id,
                    "filename": doc_record['original_filename'],
                    "phone_number": phone_number,
                    "share_url": share_url,
                    "expires_in_hours": expiration_hours,
                    "whatsapp_sent": False,
                    "message": "WhatsApp client not configured. Share link manually."
                }
            
        except Exception as whatsapp_error:
            import traceback
            logger.error(f"WhatsApp sending failed: {whatsapp_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Still return the link even if WhatsApp fails
            return {
                "success": True,
                "document_id": document_id,
                "filename": doc_record['original_filename'],
                "phone_number": phone_number,
                "share_url": share_url,
                "expires_in_hours": expiration_hours,
                "whatsapp_sent": False,
                "error": str(whatsapp_error),
                "message": "Link generated but WhatsApp sending failed. You can share the link manually."
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
