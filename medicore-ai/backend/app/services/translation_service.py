import os
import logging
import asyncio
from typing import Dict

from groq import Groq

logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

LANGUAGE_MAP: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "mr": "Marathi (मराठी)",
    "bn": "Bengali (বাংলা)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "zh": "Chinese (中文)",
    "ar": "Arabic (العربية)",
}


async def translate_text(text: str, language_code: str) -> str:
    """
    Translate medical text using Groq API.
    - Keeps medical meaning and warnings accurate.
    - Preserves basic formatting like **bold**.
    """
    if not text:
        return text

    # If English, just return original
    if language_code == "en":
        return text

    language_name = LANGUAGE_MAP.get(language_code, "English")

    prompt = f"""Translate the following medical text to {language_name}.

Keep medical terms accurate and understandable.
Maintain formatting like **bold** text.
Preserve all medical warnings and disclaimers.

Text to translate:
{text}

Provide ONLY the translated text, nothing else.
"""

    try:
        logger.info(f"Translating to {language_name}")

        # Run blocking Groq call in a thread so we don't block the event loop
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional medical translator. Maintain accuracy and clarity."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        translated_text = response.choices[0].message.content.strip()
        logger.info(f"Translation successful for {language_name}")
        return translated_text

    except Exception as e:
        logger.error(f"Translation error for {language_name}: {e}")
        # Fallback: return original text so frontend still shows something
        return text
