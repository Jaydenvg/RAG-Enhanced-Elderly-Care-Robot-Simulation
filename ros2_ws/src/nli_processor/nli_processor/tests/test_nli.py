"""
Comprehensive tests for NLI components (Intent Classifier and Entity Extractor)
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import nli_processor modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from intent_classifier import IntentClassifier
from entity_extractor import EntityExtractor


class TestIntentClassifier:
    """Test suite for IntentClassifier"""
    
    @pytest.fixture
    def classifier(self):
        """Fixture: Create a fresh classifier instance for each test"""
        return IntentClassifier()
    
    # Medication Intent Tests
    def test_medication_inquiry(self, classifier):
        """Test: Recognize medication inquiry"""
        query = "What is Lisinopril?"
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_medication'
        assert confidence > 0.5
    
    def test_medication_explanation(self, classifier):
        """Test: Recognize medication explanation request"""
        query = "Tell me about metformin"
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_medication'
        assert confidence > 0.5
    
    # Side Effects Intent Tests
    def test_side_effects_inquiry(self, classifier):
        """Test: Recognize side effects question"""
        query = "What are the side effects of this drug?"
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_side_effects'
        assert confidence > 0.5
    
    def test_adverse_effects_inquiry(self, classifier):
        """Test: Recognize adverse effects question"""
        query = "What are the adverse reactions?"
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_side_effects'
    
    # Dosage Intent Tests
    def test_dosage_question(self, classifier):
        """Test: Recognize dosage question"""
        query = "How much should I take?"
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_dosage'
    
    def test_frequency_question(self, classifier):
        """Test: Recognize frequency question"""
        query = "How often should I take my medication?"
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_dosage'
    
    # Medication Reminder Intent Tests
    def test_medication_reminder(self, classifier):
        """Test: Recognize medication reminder"""
        query = "It's time to take my medication"
        intent, confidence = classifier.classify(query)
        assert intent == 'medication_reminder'
    
    def test_take_medication_reminder(self, classifier):
        """Test: Recognize take medication reminder"""
        query = "I need to take my pills in the morning"
        intent, confidence = classifier.classify(query)
        assert intent == 'medication_reminder'
    
    # Health Question Tests
    def test_health_question(self, classifier):
        """Test: Recognize general health question"""
        query = "Why do I have high blood pressure?"
        intent, confidence = classifier.classify(query)
        assert intent == 'health_question'
    
    def test_symptom_question(self, classifier):
        """Test: Recognize symptom question"""
        query = "What are symptoms of diabetes?"
        intent, confidence = classifier.classify(query)
        assert intent == 'health_question'
    
    # Help Request Tests
    def test_help_request(self, classifier):
        """Test: Recognize help request"""
        query = "Can you help me?"
        intent, confidence = classifier.classify(query)
        assert intent == 'request_help'
    
    def test_assistance_request(self, classifier):
        """Test: Recognize assistance request"""
        query = "I need assistance with my medication"
        intent, confidence = classifier.classify(query)
        assert intent in ['request_help', 'medication_reminder']
    
    # Emergency Alert Tests
    def test_emergency_alert(self, classifier):
        """Test: Recognize emergency alert"""
        query = "I fell and can't get up!"
        intent, confidence = classifier.classify(query)
        assert intent == 'emergency_alert'
    
    def test_chest_pain_alert(self, classifier):
        """Test: Recognize chest pain emergency"""
        query = "I have severe chest pain"
        intent, confidence = classifier.classify(query)
        assert intent == 'emergency_alert'
    
    # Confidence Scoring Tests
    def test_confidence_score_range(self, classifier):
        """Test: Confidence score is always in 0-1 range"""
        queries = [
            "What is medicine?",
            "Help me",
            "Tell me about medication",
            "Emergency!"
        ]
        for query in queries:
            intent, confidence = classifier.classify(query)
            assert 0.0 <= confidence <= 1.0, f"Confidence out of range: {confidence}"
    
    def test_confidence_increases_with_matches(self, classifier):
        """Test: Confidence increases with more keyword matches"""
        query_weak = "Tell"  # Single keyword
        query_strong = "Tell me about medication side effects and interactions"  # Multiple keywords
        
        intent1, conf1 = classifier.classify(query_weak)
        intent2, conf2 = classifier.classify(query_strong)
        
        # Stronger query should have higher or equal confidence
        assert conf2 >= conf1
    
    # Debug Scores Test
    def test_classify_with_all_scores(self, classifier):
        """Test: Get all intent scores for debugging"""
        query = "What are the side effects of lisinopril?"
        result = classifier.classify_with_scores(query)
        
        assert 'best_intent' in result
        assert 'confidence' in result
        assert 'all_scores' in result
        assert result['best_intent'] == 'ask_side_effects'
        assert isinstance(result['all_scores'], dict)
        assert len(result['all_scores']) == 7  # 7 intent categories


class TestEntityExtractor:
    """Test suite for EntityExtractor"""
    
    @pytest.fixture
    def extractor(self):
        """Fixture: Create a fresh extractor instance for each test"""
        return EntityExtractor()
    
    # Medication Extraction Tests
    def test_extract_lisinopril(self, extractor):
        """Test: Extract lisinopril from query"""
        text = "I take lisinopril for high blood pressure"
        entities = extractor.extract_entities(text)
        assert 'lisinopril' in entities['medications']
    
    def test_extract_multiple_medications(self, extractor):
        """Test: Extract multiple medications"""
        text = "I take lisinopril, metformin, and aspirin daily"
        entities = extractor.extract_entities(text)
        assert 'lisinopril' in entities['medications']
        assert 'metformin' in entities['medications']
        assert 'aspirin' in entities['medications']
    
    def test_extract_no_medications(self, extractor):
        """Test: Return empty list when no medications found"""
        text = "How are you feeling today?"
        entities = extractor.extract_entities(text)
        assert len(entities['medications']) == 0
    
    # Condition Extraction Tests
    def test_extract_hypertension(self, extractor):
        """Test: Extract hypertension condition"""
        text = "I have hypertension"
        entities = extractor.extract_entities(text)
        assert 'hypertension' in entities['conditions']
    
    def test_extract_multiple_conditions(self, extractor):
        """Test: Extract multiple conditions"""
        text = "I have diabetes, arthritis, and dementia"
        entities = extractor.extract_entities(text)
        assert 'diabetes' in entities['conditions']
        assert 'arthritis' in entities['conditions']
        assert 'dementia' in entities['conditions']
    
    def test_extract_no_conditions(self, extractor):
        """Test: Return empty list when no conditions found"""
        text = "What is the weather?"
        entities = extractor.extract_entities(text)
        assert len(entities['conditions']) == 0
    
    # Dosage Extraction Tests
    def test_extract_dosage_mg(self, extractor):
        """Test: Extract dosage with mg unit"""
        text = "I take 10 mg of lisinopril"
        entities = extractor.extract_entities(text)
        assert '10 mg' in entities['dosages']
    
    def test_extract_dosage_ml(self, extractor):
        """Test: Extract dosage with ml unit"""
        text = "Take 5 ml three times a day"
        entities = extractor.extract_entities(text)
        assert '5 ml' in entities['dosages']
    
    def test_extract_dosage_decimal(self, extractor):
        """Test: Extract decimal dosages"""
        text = "0.5 mg twice daily"
        entities = extractor.extract_entities(text)
        assert '0.5 mg' in entities['dosages']
    
    def test_extract_dosage_units(self, extractor):
        """Test: Extract dosage with units"""
        text = "100 units of insulin"
        entities = extractor.extract_entities(text)
        assert '100 units' in entities['dosages']
    
    def test_extract_multiple_dosages(self, extractor):
        """Test: Extract multiple dosages"""
        text = "Take 10 mg in the morning and 500 ml in the evening"
        entities = extractor.extract_entities(text)
        assert '10 mg' in entities['dosages']
        assert '500 ml' in entities['dosages']
    
    def test_extract_no_dosages(self, extractor):
        """Test: Return empty list when no dosages found"""
        text = "When should I take my medication?"
        entities = extractor.extract_entities(text)
        assert len(entities['dosages']) == 0
    
    # Time Extraction Tests
    def test_extract_morning(self, extractor):
        """Test: Extract morning time"""
        text = "Take it in the morning"
        entities = extractor.extract_entities(text)
        assert 'morning' in entities['times']
    
    def test_extract_evening(self, extractor):
        """Test: Extract evening time"""
        text = "Take evening dose after dinner"
        entities = extractor.extract_entities(text)
        assert 'evening' in entities['times']
    
    def test_extract_bedtime(self, extractor):
        """Test: Extract bedtime"""
        text = "Take before bedtime"
        entities = extractor.extract_entities(text)
        assert 'bedtime' in entities['times']
    
    def test_extract_multiple_times(self, extractor):
        """Test: Extract multiple time references"""
        text = "Morning, afternoon, and evening doses"
        entities = extractor.extract_entities(text)
        assert 'morning' in entities['times']
        assert 'afternoon' in entities['times']
        assert 'evening' in entities['times']
    
    def test_extract_no_times(self, extractor):
        """Test: Return empty list when no times found"""
        text = "Tell me about the medication"
        entities = extractor.extract_entities(text)
        assert len(entities['times']) == 0
    
    # Comprehensive Entity Tests
    def test_extract_all_entities(self, extractor):
        """Test: Extract all entity types from complex query"""
        text = "I need to take 10 mg of lisinopril for hypertension in the morning"
        entities = extractor.extract_entities(text)
        
        assert 'lisinopril' in entities['medications']
        assert 'hypertension' in entities['conditions']
        assert '10 mg' in entities['dosages']
        assert 'morning' in entities['times']
    
    def test_extract_no_duplicates(self, extractor):
        """Test: No duplicate entities are extracted"""
        text = "I take lisinopril, lisinopril, and lisinopril daily in the morning"
        entities = extractor.extract_entities(text)
        
        med_count = entities['medications'].count('lisinopril')
        time_count = entities['times'].count('morning')
        
        assert med_count == 1, "Should not have duplicate medications"
        assert time_count == 1, "Should not have duplicate times"
    
    # Individual Extraction Methods
    def test_extract_medications_method(self, extractor):
        """Test: extract_medications method"""
        text = "I take lisinopril and metformin"
        meds = extractor.extract_medications(text)
        assert 'lisinopril' in meds
        assert 'metformin' in meds
    
    def test_extract_conditions_method(self, extractor):
        """Test: extract_conditions method"""
        text = "I have diabetes and hypertension"
        conditions = extractor.extract_conditions(text)
        assert 'diabetes' in conditions
        assert 'hypertension' in conditions
    
    def test_extract_dosages_method(self, extractor):
        """Test: extract_dosages method"""
        text = "10 mg twice and 500 ml once"
        dosages = extractor.extract_dosages(text)
        assert '10 mg' in dosages
        assert '500 ml' in dosages
    
    # Dynamic Addition Tests
    def test_add_medication(self, extractor):
        """Test: Add custom medication to entity list"""
        custom_med = "myzolid"
        extractor.add_medication(custom_med)
        
        text = "I take myzolid"
        meds = extractor.extract_medications(text)
        assert custom_med in meds
    
    def test_add_condition(self, extractor):
        """Test: Add custom condition to entity list"""
        custom_condition = "parkinson"
        extractor.add_condition(custom_condition)
        
        text = "I have parkinson"
        conditions = extractor.extract_conditions(text)
        assert custom_condition in conditions


class TestIntegration:
    """Integration tests combining Intent Classifier and Entity Extractor"""
    
    @pytest.fixture
    def nli_components(self):
        """Fixture: Create both classifier and extractor"""
        return {
            'classifier': IntentClassifier(),
            'extractor': EntityExtractor()
        }
    
    def test_medication_reminder_flow(self, nli_components):
        """Test: Complete medication reminder processing"""
        query = "I need to take 10 mg of lisinopril in the morning"
        
        classifier = nli_components['classifier']
        extractor = nli_components['extractor']
        
        # Classify intent
        intent, confidence = classifier.classify(query)
        assert intent == 'medication_reminder'
        
        # Extract entities
        entities = extractor.extract_entities(query)
        assert 'lisinopril' in entities['medications']
        assert '10 mg' in entities['dosages']
        assert 'morning' in entities['times']
    
    def test_medication_inquiry_flow(self, nli_components):
        """Test: Complete medication inquiry processing"""
        query = "What are the side effects of metformin for diabetes?"
        
        classifier = nli_components['classifier']
        extractor = nli_components['extractor']
        
        intent, confidence = classifier.classify(query)
        assert intent == 'ask_side_effects'
        
        entities = extractor.extract_entities(query)
        assert 'metformin' in entities['medications']
        assert 'diabetes' in entities['conditions']
    
    def test_emergency_alert_flow(self, nli_components):
        """Test: Complete emergency alert processing"""
        query = "I fell down and I can't move!"
        
        classifier = nli_components['classifier']
        extractor = nli_components['extractor']
        
        intent, confidence = classifier.classify(query)
        assert intent == 'emergency_alert'
        
        # Should not extract specific medications for generic emergency
        entities = extractor.extract_entities(query)
        assert len(entities['medications']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
