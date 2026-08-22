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
    # 1. Primary: Use gTTS (Google Voice) - 100% reliable on Linux/Docker
    try:
        from gtts import gTTS
        mp3_path = _audio_root() / f"{uuid4()}.mp3"
        tts = gTTS(text=text, lang="en")
        tts.save(str(mp3_path))
        return mp3_path.name
    except Exception as exc1:
        print(f"gTTS synthesis warning: {exc1}")

    # 2. Fallback: Use pyttsx3 offline engine
    try:
        wav_path = _audio_root() / f"{uuid4()}.wav"
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.save_to_file(text, str(wav_path))
        engine.runAndWait()
        return wav_path.name
    except Exception as exc2:
        print(f"pyttsx3 synthesis warning: {exc2}")
        return ""




async def synthesize_speech(text: str) -> str:
    # 1. Primary: Use edge-tts (Natural Neural Male Voice with +20% speed)
    try:
        import edge_tts
        mp3_path = _audio_root() / f"{uuid4()}.mp3"
        communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+20%")
        await communicate.save(str(mp3_path))
        return mp3_path.name
    except Exception as exc:
        print(f"edge-tts synthesis warning: {exc}")

    # 2. Fallback: gTTS / pyttsx3
    return await asyncio.to_thread(_synthesize_sync, text)



def save_uploaded_audio(data: bytes, suffix: str = ".webm") -> Path:
    output_path = _audio_root() / f"{uuid4()}{suffix}"
    output_path.write_bytes(data)
    return output_path
