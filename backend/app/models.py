from __future__ import annotations

from pydantic import BaseModel, Field


class VoiceTurnRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)
    selected_topic: str = Field(min_length=2, max_length=200)
    transcript: str = Field(min_length=1, max_length=4000)


class GradingScorecard(BaseModel):
    accuracy: int = Field(ge=0, le=100)
    relevance: int = Field(ge=0, le=100)
    empathy: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    policy_compliance: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)


class CritiqueResult(BaseModel):
    sentiment: str
    user_state: str
    scorecard: GradingScorecard
    suggestions: list[str]
    reasoning: str


class ConversationMemoryItem(BaseModel):
    user_message: str
    original_response: str
    improved_response: str
    sentiment: str
    user_state: str
    created_at: str


class ResetSessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)


class SessionHistoryResponse(BaseModel):
    session_id: str
    memory: list[ConversationMemoryItem]


class VoiceTurnResponse(BaseModel):
    session_id: str
    selected_topic: str
    transcript: str
    original_response: str
    critique: CritiqueResult
    improved_response: str
    tts_audio_url: str
    memory: list[ConversationMemoryItem]

