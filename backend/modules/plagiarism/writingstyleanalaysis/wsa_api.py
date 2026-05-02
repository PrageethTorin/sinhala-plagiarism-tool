"""Unique entrypoint for the isolated writing style analysis service."""

import os

from .main import app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WSA_HOST", "127.0.0.1")
    port = int(os.getenv("WSA_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
