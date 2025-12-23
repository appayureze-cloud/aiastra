"""
Buddy Matching Service
Implements AI-powered buddy matching algorithm
"""

import logging
from typing import List, Dict, Any
import math

logger = logging.getLogger(__name__)

class BuddyMatchingService:
    """AI-powered buddy matching algorithm"""
    
    def calculate_match_score(
        self,
        profile1: Dict[str, Any],
        profile2: Dict[str, Any]
    ) -> float:
        """
        Calculate compatibility score between two profiles
        Returns score between 0.0 and 1.0
        """
        score = 0.0
        weights = {
            "health_goals": 0.35,
            "personality": 0.20,
            "age_range": 0.15,
            "interests": 0.15,
            "language": 0.10,
            "timezone": 0.05
        }
        
        # Health goals compatibility (most important)
        goals1 = set(profile1.get('health_goals', []))
        goals2 = set(profile2.get('health_goals', []))
        
        if goals1 and goals2:
            common_goals = len(goals1.intersection(goals2))
            total_goals = len(goals1.union(goals2))
            goals_score = common_goals / total_goals if total_goals > 0 else 0
            score += goals_score * weights['health_goals']
        
        # Personality compatibility
        personality_map = {
            'introvert': ['introvert', 'ambivert'],
            'extrovert': ['extrovert', 'ambivert'],
            'ambivert': ['introvert', 'extrovert', 'ambivert']
        }
        
        p1_type = profile1.get('personality_type', '').lower()
        p2_type = profile2.get('personality_type', '').lower()
        
        if p1_type and p2_type:
            if p2_type in personality_map.get(p1_type, []):
                score += weights['personality']
        
        # Age range compatibility
        age1 = profile1.get('age_range', '')
        age2 = profile2.get('age_range', '')
        
        if age1 and age2:
            if self._age_ranges_overlap(age1, age2):
                score += weights['age_range']
        
        # Interests compatibility
        interests1 = set(profile1.get('interests', []))
        interests2 = set(profile2.get('interests', []))
        
        if interests1 and interests2:
            common_interests = len(interests1.intersection(interests2))
            if common_interests > 0:
                interests_score = min(common_interests / 3, 1.0)  # Cap at 3 common interests
                score += interests_score * weights['interests']
        
        # Language compatibility
        if profile1.get('preferred_language') == profile2.get('preferred_language'):
            score += weights['language']
        
        # Timezone compatibility (within 2 hours)
        tz1 = profile1.get('timezone', 'Asia/Kolkata')
        tz2 = profile2.get('timezone', 'Asia/Kolkata')
        
        if self._timezones_compatible(tz1, tz2):
            score += weights['timezone']
        
        return round(score, 2)
    
    def _age_ranges_overlap(self, range1: str, range2: str) -> bool:
        """Check if age ranges overlap"""
        range_map = {
            '18-25': (18, 25),
            '26-35': (26, 35),
            '36-45': (36, 45),
            '46-60': (46, 60),
            '60+': (60, 100)
        }
        
        r1 = range_map.get(range1)
        r2 = range_map.get(range2)
        
        if not r1 or not r2:
            return False
        
        return r1[0] <= r2[1] and r2[0] <= r1[1]
    
    def _timezones_compatible(self, tz1: str, tz2: str) -> bool:
        """Check if timezones are compatible (within 2 hours)"""
        # Simplified - assume compatible if same or common Indian timezones
        india_timezones = ['Asia/Kolkata', 'Asia/Calcutta', 'IST']
        
        if tz1 in india_timezones and tz2 in india_timezones:
            return True
        
        return tz1 == tz2
    
    async def find_matches(
        self,
        user_profile: Dict[str, Any],
        candidate_profiles: List[Dict[str, Any]],
        min_score: float = 0.5,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find best matching buddies for a user
        """
        matches = []
        
        for candidate in candidate_profiles:
            # Don't match with self
            if candidate.get('user_id') == user_profile.get('user_id'):
                continue
            
            score = self.calculate_match_score(user_profile, candidate)
            
            if score >= min_score:
                matches.append({
                    'profile': candidate,
                    'match_score': score
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Return top matches
        return matches[:limit]

# Global instance
matching_service = BuddyMatchingService()
