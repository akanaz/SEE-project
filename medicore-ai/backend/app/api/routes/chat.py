from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from app.services.vectorstore import vectorstore_service
from app.services.gemini_service import gemini_service
from app.services.translation_service import translate_text
from gtts import gTTS
import uuid
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Storage for generated MP3 files
AUDIO_DIR = "tts_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# ------------------ MODELS ------------------------

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: list[ChatMessage] = []
    awaiting_followup: bool = False

class ChatResponse(BaseModel):
    response: str
    awaiting_followup: bool
    body_marker: str | None = None
    context_sources: list[str] | None = None

class SimplifyRequest(BaseModel):
    chat_history: list[ChatMessage]

class TranslateRequest(BaseModel):
    text: str
    language: str

class TranslateResponse(BaseModel):
    success: bool
    translated: str | None
    language: str


# ------------------ CHAT ENDPOINT ------------------------

@router.post("/message", response_model=ChatResponse)
async def send_message(req: ChatRequest):

    try:
        logger.info(f"Incoming message: {req.message[:60]}")

        # FIRST TURN → Ask follow-up question
        if not req.awaiting_followup:
            followup = await gemini_service.generate_followup_question(req.message)
            return ChatResponse(
                response=f"**Follow-up Question:** {followup}",
                awaiting_followup=True
            )

        # SECOND TURN → Perform RAG search
        original_query = (
            req.chat_history[-2].content
            if len(req.chat_history) >= 2
            else req.message
        )

        context_chunks = await vectorstore_service.similarity_search(
            original_query, k=5
        )

        llm_response = await gemini_service.generate_response(
            query=original_query,
            context_chunks=context_chunks
        )

        return ChatResponse(
            response=llm_response,
            awaiting_followup=False,
            context_sources=context_chunks[:3]
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------ TRANSLATION ------------------------

@router.post("/translate", response_model=TranslateResponse)
async def translate_endpoint(req: TranslateRequest):
    try:
        translated = (
            req.text if req.language == "en"
            else await translate_text(req.text, req.language)
        )

        return TranslateResponse(
            success=True,
            translated=translated,
            language=req.language
        )

    except Exception as e:
        logger.error(f"Translation error: {e}")
        return TranslateResponse(success=False, translated=None, language=req.language)


# ------------------ SIMPLIFICATION ------------------------

@router.post("/simplify")
async def simplify_conversation(req: SimplifyRequest):
    try:
        simplified = await gemini_service.simplify_explanation(
            [msg.dict() for msg in req.chat_history]
        )
        return {"simplified": simplified}

    except Exception as e:
        logger.error(f"Simplify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------ TTS (gTTS) ------------------------

@router.post("/speak")
async def speak_text(payload: dict):
    text = payload.get("text", "")
    lang = payload.get("lang", "en")

    if not text.strip():
        return {"success": False, "error": "Empty text"}

    try:
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)

        return {
            "success": True,
            "url": f"/chat/audio/{filename}"
        }

    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = os.path.join(AUDIO_DIR, filename)
    return FileResponse(filepath, media_type="audio/mpeg")
