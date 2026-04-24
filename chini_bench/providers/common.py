"""Shared helpers for parsing model output into a CanvasState dict."""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json(raw: str) -> dict[str, Any]:
    """Best-effort: strip code fences, trim prose, parse JSON.

    Models occasionally wrap output in ```json ... ``` or add a trailing
    sentence. We trim those, then parse. If parsing still fails, we raise.
    """
    text = raw.strip()

    # Strip ```json ... ``` or ``` ... ``` fences
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    # Find the outermost {...} block in case there is leading/trailing prose
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last < first:
        raise ValueError("Model did not return any JSON object.")
    candidate = text[first : last + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse model output as JSON: {e}") from e
