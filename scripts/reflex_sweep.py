"""Reflexion sweep: run `chini-bench reflex run` on every problem.

Skips the menu and parser overhead by calling cmd_reflex_run directly.
Writes a small per-run summary to stdout so you can `tee` it.
"""
from __future__ import annotations

import argparse
import sys
import time

from chini_bench import api
from chini_bench.cli import cmd_reflex_run


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="openrouter")
    p.add_argument("--model", default="anthropic/claude-sonnet-4.6")
    p.add_argument("--as", dest="submitter", default="alex")
    p.add_argument("--only", default=None, help="comma-separated problem ids; default = all")
    p.add_argument("--sleep", type=float, default=2.0, help="seconds between runs to be nice")
    args = p.parse_args()

    problems = api.list_problems()
    ids = [pp["id"] for pp in problems]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        ids = [i for i in ids if i in wanted]

    print(f"[sweep] running {len(ids)} problems on {args.provider}/{args.model}", file=sys.stderr)
    failures: list[tuple[str, str]] = []
    for i, pid in enumerate(ids, 1):
        print(f"\n[sweep] [{i}/{len(ids)}] {pid}", file=sys.stderr)
        ns = argparse.Namespace(
            problem_id=pid,
            provider=args.provider,
            model=args.model,
            submitter=args.submitter,
            dry_run=False,
        )
        try:
            cmd_reflex_run(ns)
        except (RuntimeError, ValueError) as e:
            print(f"[sweep]   FAILED: {e}", file=sys.stderr)
            failures.append((pid, str(e)))
        time.sleep(args.sleep)

    print("\n[sweep] done.", file=sys.stderr)
    if failures:
        print(f"[sweep] {len(failures)} failures:", file=sys.stderr)
        for pid, msg in failures:
            print(f"  - {pid}: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
