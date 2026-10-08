"""Audiobook reader backend: a Flask app that Vercel runs as the project's entrypoint."""

import os

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
app = Flask(__name__, static_folder=PUBLIC, static_url_path="")

MAX_CHUNK_CHARS = 5000  # multilingual_v2 per-request limit; the page sends far less

MISSING_KEY = (
    "ELEVENLABS_API_KEY is not set. On Vercel: Project → Settings → Environment Variables, "
    "add it, then redeploy. Locally: put it in a .env file."
)


def get_client():
    key = os.environ.get("ELEVENLABS_API_KEY")
    return ElevenLabs(api_key=key) if key else None


def clamp(value, lo, hi, default):
    try:
        return min(hi, max(lo, float(value)))
    except (TypeError, ValueError):
        return default


@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/api/voices")
def voices():
    client = get_client()
    if client is None:
        return jsonify(error=MISSING_KEY), 500
    try:
        result = client.voices.search(page_size=100)
    except ApiError as e:
        return jsonify(error=f"ElevenLabs error {e.status_code}: {e.body}"), 502
    return jsonify(
        [
            {
                "id": v.voice_id,
                "name": v.name,
                "category": v.category,
                "labels": v.labels or {},
                "preview_url": v.preview_url,
            }
            for v in result.voices
        ]
    )


@app.post("/api/speak")
def speak():
    client = get_client()
    if client is None:
        return jsonify(error=MISSING_KEY), 500

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Open http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
