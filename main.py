import os
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from model import VoiceShieldModel
from tool import MAX_AUDIO_BYTES, InvalidAudioError, decode_audio

INDEX_FILE = Path(__file__).with_name("index.html")
_detector = None
_analysis_lock = Lock()


def get_detector():
    global _detector
    if _detector is None:
        _detector = VoiceShieldModel()
    return _detector


def analyze_audio(samples):
    with _analysis_lock:
        return get_detector().analyze(samples)


@asynccontextmanager
async def lifespan(_app):
    if os.environ.get("PRELOAD_MODEL", "").casefold() == "true":
        await run_in_threadpool(get_detector)
    yield


app = FastAPI(
    title="VoiceShield AI",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/")
async def home():
    return FileResponse(INDEX_FILE)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": _detector is not None,
    }


@app.post("/api/analyze")
async def analyze(audio: UploadFile = File(...)):
    audio_bytes = await audio.read(MAX_AUDIO_BYTES + 1)
    try:
        samples, duration = decode_audio(audio_bytes, audio.filename)
    except InvalidAudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await audio.close()

    fake_probability, real_probability = await run_in_threadpool(
        analyze_audio,
        samples,
    )
    return {
        "verdict": (
            "AI-generated voice likely"
            if fake_probability >= 0.6
            else "Human voice likely"
        ),
        "fake_probability": round(fake_probability, 4),
        "real_probability": round(real_probability, 4),
        "duration_seconds": round(duration, 2),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "7860")),
    )
