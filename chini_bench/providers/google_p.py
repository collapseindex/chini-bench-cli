"""Google (Gemini) provider.

Uses the `google-generativeai` SDK. JSON mode is requested via
`response_mime_type="application/json"`.
"""

from __future__ import annotations

import os
from typing import Any

from chini_bench.providers.common import extract_json


def generate(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError(
            "Google Gemini SDK not installed. Run: pip install google-generativeai"
        ) from e

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY (or GEMINI_API_KEY) environment variable is not set."
        )

    genai.configure(api_key=api_key)

    gen_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt,
    )

    try:
        resp = gen_model.generate_content(
            user_prompt,
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        )
    except Exception:
        # Older models may not support response_mime_type.
        resp = gen_model.generate_content(
            user_prompt,
            generation_config={"temperature": 0.2},
        )

    raw = getattr(resp, "text", "") or ""
    return extract_json(raw)
