"""Local result archive + score pretty-printer.

All generated canvases land in ./data/runs/ with a sortable timestamped name
so users never lose a run, even if the submit call fails.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path("data") / "runs"


def save_run(problem_id: str, provider: str, model: str, canvas: dict[str, Any]) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = model.replace("/", "-").replace(":", "-")
    name = f"{ts}_{problem_id}_{provider}_{safe_model}.json"
    path = DATA_DIR / name
    path.write_text(json.dumps(canvas, indent=2), encoding="utf-8")
    return path


def score_print(result: dict[str, Any]) -> None:
    """Render the /api/bench/submit response as a human-friendly block."""
    score = result.get("compositeScore", 0)
    passed = result.get("passed", False)
    submitter = result.get("submitter", "unknown")
    notes = result.get("notes") or []
    sub = result.get("subscores") or {}

    bar = "=" * 50
    verdict = "PASS" if passed else "FAIL"
    print(bar)
    print(f"  Score: {score} / 100   [{verdict}]")
    print(f"  Submitter: {submitter}")
    if sub:
        print("  Subscores:")
        for k, v in sub.items():
            print(f"    - {k}: {v}")
    if notes:
        print("  Notes:")
        for n in notes:
            print(f"    - {n}")
    print(bar)
