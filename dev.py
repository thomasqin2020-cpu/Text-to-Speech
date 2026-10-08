"""Local dev server: serves public/ and mounts the two API functions the way Vercel does."""

import os

from flask import Flask, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple



def load(name):
    """Import api/<name>.py by path; api/ is not a package so Vercel sees only the two functions."""
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


speak_app = load("speak")
voices_app = load("voices")

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
