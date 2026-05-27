#!/usr/bin/env python3
# ABOUTME: Liveness/readiness probe helper for the TinyLlama predictor container.
# ABOUTME: Usable as an exec probe (`python health.py readiness`); exits 0 ready, 1 not.
"""Health checks for the TinyLlama predictor.

KServe exposes readiness at ``GET /v1/models/<name>`` (200 + ``{"ready": true}``) and
liveness at ``GET /v1/models``. This module wraps both so the Kubernetes probes can be
either httpGet (as in the lab manifest) or exec (`python health.py readiness`) — no extra
dependencies, stdlib only.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

PORT = int(os.environ.get("KSERVE_PORT", "8080"))
MODEL_NAME = os.environ.get("MODEL_NAME", "tinyllama-completion")
TIMEOUT_S = 5


def _get(path: str) -> tuple[int, bytes]:
    """GET a local path; return (status_code, body). Status 0 on connection failure."""
    url = f"http://localhost:{PORT}{path}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except (urllib.error.URLError, OSError):
        return 0, b""


def is_live() -> bool:
    """Liveness: the HTTP server is responding at all."""
    status, _ = _get("/v1/models")
    return status == 200


def is_ready() -> bool:
    """Readiness: the named model reports ready (weights loaded)."""
    status, body = _get(f"/v1/models/{MODEL_NAME}")
    if status != 200:
        return False
    try:
        return bool(json.loads(body or b"{}").get("ready", True))
    except json.JSONDecodeError:
        return status == 200


def main(argv: list[str]) -> int:
    check = argv[1] if len(argv) > 1 else "readiness"
    ok = is_live() if check == "liveness" else is_ready()
    print(f"{check}: {'ok' if ok else 'not ready'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
