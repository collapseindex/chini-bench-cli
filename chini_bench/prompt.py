"""Build the system + user prompt for a benchmark problem.

This mirrors the prompt used by the public submit form on chinilla.com so a
model run via this CLI gets the same instructions as one fed via copy-paste.
Keep this file in sync with `src/scripts/benchSubmit.ts` upstream.
"""

from __future__ import annotations

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
