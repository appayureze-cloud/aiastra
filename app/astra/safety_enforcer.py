"""
Astra Safety Enforcer - Non-Bypassable Safety Layer

This module enforces medical safety rules to prevent:
- Diagnosis
- Prescription
- Treatment advice
- Dosage recommendations
- Any medical decision-making
"""

import re
import logging
from typing import Dict, List
from .capability_agent import CapabilityAgent

logger = logging.getLogger(__name__)


class SafetyEnforcer:
    """
    Non-bypassable safety enforcement layer.
    
    RULES:
    - Blocks all prohibited medical content
    - Cannot be disabled or bypassed
    - Runs before any AI generation
    - Deterministic regex-based matching
    """
    
    def __init__(self):
        self.capability_agent = CapabilityAgent()
        self.safety_rules = self.capability_agent.get_safety_rules()
        self.compiled_patterns = self._compile_safety_patterns()
        logger.info("✅ Safety Enforcer initialized with %d rules", len(self.safety_rules))
    
    def _compile_safety_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile safety rule patterns for fast matching"""
        compiled = {}
        for rule_name, rule_def in self.safety_rules.items():
            if 'patterns' in rule_def:
                compiled[rule_name] = [
                    re.compile(pattern) for pattern in rule_def['patterns']
                ]
        return compiled
    
    def enforce(self, text: str, capability: str, intent_class: str = "CLASS_A") -> Dict:
        """
        Enforce safety rules on text.
        
        Args:
            text: Text to check (should be in English)
            capability: Current capability being executed
            intent_class: Specified intent class (ASTRA 2.0.0)
        
        Returns:
            {
                "safe": bool,
                "violations": List[str],
                "message": str,
                "blocked_patterns": List[str],
                "intent_class": str,
                "handoff": bool,
                "hard_stop": bool,
                "refusal_code": str
            }
        """
        violations = []
        blocked_patterns = []
        
        # ASTRA 2.0.0 Refusal Library logic
        # If intent_class is CLASS_C or CLASS_D, we must refuse immediately
        if intent_class in ["CLASS_C", "CLASS_D"]:
            refusal_info = self._get_refusal_info(intent_class, capability)
            logger.warning("⛔ Mandatory refusal for %s (class: %s)", capability, intent_class)
            return {
                "safe": False,
                "violations": [intent_class],
                "message": refusal_info["message"],
                "blocked_patterns": [],
                "intent_class": intent_class,
                "handoff": refusal_info.get("handoff", False),
                "hard_stop": refusal_info.get("hard_stop", False),
                "refusal_code": refusal_info.get("refusal_code", "UNKNOWN")
            }

        # Get capability definition to check which rules apply
        cap_def = self.capability_agent.get_capability_definition(capability)
        if not cap_def:
            logger.warning("Unknown capability: %s, applying all safety rules", capability)
            applicable_rules = list(self.safety_rules.keys())
        else:
            applicable_rules = cap_def.get('safety_rules', [])
        
        # Check each applicable safety rule
        for rule_name in applicable_rules:
            if rule_name in self.compiled_patterns:
                for pattern in self.compiled_patterns[rule_name]:
                    if pattern.search(text):
                        violations.append(rule_name)
                        blocked_patterns.append(pattern.pattern)
                        logger.warning("⚠️ Safety violation detected: %s", rule_name)
        
        # Build response
        if violations:
            # Get replacement message from first violation
            first_violation = violations[0]
            replacement = self.safety_rules[first_violation].get(
                'replacement',
                "I cannot provide this information. Please consult a licensed healthcare professional."
            )
            
            return {
                "safe": False,
                "violations": violations,
                "message": replacement,
                "blocked_patterns": blocked_patterns,
                "intent_class": intent_class,
                "handoff": False,
                "hard_stop": False,
                "refusal_code": "SAFETY_RULE_VIOLATION"
            }
        else:
            return {
                "safe": True,
                "violations": [],
                "message": "",
                "blocked_patterns": [],
                "intent_class": intent_class,
                "handoff": False,
                "hard_stop": False,
                "refusal_code": ""
            }
    
    def _get_refusal_info(self, intent_class: str, capability: str) -> Dict:
        """Get refusal info from the refusal library in configuration"""
        full_config = self.capability_agent.capabilities
        refusal_library = full_config.get('refusal_library', {})
        
        # Default fallback refusal
        default_refusal = {
            "message": "I cannot help with medical decisions. Please consult a qualified Ayurvedic doctor.",
            "refusal_code": "REF_GEN_001",
            "handoff": True,
            "hard_stop": False
        }
        
        class_refusals = refusal_library.get(intent_class, {})
        
        # Try to find specific refusal for capability/trigger type
        # We map cap name to refusal key
        cap_to_refusal = {
            "DIAGNOSIS": "DIAGNOSIS_CONFIRMATION",
            "PRESCRIPTION": "MEDICINE_REQUEST",
            "TREATMENT_MODIFICATION": "DOSAGE_CHANGE",
            "EMERGENCY_REDIRECT": "EMERGENCY"
        }
        
        refusal_key = cap_to_refusal.get(capability)
        refusal_data = class_refusals.get(refusal_key)
        
        if not refusal_data and intent_class == "CLASS_D":
            refusal_data = class_refusals.get("EMERGENCY")
            
        if refusal_data:
            # Pick a random message or first one
            import random
            messages = refusal_data.get('messages', [default_refusal["message"]])
            message = random.choice(messages)
            
            return {
                "message": message,
                "refusal_code": refusal_data.get('refusal_code', "REF_UNKNOWN"),
                "handoff": refusal_data.get('handoff', False),
                "hard_stop": refusal_data.get('hard_stop', False)
            }
            
        return default_refusal

    def sanitize_response(self, response: str, capability: str) -> str:
        """
        Sanitize AI-generated response to remove any unsafe content.
        
        Args:
            response: AI-generated response
            capability: Current capability
        
        Returns:
            Sanitized response with unsafe content removed/replaced
        """
        sanitized = response
        
        # Get capability definition
        cap_def = self.capability_agent.get_capability_definition(capability)
        if not cap_def:
            applicable_rules = list(self.safety_rules.keys())
        else:
            applicable_rules = cap_def.get('safety_rules', [])
        
        # Apply each safety rule
        for rule_name in applicable_rules:
            if rule_name in self.compiled_patterns:
                rule_def = self.safety_rules[rule_name]
                replacement = rule_def.get('replacement', '[REDACTED]')
                
                for pattern in self.compiled_patterns[rule_name]:
                    sanitized = pattern.sub(replacement, sanitized)
        
        # Append mandatory disclaimers if needed
        for rule_name in applicable_rules:
            rule_def = self.safety_rules.get(rule_name, {})
            if rule_def.get('action') == 'append':
                # Check if it already contains the message
                msg = rule_def.get('message', '')
                if msg and msg not in sanitized:
                    sanitized += msg
        
        return sanitized
    
    def is_medical_emergency(self, text: str) -> bool:
        """Check if text indicates a medical emergency (ASTRA 2.0.0 Expanded)"""
        emergency_patterns = [
            r'\b(heart attack|cardiac arrest)\b',
            r'\b(can\'t breathe|cannot breathe|difficulty breathing|breathlessness)\b',
            r'\b(severe bleeding|heavy bleeding|bleeding heavily)\b',
            r'\b(unconscious|passed out|loss of consciousness)\b',
            r'\b(seizure|convulsion)\b',
            r'\b(stroke|paralysis|sudden paralysis)\b',
            r'\b(severe pain|excruciating pain|chest pain)\b',
            r'\b(high fever|persistent fever)\b',
            r'\b(suicidal|self harm|kill myself|end my life)\b',
        ]
        
        for pattern in emergency_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
