import os
import logging
import asyncio
from typing import List, Optional

from dotenv import load_dotenv
from groq import Groq

logger = logging.getLogger(__name__)

# Load .env whenever this module is imported
load_dotenv()


class GeminiService:
    """
    LLM wrapper for MedAssist, backed by Groq (LLaMA 3.1 8B).
    """

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set or empty")

        # Pass the key explicitly
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"  # Fast and accurate

    # ---------- internal helper for async-safe Groq calls ----------

    async def _chat_completion(self, **kwargs):
        """
        Run Groq chat completion in a thread so it doesn't block the event loop.
        """

        def _call():
            return self.client.chat.completions.create(**kwargs)

        return await asyncio.to_thread(_call)

    # ---------- main response generation ----------

    async def generate_response(
        self,
        query: str,
        context_chunks: List[str],
        system_prompt: Optional[str] = None,
    ) -> str:

        default_system_prompt = """
You are MedAssist -- an AI medical assistant for educational purposes.

CRITICAL RULES:
1. ONLY use information from the provided medical context
2. If context does not have enough info, clearly state "I don't have sufficient information about this"
3. Never invent or make up medical information
4. Always include medical disclaimer

Format your response:
**Overview** - Brief explanation in 1 paragraph
**Possible Causes** - List potential causes
**Common Symptoms** - Describe typical symptoms
**Recommended Actions** - Self-care and monitoring advice
**When to See a Doctor** - Warning signs requiring immediate attention
**Medical Disclaimer** - This is educational only. Always consult a healthcare provider.
""".strip()

        system_instructions = (system_prompt or default_system_prompt).strip()
        context_text = (
            "\n\n".join(context_chunks).strip()
            if context_chunks
            else "No specific medical context available"
        )

        try:
            logger.info("Calling Groq API for main response")
            completion = await self._chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {
                        "role": "user",
                        "content": (
                            f"Medical Context:\n{context_text}\n\n"
                            f"Patient Query: {query}"
                        ),
                    },
                ],
                temperature=0.7,
                max_tokens=1024,
            )

            return (completion.choices[0].message.content or "").strip()

        except Exception as e:
            logger.error(f"Groq error in generate_response: {e}", exc_info=True)
            raise

    # ---------- follow-up question generation ----------

    async def generate_followup_question(self, question: str) -> str:
        """
        Generate ONE high-quality clinical follow-up question.
        """

        try:
            prompt = (
                "You are a careful medical triage assistant.\n\n"
                f"The patient said: \"{question}\"\n\n"
                "Your task: Ask exactly ONE concise follow-up question that would help a doctor "
                "better understand the situation.\n\n"
                "Rules:\n"
                "- Focus on one clinically important missing detail (duration, severity, location, associated symptoms).\n"
                "- Maximum 20 words.\n"
                "- Do NOT ask multiple questions.\n"
                "- No lists, no bullet points.\n"
                "- Output only the question."
            )

            completion = await self._chat_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You generate a single, precise medical follow-up question to clarify "
                            "patient symptoms for safe triage."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=64,
            )

            followup = (completion.choices[0].message.content or "").strip()
            followup = followup.split("\n")[0].strip()

            if len(followup) > 120:
                followup = followup[:117].rstrip() + "..."

            return followup or "How long have you been experiencing this symptom?"

        except Exception as e:
            logger.error(f"Follow-up error: {e}", exc_info=True)
            return "How long have you been experiencing this symptom?"

    # ---------- simplification ----------

    async def simplify_explanation(self, chat_history: list) -> str:
        try:
            chat_text = "\n".join(
                f"{msg.get('role','unknown')}: {str(msg.get('content',''))[:80]}"
                for msg in chat_history[-3:]
            )

            completion = await self._chat_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Simplify medical information in ONE short paragraph using very easy language."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Conversation:\n{chat_text}\n\nSimplify:",
                    },
                ],
                temperature=0.7,
                max_tokens=150,
            )

            return (completion.choices[0].message.content or "").strip()

        except Exception as e:
            logger.error(f"Simplification error: {e}", exc_info=True)
            return "Unable to simplify."

    # ---------- translation ----------

    async def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text safely while keeping medical meaning.
        """
        try:
            prompt = (
                f"Translate the following medical explanation into {target_language}. "
                "Keep meaning and warnings accurate. Return only the translation.\n\n"
                f"Text:\n{text}"
            )

            completion = await self._chat_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise medical translator. Maintain medical accuracy."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=512,
            )

            return (completion.choices[0].message.content or "").strip()

        except Exception as e:
            logger.error(f"Translation error: {e}", exc_info=True)
            return text  # fallback


gemini_service = GeminiService()
