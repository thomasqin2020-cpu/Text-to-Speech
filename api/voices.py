"""GET /api/voices: the voices on the ElevenLabs account."""

import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError
from flask import Flask, jsonify

load_dotenv()

app = Flask(__name__)
app.url_map.strict_slashes = False

MISSING_KEY = (
    "ELEVENLABS_API_KEY is not set. On Vercel: Project → Settings → Environment Variables, "
    "add it, then redeploy. Locally: put it in a .env file."
)


# Vercel may hand the function any of /api/voices, /api/voices.py or /, so match everything.
@app.get("/", defaults={"_path": ""})
@app.get("/<path:_path>")
def voices(_path):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return jsonify(error=MISSING_KEY), 500
    client = ElevenLabs(api_key=key)
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
