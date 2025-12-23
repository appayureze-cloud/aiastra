"""
Model inference handling with LoRA adapter loading
"""

import asyncio
import logging
import torch
from typing import Optional, Dict, Any
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
    TextStreamer
)
from peft import PeftModel, PeftConfig
import gc

logger = logging.getLogger(__name__)

class ModelInference:
    """Handles model loading and inference operations"""
    
    def __init__(self, base_model_id: str, lora_model_id: str, device: str = "auto"):
        self.base_model_id = base_model_id
        self.lora_model_id = lora_model_id
        self.device = device
        self.model = None
        self.tokenizer = None
        self.loaded = False
        
    async def load_model(self):
        """Load the base model and LoRA adapter"""
        try:
            logger.info(f"Loading base model: {self.base_model_id}")
            
            # Configure quantization for T4 GPU
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_id,
                trust_remote_code=True,
                padding_side="left"
            )
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load base model with quantization
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_id,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2" if torch.cuda.is_available() else "eager"
            )
            
            logger.info(f"Loading LoRA adapter: {self.lora_model_id}")
            
            # Load LoRA adapter
            self.model = PeftModel.from_pretrained(
                self.model,
                self.lora_model_id,
                torch_dtype=torch.bfloat16
            )
            
            # Enable evaluation mode
            self.model.eval()
            
            # Merge LoRA weights for better inference performance
            try:
                logger.info("Merging LoRA adapter weights...")
                self.model = self.model.merge_and_unload()
            except Exception as e:
                logger.warning(f"Could not merge LoRA weights: {e}. Continuing with adapter.")
            
            self.loaded = True
            logger.info("Model loaded successfully")
            
            # Log memory usage
            if torch.cuda.is_available():
                logger.info(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
                logger.info(f"GPU memory cached: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.loaded = False
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.loaded and self.model is not None and self.tokenizer is not None
    
    async def generate_response(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True
    ) -> str:
        """Generate response using the loaded model"""
        
        if not self.is_loaded():
            raise RuntimeError("Model is not loaded")
        
        try:
            # Format prompt for Ayurveda context
            formatted_prompt = self._format_ayurveda_prompt(prompt)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    length_penalty=1.0
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], 
                skip_special_tokens=True
            )
            
            # Clean up the response
            response = self._clean_response(generated_text)
            
            # Clear cache to prevent memory issues
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return response
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise RuntimeError(f"Generation failed: {str(e)}")
    
    def _format_ayurveda_prompt(self, prompt: str) -> str:
        """Format prompt for Ayurveda context"""
        system_prompt = """You are an expert Ayurvedic practitioner with deep knowledge of traditional Indian medicine. Provide accurate, helpful information about Ayurvedic principles, treatments, herbs, and practices. Always emphasize consulting with qualified practitioners for medical advice.

User: """
        
        return f"{system_prompt}{prompt}\n\nAyurvedic Expert: "
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the generated response"""
        # Remove extra whitespace
        response = response.strip()
        
        # Remove potential artifacts
        response = response.replace("<|endoftext|>", "")
        response = response.replace("<|end|>", "")
        
        # Ensure proper sentence ending
        if response and not response.endswith(('.', '!', '?')):
            # Find the last complete sentence
            last_sentence_end = max(
                response.rfind('.'),
                response.rfind('!'),
                response.rfind('?')
            )
            if last_sentence_end > len(response) * 0.7:  # Keep if sentence is substantial
                response = response[:last_sentence_end + 1]
        
        return response
    
    def cleanup(self):
        """Clean up model resources"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
        
        self.loaded = False
        logger.info("Model resources cleaned up")
