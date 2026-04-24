"""Argparse-based command dispatcher for `chini-bench`.

If no subcommand is given, the interactive menu is launched instead.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chini_bench import __version__, api
from chini_bench.prompt import build_full_prompt
from chini_bench.providers import get_provider
from chini_bench.runner import save_run, score_print


def cmd_list(_args: argparse.Namespace) -> int:
    problems = api.list_problems()
    if not problems:
        print("No problems available.")
        return 1
    width_id = max(len(p["id"]) for p in problems)
    print(f"{'ID'.ljust(width_id)}  {'TOP'.rjust(4)}  RUNS  TITLE")
    for p in problems:
        print(
            f"{p['id'].ljust(width_id)}  "
            f"{str(p['topScore']).rjust(4)}  "
            f"{str(p['runs']).rjust(4)}  "
            f"{p['title']}"
        )
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    problem = api.get_problem(args.problem_id)
    print(build_full_prompt(problem))
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    try:
        canvas = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Could not parse {path} as JSON: {e}", file=sys.stderr)
        return 2

    result = api.submit(
        args.problem_id,
        args.submitter,
        canvas,
        model=getattr(args, "model", None),
        x=getattr(args, "x", None),
        linkedin=getattr(args, "linkedin", None),
    )
    score_print(result)
    return 0 if result.get("passed") else 0  # exit 0 even on a fail score


def cmd_run(args: argparse.Namespace) -> int:
    problem = api.get_problem(args.problem_id)
    generate = get_provider(args.provider)

    from chini_bench.prompt import SYSTEM_PROMPT, build_user_prompt, system_prompt_hash

    print(f"Calling {args.provider}/{args.model}...", file=sys.stderr)
    canvas = generate(SYSTEM_PROMPT, build_user_prompt(problem), args.model)

    saved = save_run(args.problem_id, args.provider, args.model, canvas)
    print(f"Canvas saved to {saved}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(canvas, indent=2))
        return 0

    print("Submitting to bench server...", file=sys.stderr)
    # Auto-record the model id used so the leaderboard shows it without --model.
    # `harness` lets the server distinguish unmodified-CLI runs from forks.
    result = api.submit(
        args.problem_id,
        args.submitter,
        canvas,
        model=args.model,
        x=args.x,
        linkedin=args.linkedin,
        harness=f"chini-bench-cli:{system_prompt_hash()}",
    )
    score_print(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chini-bench",
        description="CLI for the CHINI-bench public AI system-design benchmark.",
    )
    p.add_argument("--version", action="version", version=f"chini-bench {__version__}")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="List all problems with current scores").set_defaults(
        func=cmd_list
    )

    sp = sub.add_parser("prompt", help="Print the full prompt for a problem")
    sp.add_argument("problem_id", help="Problem id, e.g. chini-001-url-shortener")
    sp.set_defaults(func=cmd_prompt)

    ss = sub.add_parser("submit", help="Submit a CanvasState JSON file you already have")
    ss.add_argument("problem_id")
    ss.add_argument("--file", "-f", required=True, help="Path to CanvasState JSON")
    ss.add_argument(
        "--as",
        dest="submitter",
        required=True,
        help="Submitter name (will appear as community:<name>)",
    )
    ss.add_argument(
        "--model",
        default=None,
        help="Optional: model id that produced this canvas (shown on leaderboard)",
    )
    ss.add_argument(
        "--x",
        default=None,
        help="Optional: your X/Twitter handle (no @)",
    )
    ss.add_argument(
        "--linkedin",
        default=None,
        help="Optional: your LinkedIn vanity slug or full /in/<slug> URL",
    )
    ss.set_defaults(func=cmd_submit)

    sr = sub.add_parser(
        "run",
        help="Generate a canvas with your own model, then auto-submit",
    )
    sr.add_argument("problem_id")
    sr.add_argument(
        "--provider",
        required=True,
        choices=["openai", "anthropic", "google", "openrouter", "ollama"],
        help="Which provider to call (key from env)",
    )
    sr.add_argument("--model", required=True, help="Model id, e.g. gpt-4o-mini")
    sr.add_argument(
        "--as",
        dest="submitter",
        required=True,
        help="Submitter name (will appear as community:<name>)",
    )
    sr.add_argument(
        "--x",
        default=None,
        help="Optional: your X/Twitter handle (no @)",
    )
    sr.add_argument(
        "--linkedin",
        default=None,
        help="Optional: your LinkedIn vanity slug or full /in/<slug> URL",
    )
    sr.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and save locally, do not submit",
    )
    sr.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        # No subcommand -> interactive menu
        from chini_bench.menu import run_menu

        return run_menu()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
