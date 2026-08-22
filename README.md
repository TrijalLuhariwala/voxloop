# VoxLoop

VoxLoop is a two-agent voice workflow built around live speech capture, a draft-response agent, a critique agent, and an improvement pass.

## Stack

- `frontend/`: Next.js minimal interface with browser speech recognition
- `backend/`: FastAPI + WebSockets + LangChain + LangGraph + Mistral APIs
- `backend/voxloop.db`: SQLite long-term memory store
- Local STT: `faster-whisper`
- Local TTS: `pyttsx3`

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Edit `backend/.env` and add your Mistral keys before starting the API.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://127.0.0.1:8000` by default.

## Workflow

1. The user picks the agent job, for example `customer support`.
2. The browser records live audio and sends it to FastAPI over a WebSocket.
3. The backend transcribes the audio locally with `faster-whisper`.
4. Agent 1 generates the original response with the prompt: `You are a /selected topic/ voice assist agent...`
5. Agent 2 critiques the response using conversation history from SQLite memory.
6. Agent 2 scores `accuracy`, `relevance`, `empathy`, `clarity`, `policy_compliance`, and `overall`, then returns suggestions.
7. Agent 1 rewrites the answer using the critique.
8. The backend synthesizes the improved response locally with `pyttsx3`.
9. The UI shows the transcript, original response, scorecard, suggestions, improved response, and plays the synthesized audio.

## Environment file

Use [backend/.env.example](C:/Users/USER/Documents/Codex/2026-08-21/verify-upsk-removal/backend/.env.example) as the template:

```env
MISTRAL_API_KEY_PRIMARY=your_key_here
MISTRAL_API_KEY_CRITIC=your_key_here
MISTRAL_MODEL_PRIMARY=mistral-small-latest
MISTRAL_MODEL_CRITIC=mistral-small-latest
DATABASE_URL=sqlite:///./voxloop.db
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

## Notes

- The voice input button now records microphone audio and sends it over WebSockets.
- `faster-whisper` may require FFmpeg support on the machine depending on your audio/container setup.
- `pyttsx3` runs offline and on Windows commonly uses the local SAPI voices.
- The backend uses official LangChain Mistral integration and LangGraph state graphs, based on the current docs from LangChain and Mistral.
