"""
Astra Response Sanitizer - Final Safety Check

This module performs final sanitization on AI-generated responses
to ensure no unsafe content slips through.

This is the last line of defense before output.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class ResponseSanitizer:
    """
    Final response sanitization layer.
    
    RULES:
    - Removes any unsafe medical content
    - Blocks diagnosis, prescription, dosage
    - Adds mandatory disclaimers
    - Cannot be bypassed
    """
    
    def __init__(self, capability_agent=None):
        self.capability_agent = capability_agent
        self.unsafe_patterns = self._compile_unsafe_patterns()
        self.mandatory_disclaimers = self._build_disclaimers()
        logger.info("✅ Response Sanitizer initialized")
    
    def _compile_unsafe_patterns(self) -> Dict[str, List[Dict]]:
        """Compile patterns for unsafe content"""
        return {
            "diagnosis": [
                {
                    "pattern": re.compile(r'(?i)\b(you have|you are suffering from|diagnosed with|this is)\s+\w+', re.IGNORECASE),
                    "replacement": "Please consult a doctor for proper diagnosis.",
                    "severity": "high"
                },
                {
                    "pattern": re.compile(r'(?i)\b(it seems like you have|appears to be|looks like)\s+\w+', re.IGNORECASE),
                    "replacement": "Only a doctor can make a diagnosis.",
                    "severity": "high"
                },
            ],
            "prescription": [
                {
                    "pattern": re.compile(r'(?i)\b(take|use|try)\s+\d+\s*(mg|ml|tablets|capsules)', re.IGNORECASE),
                    "replacement": "Please consult your doctor for dosage information.",
                    "severity": "high"
                },
                {
                    "pattern": re.compile(r'(?i)\b(prescribe|recommend taking|should take)\s+\w+', re.IGNORECASE),
                    "replacement": "Please consult your doctor for prescription.",
                    "severity": "high"
                },
            ],
            "treatment": [
                {
                    "pattern": re.compile(r'(?i)\b(this will cure|this treats|this heals)\s+\w+', re.IGNORECASE),
                    "replacement": "Please discuss treatment options with your doctor.",
                    "severity": "medium"
                },
            ],
            "prognosis": [
                {
                    "pattern": re.compile(r'(?i)\b(you will|you should|it will)\s+(get better|heal|recover|improve)', re.IGNORECASE),
                    "replacement": "Please consult your doctor about your prognosis.",
                    "severity": "medium"
                },
            ],
        }
    
    def _build_disclaimers(self) -> Dict[str, str]:
        """Build mandatory disclaimers"""
        return {
            "medical_advice": "\n\n⚠️ This is not medical advice. Please consult a licensed healthcare professional.",
            "diagnosis": "\n\n⚠️ This is not a diagnosis. Only a licensed doctor can diagnose medical conditions.",
            "prescription": "\n\n⚠️ This is not a prescription. Please consult your doctor for proper medication.",
            "emergency": "\n\n🚨 If this is an emergency, please call 108/112 immediately.",
        }
    
    def sanitize(self, response: str, safety_rules: List[str] = None) -> str:
        """
        Sanitize response to remove unsafe content.
        
        Args:
            response: AI-generated response
            safety_rules: List of safety rules to enforce
        
        Returns:
            Sanitized response
        """
        sanitized = response
        violations_found = []
        
        # ASTRA 2.0.0 Post-LLM Safety Scan
        if self.capability_agent:
            config = self.capability_agent.capabilities
            scan_config = config.get('post_llm_safety_scan', {})
            forbidden_patterns = scan_config.get('forbidden_patterns', [])
            action = scan_config.get('action_on_violation', 'DISCARD_AND_REFUSE')
            
            for pattern_str in forbidden_patterns:
                if re.search(pattern_str, sanitized, re.IGNORECASE):
                    logger.warning("🚨 Forbidden pattern detected in LLM output: %s", pattern_str)
                    if action == 'DISCARD_AND_REFUSE':
                        return "I apologize, but I cannot provide that information as it contains medical advice or treatment recommendations. Please consult a qualified Ayurvedic doctor."

        # Check each unsafe pattern category (legacy patterns)
        for category, patterns in self.unsafe_patterns.items():
            for pattern_def in patterns:
                pattern = pattern_def["pattern"]
                replacement = pattern_def["replacement"]
                severity = pattern_def["severity"]
                
                if pattern.search(sanitized):
                    # Replace unsafe content
                    sanitized = pattern.sub(replacement, sanitized)
                    violations_found.append({
                        "category": category,
                        "severity": severity
                    })
                    logger.warning("⚠️ Unsafe content sanitized: %s (severity: %s)", 
                                 category, severity)
        
        # Add mandatory disclaimers based on safety rules
        if safety_rules:
            if "must_recommend_doctor" in safety_rules:
                if self.mandatory_disclaimers["medical_advice"] not in sanitized:
                    sanitized += self.mandatory_disclaimers["medical_advice"]
            
            if "no_diagnosis" in safety_rules:
                # Check if response might be interpreted as diagnosis
                if self._contains_diagnostic_language(sanitized):
                    if self.mandatory_disclaimers["diagnosis"] not in sanitized:
                        sanitized += self.mandatory_disclaimers["diagnosis"]
        
        # Add emergency disclaimer if emergency keywords detected
        if self._contains_emergency_keywords(response):
            if self.mandatory_disclaimers["emergency"] not in sanitized:
                sanitized += self.mandatory_disclaimers["emergency"]
        
        # Log sanitization
        if violations_found:
            logger.info("🧹 Response sanitized: %d violations removed", len(violations_found))
        
        return sanitized
    
    def _contains_diagnostic_language(self, text: str) -> bool:
        """Check if text contains diagnostic language"""
        diagnostic_keywords = [
            r'\b(symptoms of|signs of|indicates|suggests)\b',
            r'\b(condition|disease|disorder|syndrome)\b',
            r'\b(may have|might have|could be)\b',
        ]
        
        for pattern in diagnostic_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_emergency_keywords(self, text: str) -> bool:
        """Check if text contains emergency keywords"""
        emergency_keywords = [
            r'\b(emergency|urgent|critical|severe)\b',
            r'\b(chest pain|heart attack|stroke)\b',
            r'\b(bleeding|unconscious|seizure)\b',
        ]
        
        for pattern in emergency_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def validate_response(self, response: str) -> Dict:
        """
        Validate response for safety (without modifying).
        
        Args:
            response: Response to validate
        
        Returns:
            {
                "safe": bool,
                "violations": List[Dict],
                "warnings": List[str]
            }
        """
        violations = []
        warnings = []
        
        # Check for unsafe patterns
        for category, patterns in self.unsafe_patterns.items():
            for pattern_def in patterns:
                pattern = pattern_def["pattern"]
                severity = pattern_def["severity"]
                
                if pattern.search(response):
                    violations.append({
                        "category": category,
                        "severity": severity,
                        "pattern": pattern.pattern
                    })
        
        # Check for diagnostic language
        if self._contains_diagnostic_language(response):
            warnings.append("Response contains diagnostic language")
        
        # Determine if safe
        high_severity_violations = [v for v in violations if v["severity"] == "high"]
        is_safe = len(high_severity_violations) == 0
        
        return {
            "safe": is_safe,
            "violations": violations,
            "warnings": warnings
        }
