"""
Pydantic models for API requests and responses
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ChatRequest(BaseModel):
    """Request model for chat completion"""
    message: str = Field(..., description="The input message/prompt")
    max_length: Optional[int] = Field(1024, description="Maximum length of generated text")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(50, description="Top-k sampling parameter")
    do_sample: Optional[bool] = Field(True, description="Whether to use sampling")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the benefits of turmeric in Ayurveda?",
                "max_length": 512,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50,
                "do_sample": True
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat completion"""
    response: str = Field(..., description="The generated response")
    model: str = Field(..., description="Model identifier")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Turmeric is highly valued in Ayurveda for its anti-inflammatory properties...",
                "model": "llama-3.1-8b + ayurveda-lora-v3",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 50,
                    "total_tokens": 60
                }
            }
        }

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Overall health status")
    model_loaded: bool = Field(..., description="Whether the model is loaded")
    gpu_available: bool = Field(..., description="Whether GPU is available")
    device: str = Field(..., description="Device information")

class ModelStatus(BaseModel):
    """Response model for detailed model status"""
    loaded: bool = Field(..., description="Whether the model is loaded")
    base_model: str = Field(..., description="Base model identifier")
    lora_model: str = Field(..., description="LoRA model identifier")
    device: str = Field(..., description="Device the model is loaded on")
    memory_usage: Optional[Dict[str, Any]] = Field(None, description="GPU memory usage")

class ChatSessionRequest(BaseModel):
    """Request model for creating a chat session"""
    user_id: str = Field(..., description="User identifier")
    language: Optional[str] = Field("en", description="Preferred language")

class ChatSessionResponse(BaseModel):
    """Response model for chat session creation"""
    session_id: str = Field(..., description="Created session identifier")
    user_id: str = Field(..., description="User identifier")
    language: str = Field(..., description="Session language")
    created_at: datetime = Field(..., description="Session creation time")

class EnhancedChatRequest(BaseModel):
    """Enhanced request model for chat with session support"""
    message: str = Field(..., description="The input message/prompt")
    session_id: Optional[str] = Field(None, description="Chat session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    language: Optional[str] = Field(None, description="Message language (auto-detected if not provided)")
    max_length: Optional[int] = Field(1024, description="Maximum length of generated text")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(50, description="Top-k sampling parameter")
    do_sample: Optional[bool] = Field(True, description="Whether to use sampling")
    
class EnhancedChatResponse(BaseModel):
    """Enhanced response model for chat with metadata"""
    response: str = Field(..., description="The generated response")
    session_id: Optional[str] = Field(None, description="Chat session identifier")
    language: str = Field(..., description="Detected/used language")
    is_ayurveda_related: bool = Field(..., description="Whether the question was Ayurveda-related")
    model: str = Field(..., description="Model identifier")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    
class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    messages: List[Dict[str, Any]] = Field(..., description="Chat message history")
    session_info: Dict[str, Any] = Field(..., description="Session information")
    
class UserSessionsResponse(BaseModel):
    """Response model for user sessions"""
    sessions: List[Dict[str, Any]] = Field(..., description="User chat sessions")
    total_count: int = Field(..., description="Total number of sessions")

# Auth0 Authentication Models
class AuthRequest(BaseModel):
    """Request model for Auth0 authentication"""
    access_token: str = Field(..., description="Auth0 access token")

class SessionResponse(BaseModel):
    """Response model for session creation"""
    session_token: str = Field(..., description="Session token for persistent authentication")
    session_id: str = Field(..., description="Database session ID")
    user: Dict[str, Any] = Field(..., description="User information")
    expires_at: str = Field(..., description="Session expiration time")

class UserInfo(BaseModel):
    """User information model"""
    id: str = Field(..., description="User ID from Auth0")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    picture: Optional[str] = Field(None, description="User profile picture URL")
    email_verified: bool = Field(False, description="Whether email is verified")

class StreamingChatRequest(BaseModel):
    """Request model for streaming chat responses"""
    message: str = Field(..., description="The input message/prompt")
    language: Optional[str] = Field(None, description="Language preference (auto-detected if None)")
    max_length: Optional[int] = Field(1024, description="Maximum length of generated text")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What herbs help with stress and anxiety?",
                "language": "en",
                "max_length": 1024,
                "temperature": 0.7
            }
        }

class AuthenticatedChatRequest(BaseModel):
    """Chat request model for authenticated users"""
    message: str = Field(..., description="The input message/prompt")
    session_token: Optional[str] = Field(None, description="Session token for authentication")
    language: Optional[str] = Field(None, description="Message language (auto-detected if not provided)")
    max_length: Optional[int] = Field(1024, description="Maximum length of generated text")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(50, description="Top-k sampling parameter")
    do_sample: Optional[bool] = Field(True, description="Whether to use sampling")

class AuthenticatedChatResponse(BaseModel):
    """Chat response model for authenticated users with session info"""
    response: str = Field(..., description="The generated response")
    session_id: str = Field(..., description="Database session identifier")
    user_id: str = Field(..., description="User identifier")
    language: str = Field(..., description="Detected/used language")
    is_ayurveda_related: bool = Field(..., description="Whether the question was Ayurveda-related")
    model: str = Field(..., description="Model identifier")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    created_at: str = Field(..., description="Message timestamp")

class ChatHistoryRequest(BaseModel):
    """Request model for chat history"""
    session_token: str = Field(..., description="Session token for authentication")
    session_id: Optional[str] = Field(None, description="Specific session ID (optional)")
    limit: Optional[int] = Field(50, description="Maximum number of messages to retrieve")
