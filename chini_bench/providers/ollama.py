"""Ollama provider (local models).

Talks to a local Ollama server at $OLLAMA_HOST (default http://localhost:11434)
via its native /api/chat endpoint. Requires the model to already be pulled
(`ollama pull <model>`).
"""

from __future__ import annotations

import os
from typing import Any

import requests

from chini_bench.providers.common import extract_json

DEFAULT_HOST = "http://localhost:11434"


def generate(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        r = requests.post(f"{host}/api/chat", json=payload, timeout=300)
    except requests.ConnectionError as e:
        raise RuntimeError(
            f"Could not reach Ollama at {host}. Is it running? (ollama serve)"
        ) from e
    if not r.ok:
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text[:200]}")
    raw = r.json().get("message", {}).get("content", "")
    return extract_json(raw)
