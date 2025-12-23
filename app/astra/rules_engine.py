"""
Astra Rules Engine - Legal Boundary Enforcement

This module enforces legal and regulatory compliance rules:
- Indian Medical Council regulations
- Telemedicine Practice Guidelines 2020
- DISHA (Digital Information Security in Healthcare Act)
- IT Act 2000
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RulesEngine:
    """
    Legal boundary enforcement engine.
    
    RULES:
    - Enforces Indian medical and telemedicine laws
    - Cannot be bypassed
    - Logs all rule violations
    - Deterministic rule evaluation
    """
    
    def __init__(self):
        self.rules = self._load_legal_rules()
        logger.info("✅ Rules Engine initialized with %d legal rules", len(self.rules))
    
    def _load_legal_rules(self) -> Dict:
        """Load legal compliance rules (ASTRA 2.0.0)"""
        return {
            "no_diagnosis_without_license": {
                "description": "Only licensed practitioners can diagnose",
                "regulation": "Indian Medical Council Act 1956",
                "applies_to_class": ["CLASS_C", "CLASS_D"],
                "enforcement": "block"
            },
            "no_prescription_without_license": {
                "description": "Only licensed Ayurvedic doctors can prescribe",
                "regulation": "Drugs and Cosmetics Act 1940",
                "applies_to_class": ["CLASS_C"],
                "enforcement": "block"
            },
            "telemedicine_consent_required": {
                "description": "Explicit consent required for telemedicine",
                "regulation": "Telemedicine Practice Guidelines 2020",
                "applies_to": ["APPOINTMENT_BOOKING"],
                "enforcement": "require_consent"
            },
            "data_minimization": {
                "description": "Collect only necessary health data",
                "regulation": "DPDP Act 2023",
                "applies_to": ["all"],
                "enforcement": "log"
            },
            "astra_boundary_statement": {
                "description": "Boundary statement required for clinical theory",
                "regulation": "AYUSH Ethical Guidelines",
                "applies_to_class": ["CLASS_B_PLUS"],
                "enforcement": "append_statement"
            }
        }
    
    def enforce(self, capability: str, user_input: str, intent_class: str = "CLASS_A", user_metadata: Dict = None) -> Dict:
        """
        Enforce legal and golden rules for a capability.
        
        Args:
            capability: Capability being executed
            user_input: User's input text
            intent_class: Specified intent class (ASTRA 2.0.0)
            user_metadata: Optional user metadata
        
        Returns:
            {
                "allowed": bool,
                "violations": List[str],
                "message": str,
                "required_actions": List[str],
                "boundary_statement": str
            }
        """
        violations = []
        required_actions = []
        boundary_statement = ""
        
        # Check each rule
        for rule_name, rule_def in self.rules.items():
            applies_to = rule_def.get('applies_to', [])
            applies_to_class = rule_def.get('applies_to_class', [])
            
            # Check if rule applies to this capability or class
            if ('all' in applies_to or capability in applies_to or 
                intent_class in applies_to_class):
                
                enforcement = rule_def.get('enforcement')
                
                if enforcement == 'block':
                    # Check if this class is blocked
                    if intent_class in ["CLASS_C", "CLASS_D"]:
                        violations.append(rule_name)
                
                elif enforcement == 'require_consent':
                    # Check if consent is required (already handled by ConsentManager mostly, but here as a safety)
                    if not self._has_consent(user_metadata, rule_name):
                        required_actions.append(f"consent_required:{rule_name}")
                
                elif enforcement == 'append_statement':
                    # Get the mandatory boundary statement from config usually, but here as a rule
                    # ASTRA 2.0.0 mandatory statement
                    boundary_statement = "This explanation is for educational understanding of Ayurvedic concepts. Diagnosis and treatment decisions must be taken by a qualified Ayurvedic doctor."
                
                elif enforcement == 'log':
                    logger.info("📋 Compliance rule logged: %s (class: %s)", 
                               rule_name, intent_class)
        
        # Build response
        if violations:
            return {
                "allowed": False,
                "violations": violations,
                "message": self._get_violation_message(violations[0]),
                "required_actions": required_actions,
                "boundary_statement": ""
            }
        elif required_actions:
            return {
                "allowed": False,
                "violations": [],
                "message": "This action requires your consent. Please grant consent to continue.",
                "required_actions": required_actions,
                "boundary_statement": ""
            }
        else:
            return {
                "allowed": True,
                "violations": [],
                "message": "",
                "required_actions": [],
                "boundary_statement": boundary_statement
            }
    
    def _is_violation(self, rule_name: str, capability: str, user_input: str, 
                     user_metadata: Dict = None) -> bool:
        """Check if a specific rule is violated"""
        
        # No diagnosis without license
        if rule_name == "no_diagnosis_without_license":
            if capability in ["DIAGNOSIS"]:
                return True
        
        # No prescription without license
        elif rule_name == "no_prescription_without_license":
            if capability in ["PRESCRIPTION", "TREATMENT_MODIFICATION"]:
                return True
        
        # No autonomous medical decisions
        elif rule_name == "no_autonomous_medical_decisions":
            # This is enforced by capability system itself
            return False
        
        return False
    
    def _has_consent(self, user_metadata: Dict = None, rule_name: str = None) -> bool:
        """Check if user has given required consent"""
        if not user_metadata:
            return False
        
        consents = user_metadata.get('consents', {})
        
        if rule_name == "telemedicine_consent_required":
            return consents.get('telemedicine', False)
        elif rule_name == "minor_guardian_consent":
            is_minor = user_metadata.get('is_minor', False)
            if is_minor:
                return consents.get('guardian_consent', False)
            return True  # Not a minor, no guardian consent needed
        
        return True
    
    def _get_violation_message(self, rule_name: str) -> str:
        """Get user-friendly message for a rule violation"""
        rule_def = self.rules.get(rule_name, {})
        description = rule_def.get('description', 'This action is not allowed')
        
        messages = {
            "no_diagnosis_without_license": 
                "I cannot diagnose medical conditions. Please consult a licensed healthcare professional for proper diagnosis.",
            "no_prescription_without_license":
                "I cannot prescribe medicines. Please consult a licensed Ayurvedic doctor for prescription.",
            "no_autonomous_medical_decisions":
                "Medical decisions require consultation with a licensed healthcare professional.",
        }
        
        return messages.get(rule_name, description)
    
    def get_applicable_regulations(self, capability: str) -> List[str]:
        """Get list of regulations applicable to a capability"""
        regulations = []
        
        for rule_name, rule_def in self.rules.items():
            applies_to = rule_def.get('applies_to', [])
            if 'all' in applies_to or capability in applies_to:
                regulation = rule_def.get('regulation')
                if regulation and regulation not in regulations:
                    regulations.append(regulation)
        
        return regulations
