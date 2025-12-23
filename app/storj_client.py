"""
Storj Decentralized Storage Client for Medical Documents
Handles secure upload, download, and sharing of patient documents
"""

import os

# CRITICAL: Set these environment variables BEFORE importing boto3
# boto3 1.36.0+ has mandatory checksum validation that breaks Storj compatibility
os.environ['AWS_REQUEST_CHECKSUM_CALCULATION'] = 'when_required'
os.environ['AWS_RESPONSE_CHECKSUM_VALIDATION'] = 'when_required'

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class StorjClient:
    """Client for Storj decentralized storage with medical document focus"""
    
    def __init__(self):
        """Initialize Storj client with S3-compatible gateway"""
        self.access_key = os.getenv('STORJ_ACCESS_KEY')
        self.secret_key = os.getenv('STORJ_SECRET_KEY')
        self.endpoint = os.getenv('STORJ_ENDPOINT', 'https://gateway.storjshare.io')
        self.bucket_name = 'ayureze-medical-documents'
        
        if not self.access_key or not self.secret_key:
            raise ValueError("Storj credentials not found in environment variables")
        
        # Initialize S3-compatible client with Storj-specific configuration
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
        
        logger.info(f"Storj client initialized with endpoint: {self.endpoint}")
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def upload_document(
        self, 
        file_path: str, 
        patient_id: str, 
        doc_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Upload medical document to Storj
        
        Args:
            file_path: Local path to the document
            patient_id: Patient identifier
            doc_type: Document type (prescription, lab_report, xray, etc.)
            metadata: Additional metadata
        
        Returns:
            Object key if successful, None otherwise
        """
        try:
            filename = os.path.basename(file_path)
            
            # Create secure folder structure using hashed patient ID for privacy
            patient_hash = hashlib.sha256(patient_id.encode()).hexdigest()[:16]
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            object_key = f"patients/{patient_hash}/{doc_type}/{timestamp}_{filename}"
            
            # Prepare metadata
            doc_metadata = {
                'patient-id': patient_id,
                'doc-type': doc_type,
                'upload-timestamp': datetime.now(timezone.utc).isoformat(),
                'original-filename': filename
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            # Upload file using put_object with explicit file size for Storj compatibility
            with open(file_path, 'rb') as file_data:
                file_content = file_data.read()
                file_size = len(file_content)
                
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_content,
                    ContentLength=file_size,
                    ContentType=self._get_content_type(filename),
                    Metadata=doc_metadata
                )
            
            logger.info(f"Uploaded document: {object_key}")
            return object_key
            
        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            return None
    
    def download_document(self, object_key: str, download_path: str) -> bool:
        """
        Download document from Storj
        
        Args:
            object_key: Storj object key
            download_path: Local path to save the file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            Path(download_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.bucket_name,
                object_key,
                download_path
            )
            
            logger.info(f"Downloaded document to: {download_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed for {object_key}: {e}")
            return False
    
    def list_patient_documents(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        List all documents for a specific patient
        
        Args:
            patient_id: Patient identifier
        
        Returns:
            List of document metadata
        """
        try:
            patient_hash = hashlib.sha256(patient_id.encode()).hexdigest()[:16]
            prefix = f"patients/{patient_hash}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            documents = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Get metadata
                    try:
                        meta_response = self.s3_client.head_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        
                        documents.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'metadata': meta_response.get('Metadata', {}),
                            'content_type': meta_response.get('ContentType', 'application/octet-stream')
                        })
                    except Exception as meta_error:
                        logger.warning(f"Could not fetch metadata for {obj['Key']}: {meta_error}")
            
            logger.info(f"Found {len(documents)} documents for patient {patient_id}")
            return documents
            
        except Exception as e:
            logger.error(f"List failed for patient {patient_id}: {e}")
            return []
    
    def generate_download_url(
        self, 
        object_key: str, 
        expiration_hours: int = 24
    ) -> Optional[str]:
        """
        Generate time-limited pre-signed download URL
        
        Args:
            object_key: Storj object key
            expiration_hours: URL expiration time in hours (default: 24)
        
        Returns:
            Pre-signed URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration_hours * 3600
            )
            
            logger.info(f"Generated download URL for {object_key} (expires in {expiration_hours}h)")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate URL for {object_key}: {e}")
            return None
    
    def delete_document(self, object_key: str) -> bool:
        """
        Delete document from Storj
        
        Args:
            object_key: Storj object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"Deleted document: {object_key}")
            return True
            
        except Exception as e:
            logger.error(f"Delete failed for {object_key}: {e}")
            return False
    
    def get_document_metadata(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata without downloading
        
        Args:
            object_key: Storj object key
        
        Returns:
            Metadata dictionary or None if failed
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'metadata': response.get('Metadata', {}),
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                'etag': response.get('ETag')
            }
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {object_key}: {e}")
            return None
    
    @staticmethod
    def _get_content_type(filename: str) -> str:
        """Determine content type from filename"""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'dcm': 'application/dicom',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xml': 'application/xml',
            'json': 'application/json'
        }
        return content_types.get(ext, 'application/octet-stream')
