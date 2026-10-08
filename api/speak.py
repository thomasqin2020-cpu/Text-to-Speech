"""POST /api/speak: one passage of text to MP3 audio."""

import os

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError
from flask import Flask, Response, jsonify, request

load_dotenv()

app = Flask(__name__)
app.url_map.strict_slashes = False

MAX_CHUNK_CHARS = 5000  # multilingual_v2 per-request limit; the client sends far less

MISSING_KEY = (
    "ELEVENLABS_API_KEY is not set. On Vercel: Project → Settings → Environment Variables, "
    "add it, then redeploy. Locally: put it in a .env file."
)


def clamp(value, lo, hi, default):
    try:
        return min(hi, max(lo, float(value)))
    except (TypeError, ValueError):
        return default


# Vercel may hand the function any of /api/speak, /api/speak.py or /, so match everything.
@app.post("/", defaults={"_path": ""})
@app.post("/<path:_path>")
def speak(_path):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return jsonify(error=MISSING_KEY), 500
    client = ElevenLabs(api_key=key)

    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    voice_id = data.get("voice_id")
    model_id = data.get("model_id") or "eleven_multilingual_v2"

    if not text or not voice_id:
        return jsonify(error="text and voice_id are required"), 400
    if len(text) > MAX_CHUNK_CHARS:
        return jsonify(error=f"chunk exceeds {MAX_CHUNK_CHARS} characters"), 400

    # previous_text/next_text let the model keep intonation continuous across chunks.
    extra = {}
    if data.get("previous_text"):
        extra["previous_text"] = data["previous_text"]
    if data.get("next_text"):
        extra["next_text"] = data["next_text"]
    settings = data.get("voice_settings")
    if isinstance(settings, dict):
        extra["voice_settings"] = VoiceSettings(
            stability=clamp(settings.get("stability"), 0, 1, 0.5),
            similarity_boost=clamp(settings.get("similarity_boost"), 0, 1, 0.75),
            style=clamp(settings.get("style"), 0, 1, 0.0),
            use_speaker_boost=True,
        )

    try:
        stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128",
            **extra,
        )
        audio = b"".join(stream)
    except ApiError as e:
        return jsonify(error=f"ElevenLabs error {e.status_code}: {e.body}"), 502

    return Response(audio, mimetype="audio/mpeg")
