"""Unique entrypoint for the isolated semantic similarity service."""

import os

from .main import app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SEMANTIC_HOST", "127.0.0.1")
    port = int(os.getenv("SEMANTIC_PORT", "8002"))
    uvicorn.run(app, host=host, port=port)
