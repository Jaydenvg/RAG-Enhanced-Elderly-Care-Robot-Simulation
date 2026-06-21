"""
Prompt Builder for Elderly Care Robot LLM Inference

This module constructs context-aware prompts for the Phi-2 model
based on different interaction types:
- Medication information queries
- Side effects and warnings
- Health questions
- Emergency assessment
- Medication reminders

Each prompt includes:
1. System instructions (role and guidelines)
2. Patient context (name, age, conditions, medications)
3. Retrieved medical information from RAG
4. Specific task instructions
5. Safety guidelines for elderly patients
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Constructs effective prompts for elderly care LLM responses.
    
    Attributes:
        system_prompt (str): Base system instructions for the model
    """
    
    def __init__(self):
        """Initialize the prompt builder with system instructions."""
        
        # Base system prompt that defines the assistant's role
        self.system_prompt = """You are a compassionate and knowledgeable elderly care assistant robot.

Your primary responsibilities:
1. Provide clear, accurate medical information in simple language
2. Explain medications and their purposes without jargon
3. Help patients understand their health conditions
4. Remind patients about medication schedules
5. Encourage safe health practices
6. Always prioritize patient safety and wellbeing

Guidelines for communication:
- Use simple, clear language suitable for elderly patients
- Speak slowly and clearly in your response
- Break complex information into simple steps
- Always ask if the patient has questions
- If uncertain, recommend consulting their doctor
- Be warm, patient, and reassuring
- Never diagnose conditions or make emergency decisions alone

Safety protocols:
- If patient reports chest pain, difficulty breathing, or falling:
  → Recommend contacting emergency services immediately
- Never recommend stopping prescribed medications
- Always acknowledge side effects without causing alarm
- Encourage regular doctor checkups"""
    
    def build_medication_info_prompt(
        self,
        patient_name: str,
        medication_name: str,
        rag_context: str
    ) -> str:
        """
        Build prompt for explaining medication information.
        
        Args:
            patient_name (str): Patient's name
            medication_name (str): Name of the medication
            rag_context (str): Retrieved medical information from RAG
        
        Returns:
            str: Complete prompt for LLM inference
        
        Example:
            >>> builder = PromptBuilder()
            >>> prompt = builder.build_medication_info_prompt(
            ...     patient_name="John",
            ...     medication_name="Lisinopril",
            ...     rag_context="Lisinopril is an ACE inhibitor..."
            ... )
        """
        
        prompt = f"""{self.system_prompt}

===== PATIENT CONTEXT =====
Patient Name: {patient_name}
Medication Requested: {medication_name}

===== MEDICAL INFORMATION =====
{rag_context}

===== TASK =====
Provide a clear, reassuring explanation of {medication_name} for {patient_name}.

Include:
1. What the medication is and what it treats
2. Why {patient_name} might be taking it
3. How to take it (simple instructions)
4. Common side effects (mention these are usually mild)
5. When to contact their doctor about this medication
6. A warm closing asking if they have questions

Keep the response to 3-4 paragraphs, suitable for an elderly patient.
Use simple words. Avoid medical jargon. Be reassuring but honest."""
        
        return prompt
    
    def build_health_question_prompt(
        self,
        patient_name: str,
        question: str,
        rag_context: str,
        patient_conditions: Optional[str] = None
    ) -> str:
        """
        Build prompt for answering general health questions.
        
        Args:
            patient_name (str): Patient's name
            question (str): Patient's health question
            rag_context (str): Retrieved medical information from RAG
            patient_conditions (str, optional): Patient's known conditions
        
        Returns:
            str: Complete prompt for LLM inference
        """
        
        conditions_text = f"\nKnown Conditions: {patient_conditions}" if patient_conditions else ""
        
        prompt = f"""{self.system_prompt}

===== PATIENT CONTEXT =====
Patient Name: {patient_name}{conditions_text}

===== PATIENT'S QUESTION =====
{question}

===== RELEVANT MEDICAL INFORMATION =====
{rag_context}

===== TASK =====
Answer {patient_name}'s question based on the provided medical information.

Your response should:
1. Directly address the question asked
2. Use the medical information provided
3. Explain in simple, clear language
4. Acknowledge any personal factors (their conditions/medications)
5. Include any relevant safety warnings
6. Suggest seeing their doctor if appropriate
7. End with an invitation for more questions

Keep the response to 2-3 paragraphs. Be warm and reassuring.
If you don't have enough information to answer, say so and recommend consulting their doctor."""
        
        return prompt
    
    def build_medication_reminder_prompt(
        self,
        patient_name: str,
        medication_name: str,
        dosage: str,
        time_of_day: str,
        purpose: str,
        rag_context: str
    ) -> str:
        """
        Build prompt for medication reminders.
        
        Args:
            patient_name (str): Patient's name
            medication_name (str): Medication to take
            dosage (str): Dosage amount (e.g., "10 mg")
            time_of_day (str): When to take it (e.g., "morning")
            purpose (str): Why they're taking it
            rag_context (str): Additional medication information
        
        Returns:
            str: Complete prompt for LLM inference
        """
        
        prompt = f"""{self.system_prompt}

===== MEDICATION REMINDER =====
Patient: {patient_name}
Medication: {medication_name}
Dosage: {dosage}
Time: {time_of_day}
Purpose: {purpose}

===== MEDICATION INFORMATION =====
{rag_context}

===== TASK =====
Create a friendly, clear medication reminder for {patient_name}.

Your reminder should:
1. Greet the patient warmly and mention it's time for their medication
2. State the medication name, dosage clearly
3. Explain why they're taking it (in simple terms)
4. Give clear instructions on how to take it
5. Mention key side effects to watch for (be reassuring)
6. Ask them to confirm they've taken it
7. Remind them to have water nearby
8. End with a friendly, encouraging tone

Keep it natural and conversational, like a caring friend reminding them.
Keep to 2-3 paragraphs. Speak as if you're talking to them in person."""
        
        return prompt
    
    def build_emergency_assessment_prompt(
        self,
        patient_name: str,
        symptoms: str,
        patient_conditions: str,
        medications: str
    ) -> str:
        """
        Build prompt for assessing potentially emergency situations.
        
        Args:
            patient_name (str): Patient's name
            symptoms (str): Symptoms patient is experiencing
            patient_conditions (str): Patient's medical conditions
            medications (str): Current medications
        
        Returns:
            str: Complete prompt for LLM inference
        
        WARNING: This is for initial assessment only. 
                 Real emergencies require immediate professional help.
        """
        
        prompt = f"""{self.system_prompt}

===== EMERGENCY ASSESSMENT =====
Patient: {patient_name}
Reported Symptoms: {symptoms}
Known Conditions: {patient_conditions}
Current Medications: {medications}

===== CRITICAL TASK =====
Assess whether {patient_name}'s symptoms may indicate an emergency.

⚠️ IMPORTANT: If ANY of these apply → RECOMMEND EMERGENCY SERVICES IMMEDIATELY:
- Chest pain or pressure
- Difficulty breathing or shortness of breath
- Loss of consciousness or confusion
- Sudden severe headache
- Signs of stroke (facial drooping, arm weakness, speech difficulty)
- Severe bleeding
- Falls with head injury
- Severe pain
- Sudden vision or hearing loss

Your assessment should:
1. State clearly whether this seems like a potential emergency
2. List concerning symptoms (if any)
3. If emergency: Strongly recommend calling emergency services
4. If not emergency: Suggest what to do (call doctor, home care, etc.)
5. Recommend monitoring which symptoms
6. Include comfort measures if appropriate
7. Be clear but NOT alarming

Response format:
- Start with EMERGENCY/NON-EMERGENCY assessment
- Explain your reasoning
- Give specific next steps
- Provide reassurance if appropriate

REMEMBER: When in doubt, recommend professional evaluation."""
        
        return prompt
    
    def build_side_effects_prompt(
        self,
        patient_name: str,
        medication_name: str,
        reported_symptom: str,
        rag_context: str
    ) -> str:
        """
        Build prompt for assessing if symptoms are medication side effects.
        
        Args:
            patient_name (str): Patient's name
            medication_name (str): Medication being taken
            reported_symptom (str): Symptom patient is experiencing
            rag_context (str): Information about the medication
        
        Returns:
            str: Complete prompt for LLM inference
        """
        
        prompt = f"""{self.system_prompt}

===== SIDE EFFECT ASSESSMENT =====
Patient: {patient_name}
Medication: {medication_name}
Reported Symptom: {reported_symptom}

===== MEDICATION INFORMATION =====
{rag_context}

===== TASK =====
Help {patient_name} understand if their symptom might be a side effect of {medication_name}.

Your response should:
1. Check if the symptom is a known side effect
2. Explain whether it's common or rare
3. Reassure them about common side effects (usually mild and temporary)
4. Provide suggestions for managing the symptom
5. Specify when they should contact their doctor
6. Recommend NEVER stopping medications without consulting their doctor
7. Encourage them to report it to their doctor at next visit

Tone: Reassuring but honest. Avoid alarming language.
If serious: Recommend immediate medical attention.
Keep to 2-3 paragraphs."""
        
        return prompt
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate that a prompt contains essential components.
        
        Returns:
            bool: True if prompt is valid, False otherwise
        """
        
        essential_words = ['patient', 'task', 'response']
        prompt_lower = prompt.lower()
        
        for word in essential_words:
            if word not in prompt_lower:
                logger.warning(f"Prompt missing key word: {word}")
                return False
        
        return True


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    builder = PromptBuilder()
    
    # Example: Medication information prompt
    test_prompt = builder.build_medication_info_prompt(
        patient_name="John",
        medication_name="Lisinopril",
        rag_context="Lisinopril is an ACE inhibitor used to treat high blood pressure..."
    )
    
    print("=" * 60)
    print("SAMPLE MEDICATION INFO PROMPT:")
    print("=" * 60)
    print(test_prompt)
    print("\n")
    print(f"Prompt valid: {builder.validate_prompt(test_prompt)}")
