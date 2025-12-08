from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)

    # Define real field names (snake_case)
    chat_history: List[ChatMessage] = Field(default_factory=list, alias="chatHistory")
    awaiting_followup: bool = Field(default=False, alias="awaitingFollowup")

    class Config:
        populate_by_name = True   # Allows backend to accept both names
        allow_population_by_field_name = True


class ChatResponse(BaseModel):
    response: str
    awaiting_followup: bool
    body_marker: Optional[dict] = None
    context_sources: Optional[List[str]] = None


class SimplifyRequest(BaseModel):
    chat_history: List[ChatMessage] = Field(alias="chatHistory")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class TranslateRequest(BaseModel):
    text: str
    language: str


class TranslateResponse(BaseModel):
    success: bool
    translated: Optional[str] = None
    language: str
