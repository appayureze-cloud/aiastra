"""
AI Agent API - Standalone endpoint for Ayurveda AI responses using your trained model
This API can be used by WhatsApp bot, prescriptions, or any other feature
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-agent", tags=["AI Agent"])

class AIAgentRequest(BaseModel):
    """Request model for AI agent"""
    question: str = Field(..., description="Patient's question or health query", min_length=1)
    language: str = Field(default="en", description="Response language: en, hi, ta, es")
    max_length: int = Field(default=512, description="Maximum response length", ge=50, le=2048)
    temperature: float = Field(default=0.7, description="Creativity level (0.1-1.0)", ge=0.1, le=1.0)
    context: Optional[str] = Field(None, description="Additional context (patient history, symptoms, etc.)")

class AIAgentResponse(BaseModel):
    """Response model for AI agent"""
    answer: str = Field(..., description="AI-generated Ayurveda advice")
    model_used: str = Field(..., description="Which model generated this response")
    language: str = Field(..., description="Response language")
    metadata: dict = Field(default={}, description="Additional metadata")

@router.post("/ask", response_model=AIAgentResponse)
async def ask_ai_agent(request: AIAgentRequest):
    """
    Ask the Ayurveda AI Agent a question
    
    This endpoint uses your trained Llama 3.1 8B model with Ayurveda LoRA
    
    **Examples:**
    ```json
    {
      "question": "What are the benefits of Triphala?",
      "language": "en"
    }
    ```
    
    ```json
    {
      "question": "त्रिफला के क्या लाभ हैं?",
      "language": "hi"
    }
    ```
    """
    try:
        # Import global model instance
        from main_enhanced import model_inference
        
        if not model_inference:
            raise HTTPException(
                status_code=503,
                detail="AI model not initialized. Please wait for server to fully start."
            )
        
        # Build full prompt with context if provided
        full_question = request.question
        if request.context:
            full_question = f"Context: {request.context}\n\nQuestion: {request.question}"
        
        # Generate AI response using your trained model
        logger.info(f"AI Agent query: {request.question[:100]}...")
        
        ai_response = await model_inference.generate_response(
            prompt=full_question,
            language=request.language,
            max_length=request.max_length,
            temperature=request.temperature
        )
        
        # Determine which model was used
        model_source = "Astra AI - Conversational Ayurveda Assistant"
        
        logger.info(f"✅ AI response generated: {len(ai_response)} chars using {model_source}")
        
        return AIAgentResponse(
            answer=ai_response,
            model_used=model_source,
            language=request.language,
            metadata={
                "question_length": len(request.question),
                "response_length": len(ai_response),
                "temperature": request.temperature
            }
        )
        
    except Exception as e:
        logger.error(f"AI Agent error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI response: {str(e)}"
        )

@router.get("/status")
async def get_ai_status():
    """
    Check AI Agent status
    
    Returns information about your trained model connection
    """
    try:
        from main_enhanced import model_inference
        
        if not model_inference:
            return {
                "status": "initializing",
                "model_loaded": False,
                "message": "AI model is initializing..."
            }
        
        return {
            "status": "ready",
            "model_loaded": model_inference.loaded,
            "model_name": "Astra AI - Conversational Ayurveda Assistant",
            "type": "Intelligent conversational responses",
            "message": "Astra AI Agent is ready with intelligent conversational responses!"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "model_loaded": False,
            "error": str(e)
        }

@router.post("/batch", response_model=List[AIAgentResponse])
async def ask_ai_batch(requests: List[AIAgentRequest]):
    """
    Ask multiple questions in batch
    
    Process up to 10 questions at once for efficiency
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 questions per batch request"
        )
    
    responses = []
    for req in requests:
        try:
            response = await ask_ai_agent(req)
            responses.append(response)
        except Exception as e:
            logger.error(f"Batch item failed: {str(e)}")
            # Add error response for failed items
            responses.append(AIAgentResponse(
                answer=f"Error: {str(e)}",
                model_used="error",
                language=req.language,
                metadata={"error": True}
            ))
    
    return responses
