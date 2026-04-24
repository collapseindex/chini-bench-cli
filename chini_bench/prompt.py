"""Build the system + user prompt for a benchmark problem.

This mirrors the prompt used by the public submit form on chinilla.com so a
model run via this CLI gets the same instructions as one fed via copy-paste.
Keep this file in sync with `src/scripts/benchSubmit.ts` upstream.
"""

from __future__ import annotations

import hashlib
from typing import Any

SYSTEM_PROMPT = (
    "You are an experienced systems architect. Emit a Chinilla CanvasState as "
    "JSON that satisfies the benchmark prompt below.\n\n"
    "## Schema\n"
    "Return a single JSON object with exactly this shape:\n"
    "```\n"
    "{\n"
    '  "name": "string (free text title)",\n'
    '  "components": [\n'
    "    {\n"
    '      "id": "stable-lowercase-id",\n'
    '      "type": "person | step | storage | decision | trigger | tool | channel",\n'
    '      "label": "human-readable name",\n'
    '      "description": "optional short description",\n'
    '      "behavior": { "mode": "passthrough | transform | filter | queue | split | delay | condition | retry | ratelimit | circuitbreaker | batch | replicate" },\n'
    '      "cost": { "monthlyUsd": 0, "setupUsd": 0 }\n'
    "    }\n"
    "  ],\n"
    '  "connections": [\n'
    '    { "id": "edge-id", "from": "source-component-id", "to": "target-component-id", "label": "optional" }\n'
    "  ]\n"
    "}\n"
    "```\n\n"
    "## Rules\n"
    "- Use stable lowercase ids (e.g. \"gateway\", \"queue-1\"). Never reuse an id.\n"
    "- Every connection.from and connection.to MUST reference an existing component id.\n"
    "- Apply behavior.mode where it belongs: queue on workers, ratelimit on entry, "
    "circuitbreaker on flaky outbound edges, retry on idempotent calls.\n"
    "- Do NOT include x/y positions; layout is computed automatically.\n"
    "- Return JSON only. No prose, no markdown fences, no comments."
)


def build_user_prompt(problem: dict[str, Any]) -> str:
    """Render the problem-specific portion of the prompt."""
    constraints = problem.get("constraints") or {}
    constraint_lines: list[str] = []
    if constraints.get("maxComponents") is not None:
        constraint_lines.append(f"- Max components: {constraints['maxComponents']}")
    required = constraints.get("requiredBehaviors") or []
    if required:
        constraint_lines.append(
            "- Required to appear at least once: " + ", ".join(required)
        )
    if constraints.get("monthlyCostUsd") is not None:
        constraint_lines.append(f"- Monthly budget: ${constraints['monthlyCostUsd']}")

    scenarios = problem.get("scenarios") or []
    scenario_lines = [f"- {s['label']}: {s['description']}" for s in scenarios]

    parts = [
        f"# Problem {problem['id']}: {problem['title']}",
        "",
        problem.get("prompt", ""),
        "",
        "## Constraints",
        *constraint_lines,
        "",
        "## Scenarios that will grade this design",
        *scenario_lines,
        "",
        "Emit the full CanvasState JSON now.",
    ]
    return "\n".join(parts)


def build_full_prompt(problem: dict[str, Any]) -> str:
    """System + user prompt joined into a single string (for `prompt` command)."""
    return SYSTEM_PROMPT + "\n\n" + build_user_prompt(problem)


def system_prompt_hash() -> str:
    """First 12 hex chars of sha256(SYSTEM_PROMPT).

    Sent with every `run` submission as `harness=chini-bench-cli:<hash>`.
    Lets the server (and the leaderboard) distinguish unmodified CLI runs
    from forks that changed the system prompt. Same prompt, same hash,
    on every machine.
    """
    return hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Reflexion track (v0.6+)
# ---------------------------------------------------------------------------

REVISION_BLOCK = (
    "\n\n## REVISION MODE\n"
    "You may receive a second user message containing a FeedbackPacket from a "
    "deterministic simulator. When you do, return ONLY a revised CanvasState "
    "that addresses the failing scenarios and structural checks. The packet "
    "contains:\n"
    "- failing scenarios with observed-vs-target metrics\n"
    "- failing structural checks with missing components or behaviors\n"
    "- a controlled list of observation phrases\n"
    "You will not see your composite score. Trust the packet; do not request "
    "more information. Return JSON only."
)

REFLEX_SYSTEM_PROMPT = SYSTEM_PROMPT + REVISION_BLOCK


def build_revision_prompt(feedback_packet: dict[str, Any]) -> str:
    """Render the message-3 user prompt that delivers the FeedbackPacket."""
    import json as _json

    return (
        "Your previous CanvasState produced this FeedbackPacket from the "
        "simulator:\n\n"
        + _json.dumps(feedback_packet, indent=2)
        + "\n\nRevise the CanvasState to fix every failing scenario and "
        "structural check. Return the full revised CanvasState JSON only."
    )


def system_prompt_hash_reflex() -> str:
    """First 12 hex chars of sha256(REFLEX_SYSTEM_PROMPT).

    Sent with every `reflex run` submission as
    `harness=chini-bench-reflex:<hash>`. Distinct from the single-shot hash
    so the server can split runs into the two leaderboards without
    inspecting the canvas.
    """
    return hashlib.sha256(REFLEX_SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:12]
