"""Local dev server: serves public/ and mounts the two API functions the way Vercel does."""

import os

from flask import Flask, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from api.speak import app as speak_app
from api.voices import app as voices_app

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

site = Flask(__name__, static_folder=PUBLIC, static_url_path="")


@site.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


application = DispatcherMiddleware(site, {"/api/voices": voices_app, "/api/speak": speak_app})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Open http://127.0.0.1:{port}")
    run_simple("127.0.0.1", port, application, use_reloader=True)
