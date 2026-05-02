"""Unique entrypoint for the isolated paraphrase detection service."""

import os

from .server import app


if __name__ == "__main__":
    host = os.getenv("PARAPHRASE_HOST", "127.0.0.1")
    port = int(os.getenv("PARAPHRASE_PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"

    print(f"Paraphrase Detection API is running on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
