"""Audiobook reader: paste text, hear it read aloud through ElevenLabs."""

import hashlib
import os
from collections import OrderedDict

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    raise SystemExit("Set ELEVENLABS_API_KEY in your environment or a .env file.")

client = ElevenLabs(api_key=API_KEY)
app = Flask(__name__, static_folder="static")

# Small in-memory cache so replaying or seeking back doesn't spend credits twice.
CACHE_LIMIT = 200
audio_cache: OrderedDict[str, bytes] = OrderedDict()

MAX_CHUNK_CHARS = 5000  # multilingual_v2 per-request limit; the client sends far less


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/voices")
def voices():
    try:
        result = client.voices.search(page_size=100)
    except ApiError as e:
        return jsonify(error=f"ElevenLabs error {e.status_code}: {e.body}"), 502
    return jsonify(
        [{"id": v.voice_id, "name": v.name, "category": v.category} for v in result.voices]
    )


@app.post("/api/speak")
def speak():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    voice_id = data.get("voice_id")
    model_id = data.get("model_id") or "eleven_multilingual_v2"
    previous_text = data.get("previous_text") or None
    next_text = data.get("next_text") or None

    if not text or not voice_id:
        return jsonify(error="text and voice_id are required"), 400
    if len(text) > MAX_CHUNK_CHARS:
        return jsonify(error=f"chunk exceeds {MAX_CHUNK_CHARS} characters"), 400

    key = hashlib.sha256(
        "\x00".join([voice_id, model_id, text, previous_text or "", next_text or ""]).encode()
    ).hexdigest()

    if key in audio_cache:
        audio_cache.move_to_end(key)
        return Response(audio_cache[key], mimetype="audio/mpeg")

    try:
        # previous_text/next_text let the model keep intonation continuous across chunks.
        context = {}
        if previous_text:
            context["previous_text"] = previous_text
        if next_text:
            context["next_text"] = next_text
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

    audio_cache[key] = audio
    if len(audio_cache) > CACHE_LIMIT:
        audio_cache.popitem(last=False)
    return Response(audio, mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
