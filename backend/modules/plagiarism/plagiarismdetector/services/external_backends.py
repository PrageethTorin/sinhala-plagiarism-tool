import asyncio
import json
import os
import urllib.error
import urllib.request


class ExternalServiceError(RuntimeError):
    def __init__(self, service: str, message: str):
        super().__init__(message)
        self.service = service


def _post_json_sync(url: str, payload: dict, timeout_s: float) -> object:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = None
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise ExternalServiceError(
            "http",
            f"HTTP {e.code} calling {url}. Body: {body}",
        )
    except (urllib.error.URLError, TimeoutError) as e:
        raise ExternalServiceError("network", f"Failed calling {url}: {e}")


async def post_json(url: str, payload: dict, timeout_s: float = 60.0) -> object:
    return await asyncio.to_thread(_post_json_sync, url, payload, timeout_s)


def get_paraphrase_base_url() -> str:
    return os.getenv("PARAPHRASE_API_URL", "http://127.0.0.1:5000").rstrip("/")


def get_wsa_base_url() -> str:
    return os.getenv("WSA_API_URL", "http://127.0.0.1:8001").rstrip("/")


def get_semantic_base_url() -> str:
    return os.getenv("SEMANTIC_API_URL", "http://127.0.0.1:8002").rstrip("/")


async def check_paraphrase(source_text: str, suspicious_text: str) -> dict:
    base = get_paraphrase_base_url()
    url = f"{base}/api/check-paraphrase"
    result = await post_json(
        url,
        {"sourceText": source_text, "suspiciousText": suspicious_text},
        timeout_s=120.0,
    )
    if not isinstance(result, dict):
        raise ExternalServiceError("paraphrase", f"Unexpected response from {url}: {result}")
    return result


async def check_internet(student_text: str) -> object:
    base = get_paraphrase_base_url()
    url = f"{base}/api/check-internet"
    return await post_json(url, {"studentText": student_text}, timeout_s=300.0)


async def check_wsa(source_text: str, student_text: str) -> dict:
    base = get_wsa_base_url()
    url = f"{base}/api/check-wsa"
    result = await post_json(
        url,
        {
            "sourceText": source_text,
            "studentText": student_text,
        },
        timeout_s=300.0,
    )
    if not isinstance(result, dict):
        raise ExternalServiceError("wsa", f"Unexpected response from {url}: {result}")
    return result


async def check_semantic(original_text: str, suspicious_text: str) -> dict:
    base = get_semantic_base_url()
    url = f"{base}/api/check-plagiarism"
    payload = {
        "text_pair": {"original": original_text, "suspicious": suspicious_text},
        "threshold": 0.7,
        "algorithm": "semantic",
        "check_paraphrase": False,
    }
    result = await post_json(url, payload, timeout_s=300.0)
    if not isinstance(result, dict):
        raise ExternalServiceError("semantic", f"Unexpected response from {url}: {result}")
    return result