"""
Astra Capability Agent - Deterministic Intent Classifier

This module implements the deterministic capability identification agent.
It ONLY classifies user intent and routes to appropriate capabilities.
It does NOT reason, plan, or make autonomous decisions.
"""

import re
import yaml
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CapabilityAgent:
    """
    Deterministic capability identification agent.
    
    RULES:
    - ONLY classifies intent
    - Does NOT reason or plan
    - Does NOT execute actions
    - Deterministic and testable
    - Language-agnostic (works on English pivot)
    """
    
    def __init__(self):
        self.capabilities = self._load_capabilities()
        self.trigger_patterns = self._compile_triggers()
        self.forbidden_patterns = self._compile_forbidden()
        logger.info("✅ Capability Agent initialized with %d capabilities", 
                   len(self.capabilities['capabilities']))
        
    def _load_capabilities(self) -> Dict:
        """Load capability definitions from YAML"""
        config_path = Path(__file__).parent / "capabilities.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info("Loaded capabilities configuration from %s", config_path)
                return config
        except Exception as e:
            logger.error("Failed to load capabilities.yaml: %s", e)
            raise
    
    def _compile_triggers(self) -> Dict[str, List[re.Pattern]]:
        """Compile trigger patterns for fast matching"""
        patterns = {}
        for cap_name, cap_def in self.capabilities['capabilities'].items():
            if 'triggers' in cap_def and not cap_def.get('forbidden', False):
                patterns[cap_name] = [
                    re.compile(rf'\b{re.escape(trigger)}\b', re.IGNORECASE)
                    for trigger in cap_def['triggers']
                ]
        return patterns
    
    def _compile_forbidden(self) -> Dict[str, List[re.Pattern]]:
        """Compile forbidden capability patterns"""
        patterns = {}
        for cap_name, cap_def in self.capabilities['capabilities'].items():
            if cap_def.get('forbidden', False) and 'triggers' in cap_def:
                patterns[cap_name] = [
                    re.compile(rf'\b{re.escape(trigger)}\b', re.IGNORECASE)
                    for trigger in cap_def['triggers']
                ]
        return patterns
    
    def identify_capability(self, user_input: str) -> Dict:
        """
        Identify capability from user input.
        
        Args:
            user_input: User's message (should be in English pivot language)
        
        Returns:
            {
                "capability": "CAPABILITY_NAME",
                "intent_class": "CLASS_X",
                "confidence": 0.95,
                "matched_trigger": "trigger phrase",
                "requires_ai": bool,
                "requires_consent": bool,
                "rate_limit": str,
                "forbidden": bool,
                "priority": int,
                "definition": dict
            }
        """
        # Normalize input
        normalized = user_input.lower().strip()
        
        # PRIORITY 1: Check emergency first (CLASS_D detection)
        if self._is_emergency(normalized):
            logger.info("🚨 Emergency detected in input (CLASS_D)")
            return self._build_result("EMERGENCY_REDIRECT", 1.0, "emergency")
        
        # PRIORITY 2: Check forbidden patterns (CLASS_C detection)
        forbidden = self._check_forbidden(normalized)
        if forbidden:
            logger.warning("⛔ Forbidden capability requested (CLASS_C): %s", forbidden['capability'])
            return forbidden
        
        # PRIORITY 3: Match against capability triggers
        matches = self._match_triggers(normalized)
        
        # Return best match or default to general wellness
        if matches:
            # Sort by priority (lower number = higher priority) and then confidence
            best_match = min(matches, key=lambda x: (x['priority'], -x['confidence']))
            logger.info("✅ Capability identified: %s (class: %s, confidence: %.2f)", 
                       best_match['capability'], best_match['intent_class'], best_match['confidence'])
            return best_match
        else:
            logger.info("ℹ️ No specific capability matched, defaulting to GENERAL_WELLNESS_CHAT (CLASS_A)")
            return self._build_result("GENERAL_WELLNESS_CHAT", 0.7, "default")
    
    def _is_emergency(self, text: str) -> bool:
        """Check for emergency keywords (consistent with CLASS_D expanded taxonomy)"""
        emergency_keywords = [
            'emergency', 'urgent', 'heart attack', 'chest pain',
            'can\'t breathe', 'cannot breathe', 'breathlessness',
            'bleeding', 'severe bleeding', 'unconscious', 'loss of consciousness',
            'seizure', 'stroke', 'sudden paralysis', 'severe pain',
            'high fever', 'suicidal', 'self harm', 'help me'
        ]
        return any(keyword in text for keyword in emergency_keywords)
    
    def _check_forbidden(self, text: str) -> Optional[Dict]:
        """Check if input requests forbidden capability (CLASS_C)"""
        for forbidden_cap, patterns in self.forbidden_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    cap_def = self.capabilities['capabilities'][forbidden_cap]
                    return {
                        "capability": forbidden_cap,
                        "intent_class": cap_def.get('intent_class', 'CLASS_C'),
                        "confidence": 1.0,
                        "matched_trigger": pattern.pattern,
                        "forbidden": True,
                        "reason": cap_def.get('reason', 'This action is not allowed'),
                        "redirect_to": cap_def.get('redirect_to', 'APPOINTMENT_BOOKING'),
                        "priority": cap_def.get('priority', 1),
                        "definition": cap_def
                    }
        return None
    
    def _match_triggers(self, text: str) -> List[Dict]:
        """Match text against all capability triggers"""
        matches = []
        
        for cap_name, patterns in self.trigger_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    cap_def = self.capabilities['capabilities'][cap_name]
                    # Check for intent_class in cap_def, default to CLASS_A if missing
                    intent_class = cap_def.get('intent_class', 'CLASS_A')
                    
                    matches.append({
                        "capability": cap_name,
                        "intent_class": intent_class,
                        "confidence": 0.9,  # High confidence for exact trigger match
                        "matched_trigger": pattern.pattern,
                        "requires_ai": cap_def.get('requires_ai', False),
                        "requires_consent": cap_def.get('requires_consent', False),
                        "rate_limit": cap_def.get('rate_limit', 'default'),
                        "forbidden": False,
                        "priority": cap_def.get('priority', 3),
                        "definition": cap_def
                    })
        
        return matches
    
    def _build_result(self, capability: str, confidence: float, trigger: str) -> Dict:
        """Build capability identification result with intent class"""
        cap_def = self.capabilities['capabilities'][capability]
        return {
            "capability": capability,
            "intent_class": cap_def.get('intent_class', 'CLASS_A'),
            "confidence": confidence,
            "matched_trigger": trigger,
            "requires_ai": cap_def.get('requires_ai', False),
            "requires_consent": cap_def.get('requires_consent', False),
            "rate_limit": cap_def.get('rate_limit', 'default'),
            "forbidden": cap_def.get('forbidden', False),
            "priority": cap_def.get('priority', 3),
            "definition": cap_def
        }
    
    def get_capability_definition(self, capability_name: str) -> Optional[Dict]:
        """Get full definition of a capability"""
        return self.capabilities['capabilities'].get(capability_name)
    
    def list_all_capabilities(self) -> List[str]:
        """List all available capabilities"""
        return list(self.capabilities['capabilities'].keys())
    
    def get_safety_rules(self) -> Dict:
        """Get all safety rules"""
        return self.capabilities.get('safety_rules', {})
    
    def get_rate_limits(self) -> Dict:
        """Get rate limit configuration"""
        return self.capabilities.get('rate_limits', {})
