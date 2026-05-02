import os
import sys
import time
import subprocess
import threading
import socket
from typing import List, Tuple


def _repo_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _venv_python() -> str:
    root = _repo_root()
    candidate = os.path.join(root, ".venv", "Scripts", "python.exe")
    if os.path.exists(candidate):
        return candidate
    return sys.executable


def _stream_output(prefix: str, pipe):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            msg = f"[{prefix}] {line.rstrip()}"
            try:
                print(msg)
            except UnicodeEncodeError:
                safe_msg = msg.encode("ascii", errors="replace").decode("ascii")
                print(safe_msg)
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _start_process(prefix: str, args: List[str], env: dict) -> subprocess.Popen:
    creationflags = 0
    # Windows: create a new process group so Ctrl+C handling is saner
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    proc = subprocess.Popen(
        args,
        cwd=_repo_root(),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
    )

    assert proc.stdout is not None
    t = threading.Thread(target=_stream_output, args=(prefix, proc.stdout), daemon=True)
    t.start()
    return proc


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if TCP connect succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, name: str, procs: List[Tuple[str, subprocess.Popen]], timeout_s: float = 120.0) -> None:
    """
    Wait until host:port is accepting connections OR fail fast if a child process exits.
    """
    start = time.time()
    while True:
        # If the port is open, we're ready
        if _is_port_open(host, port):
            print(f"[BOOT] {name} is ready on {host}:{port}")
            return

        # If any process exited while waiting, stop early
        for pname, p in procs:
            code = p.poll()
            if code is not None:
                raise RuntimeError(f"{pname} exited with code {code} while waiting for {name} to start.")

        # Timeout
        if (time.time() - start) > timeout_s:
            raise TimeoutError(f"Timed out waiting for {name} on {host}:{port} after {timeout_s:.0f}s")

        time.sleep(0.5)


def main() -> int:
    py = _venv_python()
    env = os.environ.copy()

    gateway_port = int(env.get("GATEWAY_PORT", "8000"))
    wsa_port = int(env.get("WSA_PORT", "8001"))
    semantic_port = int(env.get("SEMANTIC_PORT", "8002"))
    paraphrase_port = int(env.get("PARAPHRASE_PORT", "5000"))

    # Windows consoles often default to cp1252; force UTF-8 to avoid UnicodeEncodeError
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    # Internal service discovery for the gateway
    env["WSA_API_URL"] = f"http://127.0.0.1:{wsa_port}"
    env["PARAPHRASE_API_URL"] = f"http://127.0.0.1:{paraphrase_port}"
    env["SEMANTIC_API_URL"] = f"http://127.0.0.1:{semantic_port}"

    # Semantic is REQUIRED (not optional)
    env["START_SEMANTIC"] = "1"

    procs: List[Tuple[str, subprocess.Popen]] = []
    try:
        print("Starting services in one terminal...")
        print(f"- Gateway:    http://127.0.0.1:{gateway_port}")
        print(f"- WSA:        http://127.0.0.1:{wsa_port}")
        print(f"- Paraphrase: http://127.0.0.1:{paraphrase_port}")
        print(f"- Semantic:   http://127.0.0.1:{semantic_port}")
        print("Press Ctrl+C to stop all.\n")

        # Start WSA
        procs.append((
            "WSA",
            _start_process(
                "WSA",
                [py, "-m", "uvicorn", "backend.modules.plagiarism.writingstyleanalaysis.main:app", "--host", "127.0.0.1", "--port", str(wsa_port)],
                env,
            ),
        ))

        # Start Paraphrase (Flask)
        procs.append((
            "PARA",
            _start_process(
                "PARA",
                [py, os.path.join("backend", "modules", "plagiarism", "parapahsedetection", "server.py")
],
                env,
            ),
        ))

        # Start Semantic (REQUIRED)
        procs.append((
            "SEMA",
            _start_process(
                "SEMA",
                [py, "-m", "uvicorn", "backend.modules.plagiarism.semanticsimiliarty.main:app"
, "--host", "127.0.0.1", "--port", str(semantic_port)],
                env,
            ),
        ))

        # Wait until the dependent services are actually listening
        _wait_for_port("127.0.0.1", wsa_port, "WSA", procs, timeout_s=120.0)
        _wait_for_port("127.0.0.1", paraphrase_port, "Paraphrase", procs, timeout_s=180.0)  # model load can be slow
        _wait_for_port("127.0.0.1", semantic_port, "Semantic", procs, timeout_s=180.0)      # model load can be slow

        # Start Gateway LAST (so it won't fail on cold start)
        procs.append((
            "GATE",
            _start_process(
                "GATE",
                [py, "-m", "uvicorn", "backend.modules.plagiarism.plagiarismdetector.main:app"
, "--host", "127.0.0.1", "--port", str(gateway_port)],
                env,
            ),
        ))

        _wait_for_port("127.0.0.1", gateway_port, "Gateway", procs, timeout_s=60.0)

        # Watchdog: if any service exits, stop everything
        while True:
            for name, p in procs:
                code = p.poll()
                if code is not None:
                    print(f"\n[{name}] exited with code {code}. Stopping all services...")
                    return code if code != 0 else 1
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping all services...")
        return 0
    except Exception as e:
        print(f"\n[BOOT] ERROR: {e}")
        return 1
    finally:
        for _, p in procs:
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
