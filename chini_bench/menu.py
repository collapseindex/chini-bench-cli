"""Interactive questionary-driven menu.

Loops until the user picks Exit. Mirrors the four CLI commands plus a
guided "run end-to-end" flow that prompts for provider/model/submitter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import questionary

from chini_bench import api
from chini_bench.prompt import SYSTEM_PROMPT, build_full_prompt, build_user_prompt, system_prompt_hash
from chini_bench.providers import PROVIDERS, get_provider
from chini_bench.runner import save_run, score_print


def run_menu() -> int:
    print("CHINI-bench - interactive menu")
    print(f"Server: {api.base_url()}")
    print()

    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "List problems",
                "Show full prompt for a problem",
                "Run a model end-to-end (generate + submit)",
                "Submit a CanvasState file I already have",
                "Exit",
            ],
        ).ask()

        if choice is None or choice == "Exit":
            return 0

        try:
            if choice == "List problems":
                _action_list()
            elif choice == "Show full prompt for a problem":
                _action_prompt()
            elif choice == "Run a model end-to-end (generate + submit)":
                _action_run()
            elif choice == "Submit a CanvasState file I already have":
                _action_submit()
        except (RuntimeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\nCancelled.")
            continue
        print()


def _pick_problem() -> str | None:
    problems = api.list_problems()
    if not problems:
        print("No problems available on the server.")
        return None
    return questionary.select(
        "Which problem?",
        choices=[
            questionary.Choice(
                title=f"{p['id']:<35} top={p['topScore']:>3}  runs={p['runs']:>2}  {p['title']}",
                value=p["id"],
            )
            for p in problems
        ],
    ).ask()


def _action_list() -> None:
    problems = api.list_problems()
    for p in problems:
        print(f"  {p['id']:<35} top={p['topScore']:>3}  runs={p['runs']:>2}  {p['title']}")


def _action_prompt() -> None:
    pid = _pick_problem()
    if not pid:
        return
    problem = api.get_problem(pid)
    print()
    print(build_full_prompt(problem))


def _action_submit() -> None:
    pid = _pick_problem()
    if not pid:
        return
    submitter = questionary.text(
        "Submitter name (no spaces, alphanumeric/dash/dot/underscore):"
    ).ask()
    if not submitter:
        return
    file_path = questionary.path(
        "Path to CanvasState JSON file:",
        validate=lambda p: Path(p).exists() or "File not found",
    ).ask()
    if not file_path:
        return
    model = questionary.text(
        "Model id that produced this (optional, press enter to skip):",
        default="",
    ).ask()
    x = questionary.text("X/Twitter handle, no @ (optional):", default="").ask()
    linkedin = questionary.text("LinkedIn slug (optional):", default="").ask()
    canvas = json.loads(Path(file_path).read_text(encoding="utf-8"))
    result = api.submit(
        pid,
        submitter,
        canvas,
        model=model or None,
        x=x or None,
        linkedin=linkedin or None,
    )
    score_print(result)


def _action_run() -> None:
    pid = _pick_problem()
    if not pid:
        return
    provider = questionary.select(
        "Provider:",
        choices=sorted(PROVIDERS.keys()),
    ).ask()
    if not provider:
        return
    model = questionary.text(
        f"Model id for {provider} (e.g. gpt-4o-mini, claude-sonnet-4, llama3:8b):"
    ).ask()
    if not model:
        return
    submitter = questionary.text(
        "Submitter name (no spaces, alphanumeric/dash/dot/underscore):"
    ).ask()
    if not submitter:
        return
    x = questionary.text("X/Twitter handle, no @ (optional):", default="").ask()
    linkedin = questionary.text("LinkedIn slug (optional):", default="").ask()

    problem = api.get_problem(pid)
    print(f"Calling {provider}/{model}...")
    generate = get_provider(provider)
    canvas = generate(SYSTEM_PROMPT, build_user_prompt(problem), model)

    saved = save_run(pid, provider, model, canvas)
    print(f"Canvas saved to {saved}")

    if questionary.confirm("Submit to bench server?", default=True).ask():
        result = api.submit(
            pid,
            submitter,
            canvas,
            model=model,
            x=x or None,
            linkedin=linkedin or None,
            harness=f"chini-bench-cli:{system_prompt_hash()}",
        )
        score_print(result)
