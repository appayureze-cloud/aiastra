"""
IndicTrans2 Translation Service
State-of-the-art neural machine translation for Indian languages
Powered by AI4Bharat's IndicTrans2 model
"""

import os
import logging
from typing import Optional, Dict, List, Tuple
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

class IndicTrans2Service:
    """
    IndicTrans2 translation service for high-quality Indian language translation
    
    Supports:
    - 22 Indian languages + English
    - Bidirectional translation (Indic ↔ English, Indic ↔ Indic)
    - Batch translation for efficiency
    - Caching for repeated translations
    """
    
    # Supported language codes (IndicTrans2 format)
    SUPPORTED_LANGUAGES = {
        "en": "eng_Latn",  # English
        "hi": "hin_Deva",  # Hindi
        "ta": "tam_Taml",  # Tamil
        "te": "tel_Telu",  # Telugu
        "bn": "ben_Beng",  # Bengali
        "mr": "mar_Deva",  # Marathi
        "gu": "guj_Gujr",  # Gujarati
        "kn": "kan_Knda",  # Kannada
        "ml": "mal_Mlym",  # Malayalam
        "pa": "pan_Guru",  # Punjabi
        "or": "ory_Orya",  # Odia
        "as": "asm_Beng",  # Assamese
        "ur": "urd_Arab",  # Urdu
        "sa": "san_Deva",  # Sanskrit
        "ne": "npi_Deva",  # Nepali
        "si": "sin_Sinh",  # Sinhala
        "ks": "kas_Arab",  # Kashmiri
        "sd": "snd_Arab",  # Sindhi
        "doi": "doi_Deva", # Dogri
        "mni": "mni_Mtei", # Manipuri
        "sat": "sat_Olck", # Santali
        "gom": "gom_Deva", # Konkani
    }
    
    def __init__(self):
        """Initialize IndicTrans2 service"""
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.use_gpu = False
        self.batch_size = 4
        
        # Check if HuggingFace token is available
        self.hf_token = os.getenv("HF_TOKEN")
        
        # Model configuration
        self.model_name = "ai4bharat/indictrans2-en-indic-1B"  # 1B parameter model
        self.indic_to_indic_model = "ai4bharat/indictrans2-indic-indic-1B"
        
        logger.info("IndicTrans2 service initialized (lazy loading)")
    
    async def load_model(self, direction: str = "en-indic"):
        """
        Load IndicTrans2 model asynchronously
        
        Args:
            direction: "en-indic", "indic-en", or "indic-indic"
        """
        if self.model_loaded:
            return True
        
        try:
            logger.info(f"🔄 Loading IndicTrans2 model ({direction})...")
            
            # Import transformers
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            import torch
            
            # Select model based on direction
            if direction == "indic-indic":
                model_name = self.indic_to_indic_model
            elif direction == "indic-en":
                model_name = "ai4bharat/indictrans2-indic-en-1B"
            else:
                model_name = self.model_name
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                token=self.hf_token
            )
            
            # Check GPU availability
            self.use_gpu = torch.cuda.is_available()
            device = "cuda" if self.use_gpu else "cpu"
            
            # Load model with optimizations
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                token=self.hf_token,
                torch_dtype=torch.float16 if self.use_gpu else torch.float32,
                low_cpu_mem_usage=True
            ).to(device)
            
            self.model.eval()  # Set to evaluation mode
            self.model_loaded = True
            
            logger.info(f"✅ IndicTrans2 model loaded successfully on {device}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load IndicTrans2 model: {e}")
            self.model_loaded = False
            return False
    
    def _get_flores_code(self, lang_code: str) -> Optional[str]:
        """Convert standard language code to FLORES-200 code"""
        return self.SUPPORTED_LANGUAGES.get(lang_code)
    
    @lru_cache(maxsize=1000)
    def _cached_translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Cached translation for repeated queries"""
        return self._translate_sync(text, src_lang, tgt_lang)
    
    def _translate_sync(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Synchronous translation (internal use)"""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Convert to FLORES codes
            src_flores = self._get_flores_code(src_lang)
            tgt_flores = self._get_flores_code(tgt_lang)
            
            if not src_flores or not tgt_flores:
                raise ValueError(f"Unsupported language pair: {src_lang} -> {tgt_lang}")
            
            # Prepare input with language tags
            input_text = f"{src_flores} {text}"
            
            # Tokenize
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=256
            )
            
            # Move to device
            if self.use_gpu:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_flores],
                    max_length=256,
                    num_beams=5,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=False
                )
            
            # Decode
            translation = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True
            )[0]
            
            return translation.strip()
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        use_cache: bool = True
    ) -> Dict[str, any]:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., "en", "hi", "ta")
            target_lang: Target language code
            use_cache: Whether to use cached translations
        
        Returns:
            Dict with translation result and metadata
        """
        try:
            # Validate languages
            if source_lang not in self.SUPPORTED_LANGUAGES:
                return {
                    "success": False,
                    "error": f"Unsupported source language: {source_lang}",
                    "supported_languages": list(self.SUPPORTED_LANGUAGES.keys())
                }
            
            if target_lang not in self.SUPPORTED_LANGUAGES:
                return {
                    "success": False,
                    "error": f"Unsupported target language: {target_lang}",
                    "supported_languages": list(self.SUPPORTED_LANGUAGES.keys())
                }
            
            # Same language - no translation needed
            if source_lang == target_lang:
                return {
                    "success": True,
                    "translation": text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "cached": False,
                    "note": "Same language, no translation performed"
                }
            
            # Determine model direction
            is_english_involved = source_lang == "en" or target_lang == "en"
            direction = "en-indic" if source_lang == "en" else "indic-en" if target_lang == "en" else "indic-indic"
            
            # Load model if not loaded
            if not self.model_loaded:
                await self.load_model(direction)
            
            # Translate (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            if use_cache:
                translation = await loop.run_in_executor(
                    None,
                    self._cached_translate,
                    text, source_lang, target_lang
                )
            else:
                translation = await loop.run_in_executor(
                    None,
                    self._translate_sync,
                    text, source_lang, target_lang
                )
            
            return {
                "success": True,
                "translation": translation,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": text,
                "model": "IndicTrans2-1B",
                "direction": direction,
                "cached": use_cache
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "source_lang": source_lang,
                "target_lang": target_lang
            }
    
    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[Dict[str, any]]:
        """
        Translate multiple texts in batch for efficiency
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            List of translation results
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Translate each text in batch
            batch_results = await asyncio.gather(*[
                self.translate(text, source_lang, target_lang)
                for text in batch
            ])
            
            results.extend(batch_results)
        
        return results
    
    def is_available(self) -> bool:
        """Check if translation service is available"""
        return self.model_loaded
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return list(self.SUPPORTED_LANGUAGES.keys())
    
    def get_language_pairs(self) -> List[Tuple[str, str]]:
        """Get all supported language pairs"""
        langs = self.get_supported_languages()
        pairs = []
        
        for src in langs:
            for tgt in langs:
                if src != tgt:
                    pairs.append((src, tgt))
        
        return pairs
    
    async def translate_with_fallback(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        fallback_text: Optional[str] = None
    ) -> str:
        """
        Translate with fallback to original text on error
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            fallback_text: Text to return on error (defaults to original text)
        
        Returns:
            Translated text or fallback
        """
        result = await self.translate(text, source_lang, target_lang)
        
        if result["success"]:
            return result["translation"]
        else:
            logger.warning(f"Translation failed, using fallback: {result.get('error')}")
            return fallback_text if fallback_text is not None else text


# Global IndicTrans2 service instance
indictrans2_service = IndicTrans2Service()
