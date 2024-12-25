from typing import Dict, List, Set
import json
import os

class SkillsProcessor:
    def __init__(self):
        self.skills_categories = self._load_skills_data()
        
    def _load_skills_data(self) -> Dict[str, Set[str]]:
        skills_file = os.path.join(os.path.dirname(__file__), 'data', 'skills.json')
        with open(skills_file, 'r') as f:
            return {k: set(v) for k, v in json.load(f).items()}
            
    def categorize_skills(self, text: str) -> Dict[str, List[str]]:
        found_skills = {
            'technical': [],
            'soft': [],
            'languages': [],
            'tools': []
        }
        
        words = set(text.lower().split())
        for category, skills in self.skills_categories.items():
            matches = words.intersection(skills)
            if matches:
                found_skills[category].extend(matches)
                
        return found_skills
        
    def detect_proficiency(self, skill_text: str) -> float:
        proficiency_indicators = {
            'expert': 1.0,
            'advanced': 0.8,
            'intermediate': 0.6,
            'basic': 0.4,
            'familiar': 0.3
        }
        
        for indicator, level in proficiency_indicators.items():
            if indicator in skill_text.lower():
                return level
        return 0.5  # default proficiency 