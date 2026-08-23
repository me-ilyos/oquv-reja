# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It covers how to write code for this project. For product/domain background (what the tool does, glossary, Excel format, output format, roadmap), see `PRD.md`. For current implementation state, see `status.md`.

## Commands

```bash
# Parse all files in sources/ (parser is a package; run as a module)
python -m parser.main

# Parse specific file(s)
python -m parser.main sources/mmt_23.xlsx
python -m parser.main sources/mmt_23.xlsx sources/60110100_ppd.xlsx

# Import parsed curricula into the Django DB
python manage.py import_reja sources/mmt_23.xlsx
python manage.py import_reja sources/mmt_23.xlsx --replace

# Install dependencies
pip install -r requirements.txt

# Format code
ruff format .

# Lint
ruff check .
ruff check --fix.
```

## Linting & Formatting

Tool: ruff. Config lives in pyproject.toml
(line-length 88; rules E, F, W, I).

Always run ruff format . before committing. If ruff and a hand-written style
choice conflict, ruff wins — don't use # fmt: skip to preserve alignment.

## Tech Stack

- **Python 3.10+** (uses lowercase `tuple[...]` type hints)
- **openpyxl** — reads `.xlsx` files with `data_only=True` (formulas resolve to cached values)
- **Standard library only** otherwise (`re`, `pathlib`)
- **Django** for the backend
- **Frontend** - template files with HTML, CSS. For working with tables and dynamic actions HTMX and Alpine JS

## Architecture rules
- One module = one responsibility. New concern → new file, not a new section
in an existing file.


## Code conventions
- Full type hints on all public functions. No Any in signatures.
- Functions under ~40 lines; split otherwise.
- Names over comments. Comments only for "why" (Excel-format quirks, non-obvious decisions), never for "what".

## Git rules
- Never commit to main. One branch per task: feat/, fix/, refactor/.
- Commit after each verified checkpoint (tests green).
- Message format: type(scope): imperative summary of the change, under 72 chars.
  Add a body explaining WHY when the reason isn't obvious.
- Never `git add .` or `git add -A`. Run `git status`, then add named files only.
- Never push, merge, rebase, or force-push. Ever. I do those myself.
- Never commit commented-out code — delete it, git history keeps it.

## Rules
- After finishing a task, explain what you changed and why in 5 sentences max.