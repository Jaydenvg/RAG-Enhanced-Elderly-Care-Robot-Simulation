"""
Entity Extractor for Elderly Care Robot NLI

Extracts medical named entities from patient queries:
- Medication names (lisinopril, metformin, ibuprofen, etc.)
- Medical conditions (hypertension, diabetes, arthritis, etc.)
- Dosages (10 mg, 500 ml, etc.)
- Times (morning, evening, bedtime, etc.)
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract medical entities from patient queries."""
    
    def __init__(self):
        """Initialize entity extractor with medical entity lists."""
        # Common medication names
        self.medications = [
            'lisinopril', 'enalapril', 'ramipril',
            'metformin', 'glipizide',
            'amlodipine', 'nifedipine',
            'metoprolol', 'atenolol',
            'ibuprofen', 'naproxen',
            'acetaminophen', 'paracetamol',
            'aspirin',
            'donepezil', 'rivastigmine', 'memantine',
            'insulin', 'glyburide',
            'calcium', 'vitamin d',
            'bisphosphonate',
            'sertraline', 'fluoxetine',
        ]
        
        # Common medical conditions
        self.conditions = [
            'hypertension', 'high blood pressure', 'bp',
            'diabetes', 'diabetes mellitus', 'type 2 diabetes',
            'arthritis', 'osteoarthritis', 'rheumatoid arthritis',
            'dementia', 'alzheimer',
            'heart disease', 'cardiac', 'heart attack',
            'osteoporosis', 'weak bones',
            'copd', 'emphysema', 'chronic obstructive',
            'depression', 'anxiety',
            'asthma',
            'thyroid',
            'kidney disease',
            'liver disease'
        ]
        
        # Times of day
        self.times = [
            'morning', 'breakfast', 'early morning',
            'afternoon', 'lunch', 'midday', 'noon',
            'evening', 'dinner', 'supper',
            'night', 'bedtime', 'before bed', 'at night',
            'after meals', 'with meals', 'between meals'
        ]
        
        # Dosage pattern: captures number + unit
        self.dosage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(mg|g|ml|l|mcg|units|tablets?|pills?|capsules?)')
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text."""
        text_lower = text.lower()
        
        entities = {
            'medications': [],
            'conditions': [],
            'dosages': [],
            'times': []
        }
        
        # Extract medications
        for med in self.medications:
            if med in text_lower and med not in entities['medications']:
                entities['medications'].append(med)
        
        # Extract conditions
        for condition in self.conditions:
            if condition in text_lower and condition not in entities['conditions']:
                entities['conditions'].append(condition)
        
        # Extract dosages using regex
        dosage_matches = self.dosage_pattern.findall(text_lower)
        for match in dosage_matches:
            amount, unit = match
            dosage_str = f"{amount} {unit}"
            if dosage_str not in entities['dosages']:
                entities['dosages'].append(dosage_str)
        
        # Extract times
        for time in self.times:
            if time in text_lower and time not in entities['times']:
                entities['times'].append(time)
        
        logger.debug(f"Extracted entities from '{text}': {entities}")
        
        return entities
    
    def extract_medications(self, text: str) -> List[str]:
        """Extract only medication names."""
        text_lower = text.lower()
        found_meds = []
        for med in self.medications:
            if med in text_lower and med not in found_meds:
                found_meds.append(med)
        return found_meds
    
    def extract_conditions(self, text: str) -> List[str]:
        """Extract only medical conditions."""
        text_lower = text.lower()
        found_conditions = []
        for condition in self.conditions:
            if condition in text_lower and condition not in found_conditions:
                found_conditions.append(condition)
        return found_conditions
    
    def extract_dosages(self, text: str) -> List[str]:
        """Extract only dosages."""
        text_lower = text.lower()
        dosage_matches = self.dosage_pattern.findall(text_lower)
        dosages = []
        for match in dosage_matches:
            amount, unit = match
            dosage_str = f"{amount} {unit}"
            if dosage_str not in dosages:
                dosages.append(dosage_str)
        return dosages
    
    def add_medication(self, medication_name: str) -> None:
        """Add a new medication to the recognized list."""
        med_lower = medication_name.lower()
        if med_lower not in self.medications:
            self.medications.append(med_lower)
            logger.info(f"Added medication: {med_lower}")
    
    def add_condition(self, condition_name: str) -> None:
        """Add a new condition to the recognized list."""
        cond_lower = condition_name.lower()
        if cond_lower not in self.conditions:
            self.conditions.append(cond_lower)
            logger.info(f"Added condition: {cond_lower}")
