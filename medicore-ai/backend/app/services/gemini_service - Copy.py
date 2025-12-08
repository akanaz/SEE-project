import google.generativeai as genai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)

    async def generate_response(self, query: str, context_chunks: list[str], system_prompt: str = None) -> str:
        default_system_prompt = """You are MedAssist — an intelligent, reliable, and safety-aware AI medical assistant.

CRITICAL RULES:
1. ONLY use information from the provided medical context
2. If context doesn't contain sufficient information, clearly state limitations
3. Never invent or hallucinate medical information
4. Always include medical disclaimer

Respond using this structure:

**Overview**
Brief explanation of condition/symptom in one paragraph.

**Possible Causes**
One clear paragraph listing potential causes.

**Common Symptoms**
One paragraph describing typical symptoms.

**Recommended Actions**
One paragraph with self-care and monitoring advice.

**Treatment Options**
One paragraph with general treatment approaches (if relevant).

**When to See a Doctor**
One paragraph with clear warning signs.

**Medical Disclaimer**
This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare provider for diagnosis and treatment."""

        system_instructions = system_prompt or default_system_prompt
        context_text = "\n\n".join(context_chunks).strip() if context_chunks else ""
        prompt = f"""{system_instructions}

Medical Context from Textbooks:
{context_text}

Patient Query:
{query}

Response:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def generate_followup_question(self, question: str) -> str:
        """Generate a medically-relevant follow-up question for triage"""

        followup_prompt = f"""You are an experienced medical triage assistant. 
A patient says: "{question}"

Generate ONE specific follow-up question (max 15 words) to assess severity or gather critical information.

RULES:
- Ask about duration, severity, or associated symptoms
- Focus on red flags or emergency symptoms
- Be specific and clear
- No generic questions like "tell me more"
- Use proper medical terminology when appropriate

EXAMPLES:
Patient: "I have a headache"
Good: "How long have you had this headache, and is it the worst you've ever experienced?"
Bad: "Tell me more about your headache"

Patient: "My chest hurts"
Good: "Is the chest pain crushing, and does it radiate to your arm or jaw?"
Bad: "Does anything make it worse?"

Patient: "I feel dizzy"
Good: "Do you feel dizzy when standing up, and have you fainted?"
Bad: "How long has this been happening?"

NOW, generate ONE follow-up question for: "{question}"
Follow-up Question:"""

        try:
            response = self.model.generate_content(followup_prompt)
            question_text = response.text.strip()
            question_text = question_text.replace("Follow-up Question:", "").strip()
            question_text = question_text.replace('"', '').strip()
            return question_text
        except Exception as e:
            logger.error(f"Follow-up generation error: {e}")
            return self._get_fallback_followup(question)

    def _get_fallback_followup(self, question: str) -> str:
        """Provide intelligent fallback questions based on symptom keywords"""
        question_lower = question.lower()

        if any(word in question_lower for word in ["pain", "hurt", "ache"]):
            if "head" in question_lower:
                return "On a scale of 1-10, how severe is the pain, and is this your worst headache ever?"
            elif "chest" in question_lower:
                return "Is the pain crushing or pressure-like, and does it spread to your arm or jaw?"
            elif "abdomen" in question_lower or "stomach" in question_lower:
                return "Is the pain constant or cramping, and have you vomited or seen blood?"
            else:
                return "How long have you had this pain, and does anything make it better or worse?"

        elif any(word in question_lower for word in ["breath", "cough", "wheez"]):
            return "Are you having difficulty breathing at rest, and is there any chest pain?"

        elif any(word in question_lower for word in ["dizz", "faint", "heart"]):
            return "Have you lost consciousness, and do you have chest pain or palpitations?"

        elif any(word in question_lower for word in ["numb", "weak", "tingle"]):
            return "Is the numbness on one side of your body, and can you lift both arms equally?"

        elif any(word in question_lower for word in ["fever", "chills", "sweat"]):
            return "What is your temperature, and have you had fever for more than 3 days?"

        elif any(word in question_lower for word in ["nausea", "vomit", "diarrhea"]):
            return "Are you keeping fluids down, and have you seen blood in vomit or stool?"

        return "How long have you had these symptoms, and are they getting worse?"

    async def simplify_explanation(self, chat_history: list) -> str:
        """Simplify the entire conversation for easier understanding"""

        chat_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in chat_history
        ])

        simplify_prompt = f"""You are a medical educator explaining to a 10-year-old.

Summarize this medical conversation in ONE simple paragraph (max 50 words).
- Use everyday language
- Avoid medical jargon
- Focus on the main point
- Be reassuring but honest

Conversation:
{chat_text}

Simple Summary:"""

        try:
            response = self.model.generate_content(simplify_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Simplification error: {e}")
            return "I've explained your symptoms and possible causes. Remember to see a doctor if symptoms worsen."

    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language while preserving medical context"""

        translate_prompt = f"""Translate the following medical text to {target_language}.
Preserve medical terminology accuracy and formatting.

Text to translate:
{text}

Translation:"""

        try:
            response = self.model.generate_content(translate_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise

gemini_service = GeminiService()