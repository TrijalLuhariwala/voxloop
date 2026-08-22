from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import pyttsx3
from faster_whisper import WhisperModel

from .config import settings


_whisper_model: WhisperModel | None = None


def _audio_root() -> Path:
    root = Path(__file__).resolve().parents[1] / "generated_audio"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    return _whisper_model


def _transcribe_sync(audio_path: Path) -> str:
    model = _get_whisper_model()
    segments, _ = model.transcribe(str(audio_path), vad_filter=True)
    transcript_parts = [segment.text.strip() for segment in segments if segment.text.strip()]
    return " ".join(transcript_parts).strip()


async def transcribe_audio(audio_path: Path) -> str:
    return await asyncio.to_thread(_transcribe_sync, audio_path)


def _synthesize_sync(text: str) -> str:
    output_path = _audio_root() / f"{uuid4()}.wav"
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    return output_path.name


async def synthesize_speech(text: str) -> str:
    return await asyncio.to_thread(_synthesize_sync, text)


def save_uploaded_audio(data: bytes, suffix: str = ".webm") -> Path:
    output_path = _audio_root() / f"{uuid4()}{suffix}"
    output_path.write_bytes(data)
    return output_path
