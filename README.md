# CHINI-bench CLI

**Version:** 0.1.0
**Last Updated:** April 23, 2026

A standalone command-line tool for the [CHINI-bench](https://chinilla.com/bench) public AI system-design benchmark.

Models emit a Chinilla architecture as JSON. The simulator runs it through stress
scenarios. Pass or fail is mechanical. No LLM-as-judge.

This CLI lets you list problems, fetch the full prompt, run any LLM end-to-end
with your own API key, and submit the result to the public leaderboard, without
any copy-paste.

## Features

- **List** every benchmark problem with score and submission count
- **Prompt** prints the full prompt for a given problem (pipe to any tool)
- **Submit** a CanvasState JSON file you already produced (any model, any way)
- **Run** end-to-end against your own OpenAI, Anthropic, or Ollama key
- **Interactive menu** (questionary) for guided use, no flags to remember
- Local result archive in `data/runs/` so you never lose a canvas

## Installation

Clone and install in editable mode:

```bash
git clone https://github.com/collapseindex/chini-bench-cli.git
cd chini-bench-cli
pip install -e .
```

Or just run from the repo without installing:

```bash
python -m chini_bench --help
```

## Quick Start

Interactive menu (recommended for first time):

```bash
chini-bench
```

End-to-end run with your own OpenAI key:

```bash
export OPENAI_API_KEY=sk-...
chini-bench run chini-001-url-shortener --provider openai --model gpt-4o-mini --as alex
```

Just fetch a prompt and pipe it somewhere:

```bash
chini-bench prompt chini-002-checkout > prompt.txt
```

Submit a canvas you already have:

```bash
chini-bench submit chini-002-checkout --file canvas.json --as alex
```

## Commands

| Command | What it does |
|---------|--------------|
| `chini-bench` | Launch interactive menu |
| `chini-bench list` | List all problems with current scores |
| `chini-bench prompt <id>` | Print the full prompt for a problem |
| `chini-bench submit <id> --file canvas.json --as <name>` | Submit a CanvasState file |
| `chini-bench run <id> --provider <p> --model <m> --as <name>` | Generate + submit end-to-end |

Run `chini-bench <command> --help` for full options.

## Configuration

| Env var | Purpose | Default |
|---------|---------|---------|
| `CHINI_BENCH_URL` | Bench server base URL | `https://chinilla.com` |
| `OPENAI_API_KEY` | For `--provider openai` | none |
| `ANTHROPIC_API_KEY` | For `--provider anthropic` | none |
| `OLLAMA_HOST` | For `--provider ollama` | `http://localhost:11434` |

## Privacy & Control

- **Your API key never leaves your machine.** The CLI calls the model provider
  directly from your local process.
- **Only the resulting CanvasState JSON** is sent to the bench server (plus
  your chosen submitter name).
- **No telemetry, no tracking, no account.** Everything runs locally.
- **Submissions show as `community:<your-name>`** on the public leaderboard.

## License

MIT. See [LICENSE](LICENSE).

## Changelog

### v0.1.0 (2026-04-23)
- Initial release: list, prompt, submit, run, interactive menu
- Providers: OpenAI, Anthropic, Ollama
