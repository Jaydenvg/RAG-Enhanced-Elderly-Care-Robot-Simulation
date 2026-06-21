"""
Intent Classifier for Elderly Care Robot NLI

Classifies patient queries into intent categories:
- ask_medication: Questions about medications
- ask_side_effects: Questions about side effects
- ask_dosage: Questions about dosage/timing
- medication_reminder: Medication taking time
- health_question: General health questions
- request_help: Requests for assistance
- emergency_alert: Emergency situations

Uses keyword matching with confidence scoring.
"""

from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Rule-based intent classifier for medical queries.
    
    Attributes:
        intents (dict): Mapping of intent labels to keyword sets
    """
    
    def __init__(self):
        """Initialize intent classifier with medical keywords."""
        self.intents = {
            'ask_medication': [
                'what is', 'tell me about', 'how does', 'medication',
                'drug', 'medicine', 'tablet', 'pill', 'explain',
                'describe', 'information about'
            ],
            'ask_side_effects': [
                'side effects', 'adverse', 'problems', 'risks',
                'dangers', 'harm', 'negative', 'complications',
                'reaction', 'allergy', 'interactions'
            ],
            'ask_dosage': [
                'how much', 'dosage', 'dose', 'amount', 'mg', 'ml',
                'frequency', 'often', 'times per day', 'take',
                'tablet', 'pill', 'strength'
            ],
            'medication_reminder': [
                'time', 'remind', 'take', 'medication', 'medicine',
                'pill', 'tablet', 'when', 'should i', 'it is time'
            ],
            'health_question': [
                'why', 'how', 'what', 'when', 'where', 'condition',
                'disease', 'symptom', 'problem', 'issue', 'pain',
                'feeling', 'experience'
            ],
            'request_help': [
                'help', 'assist', 'need', 'can you', 'please',
                'could', 'would', 'question', 'ask', 'support'
            ],
            'emergency_alert': [
                'help', 'emergency', 'fall', 'hurt', 'pain',
                'chest', 'difficulty breathing', 'severe', 'urgent',
                'call', 'doctor', 'ambulance', 'danger', 'unable'
            ]
        }
    
    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify the intent of a patient query.
        
        Args:
            query (str): Patient's natural language query
        
        Returns:
            Tuple[str, float]: (intent_label, confidence_score)
                - intent_label: One of the predefined intent categories
                - confidence_score: 0.0-1.0 indicating classifier confidence
        """
        query_lower = query.lower()
        intent_scores = {}
        
        # Calculate score for each intent
        for intent, keywords in self.intents.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            
            if matches > 0:
                score = matches / len(keywords)
                intent_scores[intent] = score
            else:
                intent_scores[intent] = 0.0
        
        # Get best scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        raw_confidence = intent_scores[best_intent]
        
        # Normalize confidence to 0-1 range
        if raw_confidence > 0:
            normalized_confidence = min(raw_confidence / 0.5, 1.0)
        else:
            normalized_confidence = 0.0
        
        logger.debug(
            f"Query: '{query}' -> Intent: {best_intent} "
            f"(confidence: {normalized_confidence:.2f})"
        )
        
        return best_intent, normalized_confidence
    
    def classify_with_scores(self, query: str) -> dict:
        """Classify intent and return ALL intent scores for debugging."""
        query_lower = query.lower()
        intent_scores = {}
        
        for intent, keywords in self.intents.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            score = matches / len(keywords) if keywords else 0
            intent_scores[intent] = score
        
        best_intent = max(intent_scores, key=intent_scores.get)
        raw_confidence = intent_scores[best_intent]
        normalized_confidence = min(raw_confidence / 0.5, 1.0) if raw_confidence > 0 else 0.0
        
        return {
            'best_intent': best_intent,
            'confidence': normalized_confidence,
            'all_scores': intent_scores
        }
