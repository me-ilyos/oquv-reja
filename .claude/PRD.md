# PRD: Oquv Reja Parser

This is the product requirements document — what the tool does, who it's for, and where it's headed. For how to write code against it, see `CLAUDE.md`. For current implementation state, see `status.md`.

## Project Overview

A backend system accepts university curriculum plans (*oquv reja*) issued in Excel by the Ministry of Higher Education and Science. Automates work departments previously did by extracting following data:

- Major information like: major code, duration, title, start date. The start date format is "2024/2025" that means first study year is 2024/2025.

- Mandatory courses: code, classroom hours ("Auditoriya mashgulotlari") - Lecture ("Maruza"), Practice ("Amaliy mashgulotlar"), Seminar ("Seminar"), Lab ("Laboratoriya"), Course work ("Kurs ishi").

- Selective courses and the same information as in mandatory courses. For one slot multiple courses. The total classroom hours are the same but the type might be different: in some choices there are lecture hours but other choices may have only practice lessons.

- Credits and credit distribution if the course spans multiple semesters. Each study season has 2 semesters. Total hoours per week for the course.

By extracting above data we will be able to:

- calculate total available teaching hours.
- distributing them across professors, thus we know whether a professors has enough hours.
- splitting multi-semester course's classroom hours proportionally per semester.
- create course document templates pre-filled with per-semester hour breakdowns for professors.

**Users:** Department heads at Uzbek universities, professors

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
| — Laboratoriya | Lab work |
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

## Excel Input Format

The parser expects the standardized Ministry curriculum `.xlsx` files. Key structural assumptions:

### Metadata region (rows 1–15)
- Metadata is found by keyword search, not by fixed cell position.
- `"Ta'lim yo'nalishi:"` (or the substring `"nalishi:"`) → direction cell containing `"CODE - Name"`. In some files, the code and name are split across two vertically adjacent rows; the parser checks the cell below if no digit code is found.
- `"quv yili"` → academic year in `"YYYY/YYYY"` format.
- `"Akademik daraja"` → degree type (value after `" - "`).
- `"muddati"` → program duration.
- `"shakli"` → study format.

### Course data region
- Section `1.00` marks the start of mandatory courses (majburiy fanlar).
- Section `2.00` or a row containing `"Jami:"` ends the section.
- Course rows have a dotted number (e.g. `1.01`, `1.02.1`) in the number column.
- **Column positions vary between files** due to merged cells. The parser detects them dynamically — never hardcode column indices.

### Header region for hour columns
- A row containing `"soat"` (hours) indicates the total-hours column.
- A row containing `"auditoriya"` indicates the classroom-hours column.
- The row immediately below the auditoriya header contains subcategory labels (`Ma'ruza`, `Amaliy`, `Laboratoriya`, `Seminar`, `Kurs ishi`), matched by normalized substrings (all non-alpha chars stripped).

## Output Format

Each `.md` file contains:

```
# Oquv Reja: {program name}

**Akademik daraja:** {degree}
**O'qish muddati:** {duration}
**Ta'lim shakli:** {study format}

## Majburiy Fanlar (Core Courses)

| # | Code | Name | Hours | Credits | Classroom | Lecture | Practice | Lab | Seminar | Course Proj |
|---|------|------|-------|---------|-----------|---------|----------|-----|---------|-------------|
| ...rows... |

---
**O'quv yili:** {start year}
```

## Users & core flows
- Department heads uploads an .xlsx plan → gets validation report → data is stored.
- Frontend queries courses by program/semester.
- Report tool exports a program's full 4-year.
- Professor can generate reports, documents with prefilled data 

