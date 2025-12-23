"""
Guided meditation and breathing exercise generation for Astra
"""

import logging
from typing import Dict, List, Optional, Any
from app.voice_models import MeditationRequest, BreathingExerciseRequest
from app.language_utils import language_manager

logger = logging.getLogger(__name__)

class MeditationGenerator:
    """Generates personalized meditation scripts and breathing exercises"""
    
    def __init__(self):
        self.mantras = {
            "om": "ॐ (Om)",
            "peace": "ॐ शान्ति शान्ति शान्तिः (Om Shanti Shanti Shantih)",
            "healing": "ॐ त्र्यम्बकं यजामहे (Om Tryambakam Yajamahe)",
            "energy": "ॐ गं गणपतये नमः (Om Gam Ganapataye Namah)"
        }
        
        self.breathing_patterns = {
            "4-7-8": {"inhale": 4, "hold": 7, "exhale": 8, "cycles": 4},
            "box_breathing": {"inhale": 4, "hold": 4, "exhale": 4, "hold_2": 4},
            "nadi_shodhana": {"inhale": 4, "exhale": 4, "alternate": True},
            "bhramari": {"inhale": 4, "hold": 2, "exhale": 6, "humming": True}
        }
    
    async def generate_meditation_script(self, request: MeditationRequest) -> Dict[str, Any]:
        """Generate a personalized meditation script"""
        
        # Base script structure
        script_parts = []
        
        # Opening
        opening = self._generate_opening(request)
        script_parts.append(opening)
        
        # Body relaxation
        body_scan = self._generate_body_scan(request)
        script_parts.append(body_scan)
        
        # Main meditation focus
        main_practice = self._generate_main_practice(request)
        script_parts.append(main_practice)
        
        # Mantras if requested
        mantra_section = ""
        mantras_used = []
        if request.include_mantra:
            mantra_section, mantras_used = self._generate_mantra_section(request)
            script_parts.append(mantra_section)
        
        # Closing
        closing = self._generate_closing(request)
        script_parts.append(closing)
        
        full_script = "\n\n".join(script_parts)
        
        return {
            "script": full_script,
            "sections": ["Opening", "Body Scan", "Main Practice", "Mantras", "Closing"] if request.include_mantra else ["Opening", "Body Scan", "Main Practice", "Closing"],
            "mantras": mantras_used,
            "estimated_duration": request.duration
        }
    
    def _generate_opening(self, request: MeditationRequest) -> str:
        """Generate meditation opening"""
        dosha_specific = ""
        if request.user_dosha:
            dosha_guidance = {
                "vata": "As we begin, notice the natural rhythm of your breath, allowing your restless mind to settle like leaves finding stillness.",
                "pitta": "Let go of any goals or expectations for this practice. Simply be present with what is, cooling the fires of ambition.",
                "kapha": "Gently awaken your inner energy, breathing life and lightness into your being."
            }
            dosha_specific = dosha_guidance.get(request.user_dosha, "")
        
        openings = {
            "stress": f"""Welcome to this peaceful sanctuary of calm. Find a comfortable seated position, allowing your spine to be naturally erect yet relaxed. Close your eyes gently, like flower petals folding inward at dusk. {dosha_specific}
            
Take three deep, nourishing breaths. With each exhale, release the weight of the day. Feel your shoulders melting away from your ears, your jaw softening, your mind beginning to settle.""",
            
            "sleep": f"""Welcome to this gentle journey toward rest. Settle into your most comfortable position, whether lying down or sitting supported. {dosha_specific}
            
Allow your breathing to become naturally slower and deeper. Imagine roots growing from your body into the earth, grounding you in this moment of peace.""",
            
            "energy": f"""Welcome to this revitalizing practice. Sit with dignity and alertness, spine straight, crown of your head reaching toward the sky. {dosha_specific}
            
Feel the life force, the prana, flowing through you with each breath. Today we awaken the dormant energy within.""",
            
            "anxiety": f"""Welcome to this safe harbor of peace. Find your most secure and comfortable position. Know that in this moment, you are completely safe. {dosha_specific}
            
Place one hand on your heart, one on your belly. Feel the steady rhythm of life within you, constant and reassuring.""",
            
            "concentration": f"""Welcome to this practice of inner focus. Sit with alert awareness, your posture reflecting your intention to cultivate clarity. {dosha_specific}
            
Gather your scattered thoughts like collecting precious gems, bringing your full attention to this present moment."""
        }
        
        return openings.get(request.focus, openings["stress"])
    
    def _generate_body_scan(self, request: MeditationRequest) -> str:
        """Generate body relaxation section"""
        base_scan = """Now, let's bring awareness to your physical body. Starting from the crown of your head, imagine a warm, golden light beginning to flow downward.
        
Feel this healing light relaxing your forehead, releasing any tension between your eyebrows. Let it flow around your eyes, softening them completely.
        
Feel the light moving to your jaw, allowing it to drop slightly open. Your neck and shoulders receive this warm energy, letting go of any tightness.
        
Continue this flowing awareness down your arms, through your chest, feeling your heart center opening and softening. Let the light flow through your torso, your back, releasing and relaxing.
        
Feel this golden energy moving through your hips, down your legs, all the way to your toes. Your entire body is now bathed in relaxation and peace."""
        
        if request.experience_level == "beginner":
            return base_scan + "\n\nTake a moment to simply rest in this feeling of complete physical relaxation."
        else:
            return base_scan + "\n\nNotice how this relaxation affects your mental state. Observe the connection between body and mind."
    
    def _generate_main_practice(self, request: MeditationRequest) -> str:
        """Generate the main meditation practice"""
        practices = {
            "stress": """Now, bring your attention to your breath. Not changing it, simply observing. Notice how your breath flows in naturally, and flows out naturally.
            
If thoughts of stress or worry arise, imagine them as clouds passing through the vast sky of your awareness. You are the sky - unchanging, peaceful, infinite.
            
With each exhale, release tension. With each inhale, breathe in peace. Continue this rhythm, this dance of letting go and receiving.""",
            
            "sleep": """Allow your breathing to become even slower and deeper. With each exhale, feel yourself sinking deeper into relaxation, like settling into the softest bed.
            
Imagine yourself in a peaceful garden at twilight. Feel the gentle evening air, hear the soft sounds of nature settling into rest. 
            
Let your mind become like the quiet garden - still, peaceful, ready for the restorative gift of sleep.""",
            
            "energy": """Focus on your breath at the base of your spine. With each inhale, imagine drawing golden energy up through your spine, awakening each energy center.
            
Feel this vital life force moving through you, clearing away lethargy and awakening your natural vitality. You are connected to the infinite energy of the universe.
            
With each breath, feel more alive, more vibrant, more connected to your inner power.""",
            
            "anxiety": """Return to the feeling of your hands - one on your heart, one on your belly. Feel the steady rhythm beneath your palms. This is your anchor.
            
When anxiety arises, simply notice it without judgment. Say silently: 'I see you, anxiety. You are just a feeling, and feelings pass.'
            
Breathe into your heart center. With each breath, expand the space around any anxious feelings. You are larger than any temporary emotion.""",
            
            "concentration": """Choose a single point of focus - perhaps the sensation of breath at your nostrils, or a simple word like 'peace' or 'one.'
            
When your mind wanders, gently return to your chosen focus. Each return is a victory, strengthening your capacity for concentration.
            
Like training a muscle, each moment of focused attention builds your mental clarity and power."""
        }
        
        return practices.get(request.focus, practices["stress"])
    
    def _generate_mantra_section(self, request: MeditationRequest) -> tuple[str, List[str]]:
        """Generate mantra section if requested"""
        focus_mantras = {
            "stress": ["om", "peace"],
            "sleep": ["om", "peace"],
            "energy": ["energy", "om"],
            "anxiety": ["peace", "om"],
            "concentration": ["om"]
        }
        
        selected_mantras = focus_mantras.get(request.focus, ["om"])
        mantra_texts = [self.mantras[m] for m in selected_mantras if m in self.mantras]
        
        section = f"""Now we'll work with sacred sounds, mantras that have been used for thousands of years to calm and focus the mind.
        
Begin chanting slowly and softly: {' and '.join(mantra_texts)}
        
Let the vibration of these sacred sounds resonate through your entire being. Feel how the sound creates space and peace within you.
        
Continue chanting for the next few minutes, allowing the mantra to carry you deeper into meditation."""
        
        return section, mantra_texts
    
    def _generate_closing(self, request: MeditationRequest) -> str:
        """Generate meditation closing"""
        base_closing = """As we prepare to close this practice, take a moment to feel gratitude for this time you've given yourself.
        
Notice how you feel now compared to when you began. Any shift, however subtle, is a gift.
        
Begin to bring gentle movement back to your body. Wiggle your fingers and toes. Take a deeper breath.
        
When you're ready, slowly open your eyes. Carry this sense of peace with you into your day.
        
May you be at peace. May you be happy. May you be free from suffering. Namaste."""
        
        if request.focus == "sleep":
            return """As we close this practice, allow yourself to continue sinking into deeper relaxation. 
            
You may choose to continue lying here, drifting into peaceful sleep, or slowly transition to your bed.
            
Trust in your body's wisdom to rest and restore. May your sleep be deep and healing. Good night."""
        
        return base_closing
    
    async def generate_breathing_exercise(self, request: BreathingExerciseRequest) -> Dict[str, Any]:
        """Generate guided breathing exercise"""
        
        pattern = self.breathing_patterns.get(request.technique)
        if not pattern:
            raise ValueError(f"Unknown breathing technique: {request.technique}")
        
        instructions = self._get_breathing_instructions(request.technique, pattern)
        script = self._generate_breathing_script(request, pattern)
        
        return {
            "technique_name": self._get_technique_name(request.technique),
            "instructions": instructions,
            "script": script,
            "pattern": self._get_pattern_description(request.technique, pattern),
            "estimated_duration": request.duration
        }
    
    def _get_technique_name(self, technique: str) -> str:
        """Get proper name for breathing technique"""
        names = {
            "4-7-8": "4-7-8 Relaxing Breath",
            "box_breathing": "Box Breathing (Sama Vritti)",
            "nadi_shodhana": "Alternate Nostril Breathing (Nadi Shodhana)",
            "bhramari": "Bee Breath (Bhramari Pranayama)"
        }
        return names.get(technique, technique)
    
    def _get_breathing_instructions(self, technique: str, pattern: Dict) -> str:
        """Get written instructions for breathing technique"""
        instructions = {
            "4-7-8": "Inhale for 4 counts, hold for 7 counts, exhale for 8 counts. This technique is excellent for relaxation and falling asleep.",
            
            "box_breathing": "Inhale for 4 counts, hold for 4 counts, exhale for 4 counts, hold empty for 4 counts. Creates balance and calm focus.",
            
            "nadi_shodhana": "Using your right thumb and ring finger, alternate blocking nostrils while breathing. Balances the nervous system.",
            
            "bhramari": "Inhale normally, then exhale while making a gentle humming sound like a bee. Calms the mind and reduces stress."
        }
        return instructions.get(technique, "Follow the guided audio for proper technique.")
    
    def _get_pattern_description(self, technique: str, pattern: Dict) -> str:
        """Get pattern description"""
        if technique == "4-7-8":
            return f"Inhale {pattern['inhale']} → Hold {pattern['hold']} → Exhale {pattern['exhale']}"
        elif technique == "box_breathing":
            return f"Inhale {pattern['inhale']} → Hold {pattern['hold']} → Exhale {pattern['exhale']} → Hold {pattern['hold_2']}"
        elif technique == "nadi_shodhana":
            return f"Alternate nostril breathing, {pattern['inhale']} counts in, {pattern['exhale']} counts out"
        elif technique == "bhramari":
            return f"Inhale {pattern['inhale']} → Hold {pattern['hold']} → Exhale with humming {pattern['exhale']}"
        return "Follow audio guidance"
    
    def _generate_breathing_script(self, request: BreathingExerciseRequest, pattern: Dict) -> str:
        """Generate full breathing exercise script"""
        intro = f"""Welcome to {self._get_technique_name(request.technique)} practice. 
        
Find a comfortable seated position with your spine naturally straight. Close your eyes and take a few natural breaths to settle in.
        
We'll practice this technique for {request.duration} minutes. Remember, if you feel dizzy or uncomfortable at any time, return to your natural breathing."""
        
        # Generate practice section based on technique
        if request.technique == "4-7-8":
            practice = """Now we'll begin the 4-7-8 pattern. 
            
Place the tip of your tongue against the ridge behind your upper teeth. Exhale completely through your mouth.
            
Close your mouth and inhale quietly through your nose for 4 counts... 1, 2, 3, 4
            Hold your breath for 7 counts... 1, 2, 3, 4, 5, 6, 7
            Exhale completely through your mouth for 8 counts... 1, 2, 3, 4, 5, 6, 7, 8
            
Continue this pattern..."""
            
        elif request.technique == "box_breathing":
            practice = """Now we'll begin box breathing - equal counts for each phase.
            
Inhale slowly through your nose for 4 counts... 1, 2, 3, 4
            Hold your breath gently for 4 counts... 1, 2, 3, 4
            Exhale slowly through your mouth for 4 counts... 1, 2, 3, 4
            Hold empty for 4 counts... 1, 2, 3, 4
            
Continue this square pattern..."""
            
        elif request.technique == "nadi_shodhana":
            practice = """Now we'll begin alternate nostril breathing.
            
Bring your right hand to your face. Use your thumb to gently close your right nostril, and inhale through your left nostril for 4 counts.
            Close your left nostril with your ring finger, release your thumb, and exhale through your right nostril for 4 counts.
            Inhale through your right nostril for 4 counts.
            Close your right nostril, release your left, exhale through your left nostril for 4 counts.
            
This completes one round. Continue..."""
            
        else:  # bhramari
            practice = """Now we'll begin bee breath - bhramari pranayama.
            
Place your thumbs in your ears and your other fingers gently over your closed eyes.
            Take a normal inhale through your nose.
            As you exhale, make a soft humming sound like a gentle bee... mmmmm
            Continue this pattern, focusing on the vibration of the sound..."""
        
        closing = """As we complete this breathing practice, return to your natural breath.
        
Notice how you feel. Take a moment to appreciate the time you've given yourself for this healing practice.
        
When you're ready, gently open your eyes and carry this sense of calm with you."""
        
        return f"{intro}\n\n{practice}\n\n{closing}"

# Global meditation generator instance
meditation_generator = MeditationGenerator()