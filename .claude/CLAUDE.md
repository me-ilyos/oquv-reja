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

## Git
- Never commit to main. Branch per task: feat/, fix/, refactor/.
- Commit after each verified checkpoint. Format: type(scope): imperative summary — why, not what, under 72 chars.
- Never git add . — add named files only; review git status first.
- Never push, merge, or force-push without my explicit instruction.
- Never commit: source .xlsx files over 1MB, generated output .md, credentials, commented-out code.