"""Audiobook reader backend. Runs as a Vercel Python function, or locally with `python api/index.py`."""

import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")

MAX_CHUNK_CHARS = 5000  # multilingual_v2 per-request limit; the client sends far less


def get_client():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return None
    return ElevenLabs(api_key=key)


MISSING_KEY = (
    "ELEVENLABS_API_KEY is not set. On Vercel: Project → Settings → Environment Variables, "
    "add it, then redeploy. Locally: put it in a .env file."
)


@app.get("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")


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
        [{"id": v.voice_id, "name": v.name, "category": v.category} for v in result.voices]
    )


@app.post("/api/speak")
def speak():
    client = get_client()
    if client is None:
        return jsonify(error=MISSING_KEY), 500

    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    voice_id = data.get("voice_id")
    model_id = data.get("model_id") or "eleven_multilingual_v2"

    if not text or not voice_id:
        return jsonify(error="text and voice_id are required"), 400
    if len(text) > MAX_CHUNK_CHARS:
        return jsonify(error=f"chunk exceeds {MAX_CHUNK_CHARS} characters"), 400

    # previous_text/next_text let the model keep intonation continuous across chunks.
    context = {}
    if data.get("previous_text"):
        context["previous_text"] = data["previous_text"]
    if data.get("next_text"):
        context["next_text"] = data["next_text"]

    try:
        stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128",
            **context,
        )
        audio = b"".join(stream)
    except ApiError as e:
        return jsonify(error=f"ElevenLabs error {e.status_code}: {e.body}"), 502

    return Response(audio, mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
