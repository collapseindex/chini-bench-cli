# Security Policy

**Project:** chini-bench-cli
**Version:** 0.6.0
**Last updated:** April 24, 2026
**Contact:** squeak@chinilla.com

## Reporting a vulnerability

Email **squeak@chinilla.com** with the subject line `chini-bench-cli security`.

Please include:

- A description of the issue and its impact.
- Steps to reproduce, or a proof-of-concept.
- The version (`chini-bench --version`) and the commit hash if you have it.
- Any logs or canvas JSON involved (redact your API keys).

**Please do not open a public GitHub issue first.** I will reply within 7 days.

If the report is a real, fixable vulnerability I will:

1. Acknowledge receipt within 7 days.
2. Confirm the issue and ship a fix in the next patch release.
3. Credit the reporter in the release notes (unless asked not to).

There is no bug bounty.

## Supported versions

Only the latest minor version receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.6.x   | Yes       |
| 0.5.x   | No (please upgrade) |
| < 0.5   | No        |

## Threat model

The CLI is intentionally minimal. The full attack surface is:

1. Read environment variables for API keys.
2. Make HTTPS calls to **one** model provider you choose at runtime.
3. POST a JSON canvas to the bench server (`https://chinilla.com/api/bench/*`)
   when, and only when, you explicitly run `submit` or `run`.

There is no daemon, no background process, no auto-update, no telemetry, no
account system, no credential cache.

### What a malicious model could do

The CLI parses model output as JSON only (`json.loads`, never `eval`). A model
that returns malformed or oversized output should fail closed: a parse error,
a schema validation rejection, or a 4xx from the bench server. If you find an
output payload that escapes those checks, report it.

### What a compromised PyPI package or upstream dep could do

The dependency surface is small (`requests`, `questionary`, `pydantic`, plus
the optional provider SDKs you opt into). `pip-audit` runs against
`requirements.txt` on every release. If you find a transitive dep with a known
CVE that we missed, report it.

### What is explicitly out of scope

- Issues that require attacker control of your local machine (env vars,
  filesystem, terminal). If they have your `OPENAI_API_KEY` they have already
  won; the CLI is not a defense layer.
- Bench server vulnerabilities (`https://chinilla.com/api/bench/*`). Report
  those to the same address but mark them as "bench server" in the subject;
  they are tracked in a separate repository.
- Rate-limit bypass against model providers. You are responsible for your own
  API quota.
- Cosmetic issues, broken links, typos. Open a normal GitHub issue.

## Security audit

Automated checks run on every release. Reproduce locally:

```bash
pip install bandit pip-audit
bandit -r chini_bench
pip-audit -r requirements.txt
```

Latest results (v0.6.0, 2026-04-24, 864 LOC):

| Tool | Result |
|------|--------|
| `bandit -r chini_bench` | 0 issues, all severities |
| `pip-audit -r requirements.txt` | No known vulnerabilities |

## Design choices that limit risk

- **No `subprocess`, `os.system`, `eval`, `exec`, `pickle`, or `shell=True`**
  anywhere in the package.
- **No SSL verification disabled.** All `requests` calls use defaults plus an
  explicit 60s timeout.
- **API keys come from environment variables only.** The CLI never writes them
  to disk, never logs them, and never sends them to anything except the
  matching provider's official SDK or REST endpoint.
- **LLM output is parsed as JSON only** (`json.loads`), never `eval`'d.
- **The bench server validates everything** the CLI sends (submitter regex,
  model regex, canvas schema). The CLI is not a trusted client; the server
  treats it as untrusted input.
- **No telemetry.** The only outbound calls are to your chosen provider and to
  `https://chinilla.com/api/bench/*` when you explicitly invoke `submit` or
  `run`.
- **Local result archive in `data/runs/`** stores only the canvas, the
  submitter handle, and the bench server response. No keys, no env, no PII.

## Hash verification

You can verify that your installed CLI's harness prompts have not been
modified upstream:

```bash
python -c "from chini_bench.prompt import system_prompt_hash, system_prompt_hash_reflex; \
  print('single-shot:', system_prompt_hash()); \
  print('reflex:    ', system_prompt_hash_reflex())"
```

Canonical hashes for v0.6.0:

- `chini-bench-cli:06d0ffb42f19`
- `chini-bench-reflex:42769353289d`

A mismatch means either the package on your machine has been modified, or you
have intentionally edited `SYSTEM_PROMPT` (in which case your runs will surface
as `custom` on the leaderboard, not `default`, which is the intended behavior).
