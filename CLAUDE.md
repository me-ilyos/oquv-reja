# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Parses Uzbek university curriculum plans (*oquv reja*) issued in Excel by the Ministry of Higher Education and Science. Automates work departments previously did by hand: calculating total available teaching hours, distributing them across professors, and splitting multi-semester courses proportionally per semester.

**Users:** Department heads at Uzbek universities. The script is the backend of a planned UI — department heads will eventually run everything through an interface.

**Trigger:** On demand — whenever the department head needs to recalculate workloads or generate updated course templates.

**Output is used for:**
- Professor hour-load tables (who teaches what, and how many hours)
- Course document templates pre-filled with per-semester hour breakdowns for professors
- A future database powering the department management UI

**Scope:** Handles the standardized curriculum Excel format shared by all Uzbek universities.

## Glossary

**Oquv reja** — The official Excel document specifying the full curriculum for a degree program. Covers all courses, their hours, credits, and weekly schedule across every semester.

**Course categories**
| Uzbek term | English | Notes |
|---|---|---|
| Majburiy fanlar | Mandatory courses | Fixed required courses for the degree |
| Tanlov fanlar | Selective courses | Slots where one course is chosen from a sub-list; same hours/credits structure as mandatory |

**Hour structure (per course)**
| Uzbek term | English |
|---|---|
| Auditoriya mashg'ulotlari | Classroom hours (total contact time) |
| — Maruza | Lecture |
| — Amaliy / Amaliy mashg'ulot | Practice session |
| — Seminar | Seminar |
| — Kurs ishi | Course project |
| Mustaqil ta'lim | Individual / self-study hours |

**Credits:** 1 credit = 30 hours total (classroom + individual).

**Semester:** exactly 15 weeks. Each course states its weekly contact hours, from which per-semester totals are derived.

**Program metadata in the oquv reja**
| Field | Example values |
|---|---|
| Major code | 60110200 |
| Degree type | Bakalavr (Bachelor), Magistr (Master) |
| Program duration | 4 yil (4 years) |
| Study format | Kunduzgi (morning/full-time), Sirtqi (evening/part-time) |

## Commands

```bash
# Run the parser
python main.py

# Install dependencies
pip install -r requirements.txt
```

No test suite or linter is configured.

## Architecture

This is a single-file ETL script (`main.py`) that reads Uzbek academic plan spreadsheets from `sources/*.xlsx` and writes one Markdown file per spreadsheet to `output/`.

### Data flow

```
sources/*.xlsx  →  main.py  →  output/*.md
```

Each output filename is built from the extracted program name (CamelCase) + direction code + start year, e.g. `MaktabgachaTalim_60110200_2023.md`.

## Dev log

Task history is tracked in `DEVLOG.md`.
