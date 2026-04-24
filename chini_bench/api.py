"""HTTP client for the CHINI-bench server.

All network I/O lives here. Everything else in the package consumes the
typed helpers below so the rest of the code stays unaware of HTTP details.
"""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE_URL = "https://chinilla.com"
USER_AGENT = "chini-bench-cli/0.1.0 (+https://github.com/collapseindex/chini-bench-cli)"
TIMEOUT_SECONDS = 60


def base_url() -> str:
    return os.environ.get("CHINI_BENCH_URL", DEFAULT_BASE_URL).rstrip("/")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def list_problems() -> list[dict[str, Any]]:
    """GET /api/bench/problems - returns summary list."""
    r = _session().get(f"{base_url()}/api/bench/problems", timeout=TIMEOUT_SECONDS)
    r.raise_for_status()
    return r.json().get("problems", [])


def get_problem(problem_id: str) -> dict[str, Any]:
    """GET /api/bench/problems?id=<id> - returns full problem schema."""
    r = _session().get(
        f"{base_url()}/api/bench/problems",
        params={"id": problem_id},
        timeout=TIMEOUT_SECONDS,
    )
    if r.status_code == 404:
        raise ValueError(f"Unknown problem id: {problem_id}")
    r.raise_for_status()
    return r.json().get("problem", {})


def submit(problem_id: str, submitter: str, canvas: dict[str, Any]) -> dict[str, Any]:
    """POST /api/bench/submit - send a CanvasState, get a deterministic score."""
    payload = {
        "problemId": problem_id,
        "submitter": submitter,
        "canvas": canvas,
        "website": "",  # honeypot must be empty for real users
    }
    r = _session().post(
        f"{base_url()}/api/bench/submit",
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )
    body = _safe_json(r)
    if not r.ok:
        msg = body.get("error") if isinstance(body, dict) else r.text
        raise RuntimeError(f"Submit failed ({r.status_code}): {msg}")
    return body


def _safe_json(r: requests.Response) -> Any:
    try:
        return r.json()
    except ValueError:
        return {"error": r.text}
