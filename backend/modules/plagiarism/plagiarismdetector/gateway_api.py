"""Unique entrypoint for the isolated plagiarism detector gateway."""

import os

from .main import app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("GATEWAY_HOST", "127.0.0.1")
    port = int(os.getenv("GATEWAY_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
