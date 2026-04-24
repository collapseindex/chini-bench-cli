"""HTTP client for the CHINI-bench server.

All network I/O lives here. Everything else in the package consumes the
typed helpers below so the rest of the code stays unaware of HTTP details.
"""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE_URL = "https://chinilla.com"
USER_AGENT = "chini-bench-cli/0.6.0 (+https://github.com/collapseindex/chini-bench-cli)"
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


def submit(
    problem_id: str,
    submitter: str,
    canvas: dict[str, Any],
    model: str | None = None,
    harness: str | None = None,
    v1_canvas: dict[str, Any] | None = None,
    v1_score: int | None = None,
    v1_passed: bool | None = None,
    feedback: dict[str, Any] | None = None,
    tokens_total: int | None = None,
) -> dict[str, Any]:
    """POST /api/bench/submit - send a CanvasState, get a deterministic score.

    Reflexion-track args (v0.6+): when present, the v1 artifacts are stored
    on the result file under `meta.*` for audit and leaderboard display.
    """
    payload: dict[str, Any] = {
        "problemId": problem_id,
        "submitter": submitter,
        "canvas": canvas,
        "website": "",  # honeypot must be empty for real users
    }
    if model:
        payload["model"] = model
    if harness:
        payload["harness"] = harness
    if v1_canvas is not None:
        payload["v1Canvas"] = v1_canvas
    if v1_score is not None:
        payload["v1Score"] = v1_score
    if v1_passed is not None:
        payload["v1Passed"] = v1_passed
    if feedback is not None:
        payload["feedback"] = feedback
    if tokens_total is not None:
        payload["tokensTotal"] = tokens_total
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


def get_feedback(problem_id: str, canvas: dict[str, Any]) -> dict[str, Any]:
    """POST /api/bench/feedback - get a redacted FeedbackPacket for a v1 canvas.

    Used by the Reflexion track between v1 generation and v2 generation. The
    packet contains no scores or thresholds, only failing-scenario metrics
    and structural-check results.
    """
    payload = {
        "problemId": problem_id,
        "canvas": canvas,
        "website": "",
    }
    r = _session().post(
        f"{base_url()}/api/bench/feedback",
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )
    body = _safe_json(r)
    if not r.ok:
        msg = body.get("error") if isinstance(body, dict) else r.text
        raise RuntimeError(f"Feedback failed ({r.status_code}): {msg}")
    return body


def _safe_json(r: requests.Response) -> Any:
    try:
        return r.json()
    except ValueError:
        return {"error": r.text}
