from __future__ import annotations

import base64
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, select

from .audio import save_uploaded_audio, synthesize_speech, transcribe_audio
from .config import settings
from .db import ConversationRun, get_session, init_db
from .models import (
    ConversationMemoryItem,
    CritiqueResult,
    ResetSessionRequest,
    SessionHistoryResponse,
    VoiceTurnRequest,
    VoiceTurnResponse,
)
from .workflow import run_workflow


GENERATED_AUDIO_DIR = Path(__file__).resolve().parents[1] / "generated_audio"
GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/generated-audio",
    StaticFiles(directory=GENERATED_AUDIO_DIR),
    name="generated-audio",
)


def _history_text(session_id: str) -> tuple[str, list[ConversationMemoryItem]]:
    with get_session() as session:
        rows = (
            session.execute(
                select(ConversationRun)
                .where(ConversationRun.session_id == session_id)
                .order_by(ConversationRun.created_at.asc())
                .limit(50)
            )
            .scalars()
            .all()
        )

    memory = [
        ConversationMemoryItem(
            user_message=row.user_message,
            original_response=row.original_response,
            improved_response=row.improved_response,
            sentiment=row.sentiment,
            user_state=row.user_state,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]

    history_chunks = []
    for item in memory:
        history_chunks.append(
            "\n".join(
                [
                    f"User: {item.user_message}",
                    f"Original agent response: {item.original_response}",
                    f"Improved agent response: {item.improved_response}",
                    f"Sentiment: {item.sentiment}",
                    f"User state: {item.user_state}",
                ]
            )
        )
    return "\n\n".join(history_chunks), memory


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reset-session")
def reset_session(request: ResetSessionRequest) -> dict[str, str]:
    with get_session() as session:
        session.execute(
            delete(ConversationRun).where(ConversationRun.session_id == request.session_id)
        )
        session.commit()
    return {"status": "ok", "message": f"Session '{request.session_id}' reset successfully."}


@app.get("/api/session/{session_id}/history", response_model=SessionHistoryResponse)
def get_session_history(session_id: str) -> SessionHistoryResponse:
    _, memory = _history_text(session_id)
    return SessionHistoryResponse(session_id=session_id, memory=memory)



@app.post("/api/voice-turn", response_model=VoiceTurnResponse)
def voice_turn(request: VoiceTurnRequest) -> VoiceTurnResponse:
    try:
        history_text, _ = _history_text(request.session_id)
        result = run_workflow(
            selected_topic=request.selected_topic,
            transcript=request.transcript,
            history_text=history_text,
        )
        critique = CritiqueResult.model_validate(result["critique"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc

    with get_session() as session:
        row = ConversationRun(
            session_id=request.session_id,
            selected_topic=request.selected_topic,
            user_message=request.transcript,
            sentiment=critique.sentiment,
            user_state=critique.user_state,
            original_response=result["original_response"],
            improved_response=result["improved_response"],
            scorecard_json=critique.scorecard.model_dump_json(),
            suggestions_json=json.dumps(critique.suggestions),
        )
        session.add(row)
        session.commit()

    _, updated_memory = _history_text(request.session_id)
    return VoiceTurnResponse(
        session_id=request.session_id,
        selected_topic=request.selected_topic,
        transcript=request.transcript,
        original_response=result["original_response"],
        critique=critique,
        improved_response=result["improved_response"],
        tts_audio_url="",
        memory=updated_memory,
    )


@app.websocket("/ws/voice-turn")
async def voice_turn_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        session_id = str(payload.get("session_id", "")).strip()
        selected_topic = str(payload.get("selected_topic", "")).strip()
        audio_base64 = str(payload.get("audio_base64", "")).strip()
        mime_type = str(payload.get("mime_type", "audio/webm")).strip()

        if not session_id or not selected_topic or not audio_base64:
            await websocket.send_json(
                {"type": "error", "message": "session_id, selected_topic, and audio_base64 are required."}
            )
            return

        suffix = ".wav" if "wav" in mime_type else ".webm"
        audio_bytes = base64.b64decode(audio_base64)

        await websocket.send_json({"type": "status", "stage": "stt", "message": "Transcribing audio locally..."})
        audio_path = save_uploaded_audio(audio_bytes, suffix=suffix)
        transcript = await transcribe_audio(audio_path)
        if not transcript:
            await websocket.send_json({"type": "error", "message": "No speech could be transcribed from the audio."})
            return
        await websocket.send_json({"type": "transcript", "transcript": transcript})

        await websocket.send_json({"type": "status", "stage": "llm", "message": "Running the agent loop..."})
        history_text, _ = _history_text(session_id)
        result = run_workflow(
            selected_topic=selected_topic,
            transcript=transcript,
            history_text=history_text,
        )
        critique = CritiqueResult.model_validate(result["critique"])

        await websocket.send_json({"type": "status", "stage": "tts", "message": "Synthesizing improved response locally..."})
        audio_file_name = await synthesize_speech(result["improved_response"])

        with get_session() as session:
            row = ConversationRun(
                session_id=session_id,
                selected_topic=selected_topic,
                user_message=transcript,
                sentiment=critique.sentiment,
                user_state=critique.user_state,
                original_response=result["original_response"],
                improved_response=result["improved_response"],
                scorecard_json=critique.scorecard.model_dump_json(),
                suggestions_json=json.dumps(critique.suggestions),
            )
            session.add(row)
            session.commit()

        _, updated_memory = _history_text(session_id)
        response = VoiceTurnResponse(
            session_id=session_id,
            selected_topic=selected_topic,
            transcript=transcript,
            original_response=result["original_response"],
            critique=critique,
            improved_response=result["improved_response"],
            tts_audio_url=f"/generated-audio/{audio_file_name}" if audio_file_name else "",
            memory=updated_memory,
        )
        await websocket.send_json({"type": "result", "payload": response.model_dump()})
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": f"Voice workflow failed: {exc}"})
