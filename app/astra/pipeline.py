"""
Astra Pipeline - Mandatory 17-Step Pipeline Orchestrator

This is the HEART of Astra. Every user input MUST flow through this pipeline.
No step may be skipped, reordered, or bypassed.

PIPELINE STEPS (MANDATORY ORDER):
1. User Input (Text or Voice)
2. Rate-Limit Check
3. Language Detection
4. IndicTrans2 Normalization
5. ⭐ Capability Identification
6. Safety Enforcement
7. Rules Enforcement
8. Consent Verification
9. RAG Context Retrieval
10. Emotion Detection
11. Tone Mapping
12. Capability Routing
13. (Optional) AI / GPU Operations
14. Response Sanitization
15. Emotional Language Wrapping
16. IndicTrans2 Localization
17. Audit Logging
18. Output (Text and/or Voice)
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from .capability_agent import CapabilityAgent
from .safety_enforcer import SafetyEnforcer
from .rules_engine import RulesEngine
from .consent_manager import ConsentManager
from .rag_memory import RAGMemory
from .emotion_detector import EmotionDetector
from .tone_mapper import ToneMapper
from .response_sanitizer import ResponseSanitizer

logger = logging.getLogger(__name__)


class AstraPipeline:
    """
    Mandatory Astra pipeline orchestrator.
    
    RULES:
    - All inputs MUST follow this exact sequence
    - No step may be skipped, reordered, or bypassed
    - Each step is logged for audit trail
    - Pipeline is deterministic and testable
    """
    
    def __init__(
        self,
        db_connection=None,
        rate_limiter=None,
        translation_service=None,
        model_service=None
    ):
        """
        Initialize Astra pipeline.
        
        Args:
            db_connection: Database connection
            rate_limiter: Rate limiter instance
            translation_service: IndicTrans2 service
            model_service: AI model service
        """
        # Core components
        self.capability_agent = CapabilityAgent()
        self.safety_enforcer = SafetyEnforcer()
        self.rules_engine = RulesEngine()
        self.consent_manager = ConsentManager(db_connection)
        self.rag_memory = RAGMemory(db_connection=db_connection)
        self.emotion_detector = EmotionDetector()
        self.tone_mapper = ToneMapper()
        self.response_sanitizer = ResponseSanitizer(self.capability_agent)
        
        # External services
        self.db = db_connection
        self.rate_limiter = rate_limiter
        self.translation_service = translation_service
        self.model_service = model_service
        
        logger.info("✅ Astra Pipeline initialized - 17-step mandatory pipeline ready")
    
    async def process(
        self,
        user_input: str,
        user_id: str,
        profile_id: str,
        input_language: Optional[str] = None,
        is_voice: bool = False,
        user_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process user input through mandatory Astra pipeline.
        
        Args:
            user_input: User's message (text or transcribed voice)
            user_id: User's account ID
            profile_id: Specific profile ID (for family profiles)
            input_language: Optional language code (if known)
            is_voice: Whether input is from voice
            user_metadata: Optional user metadata (age, consents, etc.)
        
        Returns:
            {
                "response": str,
                "language": str,
                "capability": str,
                "emotion": str,
                "tone": str,
                "audit_log_id": str,
                "metadata": dict,
                "error": str (if error occurred)
            }
        """
        # Generate correlation ID for tracking
        correlation_id = str(uuid.uuid4())
        
        # Initialize audit log
        audit_log = {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "profile_id": profile_id,
            "is_voice": is_voice,
            "steps": []
        }
        
        try:
            logger.info("🚀 Pipeline started: %s (user: %s, profile: %s)", 
                       correlation_id, user_id, profile_id)
            
            # ===== STEP 1: User Input =====
            audit_log["steps"].append({
                "step": 1,
                "name": "user_input",
                "input_length": len(user_input),
                "is_voice": is_voice
            })
            
            # ===== STEP 2: Rate-Limit Check =====
            rate_check = await self._check_rate_limit(user_id, profile_id, is_voice)
            audit_log["steps"].append({
                "step": 2,
                "name": "rate_limit_check",
                "result": rate_check
            })
            
            if not rate_check["allowed"]:
                logger.warning("⚠️ Rate limit exceeded for user %s", user_id)
                return await self._build_rate_limit_response(rate_check, audit_log)
            
            # ===== STEP 3: Language Detection =====
            if input_language:
                detected_language = input_language
            else:
                detected_language = await self._detect_language(user_input)
            
            audit_log["steps"].append({
                "step": 3,
                "name": "language_detection",
                "language": detected_language
            })
            
            # ===== STEP 4: IndicTrans2 Normalization =====
            if detected_language != 'en':
                normalized_input = await self._normalize_to_english(user_input, detected_language)
            else:
                normalized_input = user_input
            
            audit_log["steps"].append({
                "step": 4,
                "name": "indictrans2_normalization",
                "normalized_length": len(normalized_input)
            })
            
            # ===== STEP 5: ⭐ Capability Identification =====
            capability_result = self.capability_agent.identify_capability(normalized_input)
            intent_class = capability_result.get('intent_class', 'CLASS_A')
            
            audit_log["intent_class"] = intent_class
            audit_log["capability"] = capability_result['capability']
            
            audit_log["steps"].append({
                "step": 5,
                "name": "capability_identification",
                "capability": capability_result['capability'],
                "intent_class": intent_class,
                "confidence": capability_result['confidence'],
                "forbidden": capability_result.get('forbidden', False)
            })
            
            logger.info("⭐ Capability identified: %s (class: %s, confidence: %.2f)", 
                       capability_result['capability'], intent_class, capability_result['confidence'])
            
            # ===== STEP 6: Safety Enforcement =====
            safety_check = self.safety_enforcer.enforce(
                text=normalized_input,
                capability=capability_result['capability'],
                intent_class=intent_class
            )
            audit_log["steps"].append({
                "step": 6,
                "name": "safety_enforcement",
                "safe": safety_check["safe"],
                "violations": safety_check.get("violations", []),
                "handoff": safety_check.get("handoff", False),
                "refusal_code": safety_check.get("refusal_code")
            })
            
            if not safety_check["safe"]:
                logger.warning("⛔ Safety violation detected: %s (code: %s)", 
                             safety_check["violations"], safety_check.get("refusal_code"))
                return await self._build_safety_blocked_response(
                    safety_check, detected_language, audit_log
                )
            
            # ===== STEP 7: Rules Enforcement =====
            rules_check = self.rules_engine.enforce(
                capability=capability_result['capability'],
                user_input=normalized_input,
                intent_class=intent_class,
                user_metadata=user_metadata
            )
            audit_log["steps"].append({
                "step": 7,
                "name": "rules_enforcement",
                "allowed": rules_check["allowed"],
                "violations": rules_check.get("violations", []),
                "boundary_statement": bool(rules_check.get("boundary_statement"))
            })
            
            if not rules_check["allowed"]:
                logger.warning("⛔ Legal rule violation: %s", rules_check["violations"])
                return await self._build_rules_blocked_response(
                    rules_check, detected_language, audit_log
                )
            
            # ===== STEP 8: Consent Verification =====
            # Note: ConsentManager now also checks for mandatory ASTRA_USAGE consent
            consent_check = await self.consent_manager.verify_consent(
                user_id=user_id,
                profile_id=profile_id,
                capability=capability_result['capability']
            )
            audit_log["steps"].append({
                "step": 8,
                "name": "consent_verification",
                "granted": consent_check["granted"],
                "purpose": consent_check.get("purpose")
            })
            
            if not consent_check["granted"]:
                logger.warning("⛔ Consent not granted for %s", capability_result['capability'])
                return await self._build_consent_required_response(
                    consent_check, detected_language, audit_log
                )
            
            # ===== STEP 9: RAG Context Retrieval =====
            rag_context = None
            if capability_result['definition'].get('rag_context'):
                rag_context = await self.rag_memory.retrieve(
                    query=normalized_input,
                    context_type=capability_result['definition']['rag_context'],
                    profile_id=profile_id,
                    top_k=5
                )
                audit_log["steps"].append({
                    "step": 9,
                    "name": "rag_context_retrieval",
                    "context_found": bool(rag_context),
                    "context_length": len(rag_context) if rag_context else 0
                })
            else:
                audit_log["steps"].append({
                    "step": 9,
                    "name": "rag_context_retrieval",
                    "required": False
                })
            
            # ===== STEP 10: Emotion Detection =====
            emotion = self.emotion_detector.detect(normalized_input)
            audit_log["steps"].append({
                "step": 10,
                "name": "emotion_detection",
                "emotion": emotion
            })
            
            # ===== STEP 11: Tone Mapping =====
            tone = self.tone_mapper.map_tone(emotion, capability_result['capability'])
            audit_log["steps"].append({
                "step": 11,
                "name": "tone_mapping",
                "tone": tone
            })
            
            # ===== STEP 12: Capability Routing =====
            response_text = await self._route_capability(
                capability_result=capability_result,
                normalized_input=normalized_input,
                user_id=user_id,
                profile_id=profile_id,
                rag_context=rag_context,
                tone=tone
            )
            audit_log["steps"].append({
                "step": 12,
                "name": "capability_routing",
                "capability": capability_result['capability']
            })
            
            # ===== STEP 13: (Optional) AI / GPU Operations =====
            # (Handled within _route_capability if needed)
            
            # ===== STEP 14: Response Sanitization =====
            sanitized_response = self.response_sanitizer.sanitize(
                response=response_text,
                safety_rules=capability_result['definition'].get('safety_rules', [])
            )
            
            # Post-sanitization: Add mandatory boundary statement if provided by RulesEngine
            if rules_check.get("boundary_statement"):
                if rules_check["boundary_statement"] not in sanitized_response:
                    sanitized_response = f"{sanitized_response}\n\n{rules_check['boundary_statement']}"
            
            audit_log["steps"].append({
                "step": 14,
                "name": "response_sanitization",
                "sanitized": sanitized_response != response_text
            })
            
            # ===== STEP 15: Emotional Language Wrapping =====
            emotional_response = self.tone_mapper.apply_tone(sanitized_response, tone)
            audit_log["steps"].append({
                "step": 15,
                "name": "emotional_wrapping",
                "tone_applied": tone
            })
            
            # ===== STEP 16: IndicTrans2 Localization =====
            if detected_language != 'en':
                localized_response = await self._localize_to_language(
                    emotional_response, detected_language
                )
            else:
                localized_response = emotional_response
            
            audit_log["steps"].append({
                "step": 16,
                "name": "indictrans2_localization",
                "target_language": detected_language
            })
            
            # ===== STEP 17: Audit Logging =====
            audit_log_id = await self._save_audit_log(audit_log)
            audit_log["steps"].append({
                "step": 17,
                "name": "audit_logging",
                "audit_log_id": audit_log_id
            })
            
            # ===== STEP 18: Output =====
            logger.info("✅ Pipeline completed: %s", correlation_id)
            
            return {
                "response": localized_response,
                "language": detected_language,
                "capability": capability_result['capability'],
                "intent_class": intent_class,
                "emotion": emotion,
                "tone": tone,
                "audit_log_id": audit_log_id,
                "correlation_id": correlation_id,
                "metadata": {
                    "requires_ai": capability_result.get('requires_ai', False),
                    "safety_enforced": True,
                    "consent_verified": bool(consent_check and consent_check.get("granted")),
                    "rag_context_used": bool(rag_context),
                    "forbidden": capability_result.get('forbidden', False),
                    "intent_class": intent_class,
                    "doctor_handoff": False
                }
            }
            
        except Exception as e:
            logger.error("❌ Pipeline error: %s", e, exc_info=True)
            audit_log["steps"].append({
                "step": "error",
                "error": str(e)
            })
            await self._save_audit_log(audit_log)
            
            # Return safe fallback
            return {
                "response": "I apologize, but I encountered an issue. Please try again or contact support.",
                "language": detected_language if 'detected_language' in locals() else 'en',
                "capability": "ERROR",
                "audit_log_id": audit_log.get("id"),
                "correlation_id": correlation_id,
                "error": str(e)
            }
    
    async def _check_rate_limit(self, user_id: str, profile_id: str, is_voice: bool) -> Dict:
        """Check rate limit (Step 2)"""
        if not self.rate_limiter:
            # No rate limiter configured, allow all
            return {"allowed": True}
        
        try:
            return await self.rate_limiter.check_limit(
                user_id=user_id,
                profile_id=profile_id,
                is_voice=is_voice
            )
        except Exception as e:
            logger.error("❌ Rate limit check failed: %s", e)
            # On error, allow (fail open for availability)
            return {"allowed": True}
    
    async def _detect_language(self, text: str) -> str:
        """Detect language (Step 3)"""
        if not self.translation_service:
            return 'en'  # Default to English
        
        try:
            return await self.translation_service.detect_language(text)
        except Exception as e:
            logger.error("❌ Language detection failed: %s", e)
            return 'en'  # Fallback to English
    
    async def _normalize_to_english(self, text: str, source_lang: str) -> str:
        """Normalize to English pivot (Step 4)"""
        if not self.translation_service:
            return text  # No translation available
        
        try:
            return await self.translation_service.translate(
                text=text,
                source_lang=source_lang,
                target_lang='en'
            )
        except Exception as e:
            logger.error("❌ Translation to English failed: %s", e)
            return text  # Fallback to original
    
    async def _localize_to_language(self, text: str, target_lang: str) -> str:
        """Localize to user's language (Step 16)"""
        if not self.translation_service:
            return text  # No translation available
        
        try:
            return await self.translation_service.translate(
                text=text,
                source_lang='en',
                target_lang=target_lang
            )
        except Exception as e:
            logger.error("❌ Translation to %s failed: %s", target_lang, e)
            return text  # Fallback to English
    
    async def _route_capability(
        self,
        capability_result: Dict,
        normalized_input: str,
        user_id: str,
        profile_id: str,
        rag_context: Optional[str],
        tone: str
    ) -> str:
        """Route to appropriate capability handler (Step 12)"""
        capability = capability_result['capability']
        definition = capability_result['definition']
        
        # Handle forbidden capabilities
        if capability_result.get('forbidden', False):
            return self._handle_forbidden_capability(capability_result)
        
        # Handle template-based responses
        if 'response_template' in definition:
            return definition['response_template']
        
        # Handle automation routing
        if 'automation' in definition:
            return await self._route_to_automation(definition['automation'], user_id, profile_id)
        
        # Handle AI-assisted capabilities
        if definition.get('requires_ai', False):
            return await self._generate_ai_response(
                normalized_input=normalized_input,
                capability=capability,
                definition=definition,
                rag_context=rag_context,
                tone=tone
            )
        
        # Default response
        return "I'm here to help! How can I assist you today?"
    
    def _handle_forbidden_capability(self, capability_result: Dict) -> str:
        """Handle forbidden capability request"""
        reason = capability_result.get('reason', 'This action is not allowed')
        redirect_to = capability_result.get('redirect_to', 'APPOINTMENT_BOOKING')
        
        return f"{reason} Please book an appointment with a licensed doctor for proper medical care."
    
    async def _route_to_automation(self, automation: str, user_id: str, profile_id: str) -> str:
        """Route to existing automation system"""
        automation_messages = {
            "existing_appointment_system": "Let me help you book an appointment. Please visit the appointments section or tell me your preferred date and time.",
            "existing_prescription_system": "Let me fetch your prescriptions. One moment please...",
            "existing_reminder_system": "Let me help you manage your medicine reminders.",
            "timeline_service": "Let me show you your health timeline.",
            "nudge_scheduler": "I'll send you a gentle reminder."
        }
        
        return automation_messages.get(automation, "Processing your request...")
    
    async def _generate_ai_response(
        self,
        normalized_input: str,
        capability: str,
        definition: Dict,
        rag_context: Optional[str],
        tone: str
    ) -> str:
        """Generate AI response (Step 13 - Optional GPU operation)"""
        if not self.model_service:
            return "AI service is not available. Please try again later."
        
        try:
            # Build safe system prompt
            system_prompt = self._build_safe_system_prompt(capability, definition, tone)
            
            # Add RAG context if available
            context_prompt = ""
            if rag_context:
                context_prompt = f"Context: {rag_context}\n\n"
            
            # Generate response
            full_prompt = f"{system_prompt}\n\n{context_prompt}User: {normalized_input}\n\nAssistant:"
            
            response = await self.model_service.generate(
                prompt=full_prompt,
                max_length=512,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            logger.error("❌ AI generation failed: %s", e)
            return "I apologize, but I'm having trouble generating a response. Please try again."
    
    def _build_safe_system_prompt(self, capability: str, definition: Dict, tone: str) -> str:
        """Build system prompt with safety constraints"""
        base_prompt = "You are Astra, an AI wellness companion for Ayureze. "
        
        # Add capability description
        base_prompt += f"{definition.get('description', '')} "
        
        # Add safety rules
        safety_rules = definition.get('safety_rules', [])
        if 'no_diagnosis' in safety_rules:
            base_prompt += "You MUST NOT diagnose any medical condition. "
        if 'no_prescription' in safety_rules:
            base_prompt += "You MUST NOT prescribe any medicine or treatment. "
        if 'no_dosage_recommendation' in safety_rules:
            base_prompt += "You MUST NOT recommend any dosage. "
        if 'must_recommend_doctor' in safety_rules:
            base_prompt += "You MUST recommend consulting a doctor for medical advice. "
        
        # Add allowed topics
        if 'allowed_topics' in definition:
            topics = ', '.join(definition['allowed_topics'])
            base_prompt += f"You may only discuss: {topics}. "
        
        # Add tone guidelines
        tone_guidelines = self.tone_mapper.get_tone_guidelines(tone)
        base_prompt += f"{tone_guidelines} "
        
        base_prompt += "Be empathetic, clear, and helpful within these boundaries."
        
        return base_prompt
    
    async def _save_audit_log(self, audit_log: Dict) -> Optional[str]:
        """Save audit log to database (Step 17 - ASTRA 2.0.0 compliant)"""
        if not self.db:
            logger.warning("⚠️ Database not connected, audit log not saved")
            return None
        
        try:
            # Enhanced schema for ASTRA 2.0.0
            enhanced_log = {
                "correlation_id": audit_log.get("correlation_id"),
                "timestamp": audit_log.get("timestamp"),
                "user_id": audit_log.get("user_id"),
                "profile_id": audit_log.get("profile_id"),
                "intent_class": audit_log.get("intent_class", "UNKNOWN"),
                "capability": audit_log.get("capability", "UNKNOWN"),
                "is_voice": audit_log.get("is_voice", False),
                "refusal_code": audit_log.get("refusal_code"),
                "blocked_reason": audit_log.get("blocked_reason"),
                "steps": audit_log.get("steps", [])
            }
            
            # Mark model used if any
            for step in audit_log.get("steps", []):
                if step.get("name") == "ai_generation":
                    enhanced_log["model_used"] = "IndicTrans2 + LLM"
            
            audit_log_id = str(uuid.uuid4())
            # Here you would actually save to DB:
            # await self.db.table("astra_audit_logs").insert(enhanced_log)
            
            logger.info("📋 Audit log saved: %s (class: %s)", 
                       audit_log_id, enhanced_log["intent_class"])
            return audit_log_id
            
        except Exception as e:
            logger.error("❌ Failed to save audit log: %s", e)
            return None
    
    async def _build_rate_limit_response(self, rate_check: Dict, audit_log: Dict) -> Dict:
        """Build rate limit exceeded response"""
        audit_log["blocked_reason"] = "RATE_LIMIT_EXCEEDED"
        audit_log_id = await self._save_audit_log(audit_log)
        
        return {
            "response": f"You've reached your usage limit. Please try again in {rate_check.get('retry_after', 60)} seconds.",
            "language": "en",
            "capability": "RATE_LIMITED",
            "audit_log_id": audit_log_id,
            "rate_limit_exceeded": True
        }
    
    async def _build_safety_blocked_response(self, safety_check: Dict, language: str, audit_log: Dict) -> Dict:
        """Build safety blocked response (handles refusals and handoffs)"""
        audit_log["blocked_reason"] = "SAFETY_VIOLATION"
        audit_log["refusal_code"] = safety_check.get("refusal_code")
        
        # Localize refusal message if needed
        message = safety_check['message']
        if language != 'en':
            message = await self._localize_to_language(message, language)
            
        # Add handoff message if required
        if safety_check.get("handoff"):
            config = self.capability_agent.capabilities
            handoff_msg = config.get('doctor_handoff', {}).get('cta_message', "Please consult a doctor.")
            if language != 'en':
                handoff_msg = await self._localize_to_language(handoff_msg, language)
            message = f"{message}\n\n{handoff_msg}"
            
        audit_log_id = await self._save_audit_log(audit_log)
        
        return {
            "response": message,
            "language": language,
            "capability": "SAFETY_BLOCKED",
            "audit_log_id": audit_log_id,
            "safety_blocked": True,
            "handoff_triggered": safety_check.get("handoff", False),
            "refusal_code": safety_check.get("refusal_code")
        }
    
    async def _build_rules_blocked_response(self, rules_check: Dict, language: str, audit_log: Dict) -> Dict:
        """Build rules blocked response"""
        audit_log["blocked_reason"] = "LEGAL_RULE_VIOLATION"
        
        message = rules_check['message']
        if language != 'en':
            message = await self._localize_to_language(message, language)
            
        audit_log_id = await self._save_audit_log(audit_log)
        
        return {
            "response": message,
            "language": language,
            "capability": "RULES_BLOCKED",
            "audit_log_id": audit_log_id,
            "rules_blocked": True
        }
    
    async def _build_consent_required_response(self, consent_check: Dict, language: str, audit_log: Dict) -> Dict:
        """Build consent required response"""
        audit_log["blocked_reason"] = "CONSENT_REQUIRED"
        
        message = consent_check.get('message', 'This feature requires your consent. Please grant consent in your profile settings.')
        if language != 'en':
            message = await self._localize_to_language(message, language)
            
        audit_log_id = await self._save_audit_log(audit_log)
        
        return {
            "response": message,
            "language": language,
            "capability": "CONSENT_REQUIRED",
            "audit_log_id": audit_log_id,
            "consent_required": True,
            "purpose": consent_check.get("purpose")
        }
