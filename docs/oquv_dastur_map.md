# O'quv Dastur (Course Syllabus) DOCX Map

Structural reference for generating and pre-filling the O'quv Dastur `.docx` document. Based on analysis of a real document (`Kiberxavfsizlik_asoslari_fan_dasturi_ATDT.docx`).

The platform **generates** this document with course metadata pre-filled. Teachers fill in the content sections (topics, descriptions, references). This map defines what to pre-fill and what to leave empty.

---

## 1. Document Structure Overview

The document has three top-level regions:

```
┌──────────────────────────────────────────────┐
│  COVER PAGE                                  │  Paragraphs + 1 small table
│  Title, approval block, field codes          │
├──────────────────────────────────────────────┤
│  MAIN TABLE                                  │  1 large table (~98 rows)
│  Sections 1–6: course info, lessons, tasks   │
├──────────────────────────────────────────────┤
│  FOOTER TABLE                                │  1 table (~24 rows)
│  Sections 7–10: methods, grading, references │
└──────────────────────────────────────────────┘
```

In the DOCX XML, the body contains:
- ~24 paragraphs (cover page text)
- Table 1: approval stamp (1 row, skip)
- Table 2: main content (sections 1–6, ~98 rows)
- Table 3: footer content (sections 7–10, ~24 rows)

---

## 2. Cover Page (Paragraphs)

These are standalone paragraphs before the main table. The platform pre-fills all of them.

| Order | Content | Pre-fill source | Example |
|---|---|---|---|
| 1 | University name | Hardcoded | `TURAN INTERNATIONAL UNIVERSITY` |
| 2 | *(approval table — skip)* | | |
| 3 | **Course title** (bold, centered) | O'quv Reja → course title | `KIBERXAVFSIZLIK ASOSLARI` |
| 4 | "FANINING O'QUV DASTURI" | Hardcoded | |
| 5 | Study format label | O'quv Reja → ta'lim shakli | `(kunduzgi ta'lim uchun)` |
| 6 | **Bilim sohasi** with code | DB lookup from major code | `600000 – Axborot-kommunikatsiya texnologiyalari` |
| 7 | **Ta'lim sohasi** with code | DB lookup from major code | `610000 – Axborot-kommunikatsiya texnologiyalari` |
| 8 | **Ta'lim yo'nalishi** with code | O'quv Reja → major code + title | `60610800 – Axborot texnologiyalarining dasturiy ta'minoti` |
| 9 | City and year | Hardcoded / config | `Namangan – 2026` |
| 10 | Department attribution | Platform → department name | `Mazkur o'quv dasturi ... kafedrasi tomonidan taqdim etilgan` |
| 11 | Author (Tuzuvchi) | **Teacher fills** | |
| 12 | Reviewers (Taqrizchilar) | **Teacher fills** | |

---

## 3. Main Table — Section 1: Fan ma'lumotlari (Course Info)

This is the core metadata table the platform pre-fills entirely. It occupies rows 0–6 of the main table.

### Row layout:

```
Row 0:  "1."  |  "Fan ma'lumotlari"
        ──────┼─────────────────────────────────────────────────────────
Row 1:  Fan/modul kodi     │ O'quv yili      │ Semestr    │ ECTS-Kreditlar
        {course_code}      │ {academic_year}  │ {semester} │ {credits}
        ──────┼─────────────────────────────────────────────────────────
Row 2:  Fan/modul turi     │ Ta'lim tili      │ Tartib raqami    │ Haftadagi soatlari
        {Majburiy/Tanlov}  │ {O'zbek}         │ {code – order}   │ {weekly_hours}
        ──────┼─────────────────────────────────────────────────────────
Row 3:  Fanning nomi       │ Jami yuklama     │ Auditoriya jami – {N} soat   │ Mustaqil  │ Kurs ishi
        {course_title}     │ (soat)           │ shundan:                     │ ta'lim    │
        ──────┼             ┼──────────────────┼──────────────────────────────┼           │
Row 4:  (merged↑)          │ (merged↑)        │ Ma'ruza │ Amaliy │ Lab-ya   │ (merged↑) │ (merged↑)
        ──────┼─────────────┼──────────────────┼─────────┼────────┼──────────┼───────────┼──────────
Row 5:  (empty, span=3)    │ {total_hrs}      │{lec_hrs}│{pra_hr}│{lab_hrs} │{indep_hrs}│ {- or KI}
```

### Pre-fill field mapping:

| Cell | Label | Source | Notes |
|---|---|---|---|
| R1.C0 | Fan/modul kodi | O'quv Reja → course code | e.g., `KIBAS1906` |
| R1.C1 | O'quv yili | O'quv Reja → academic year | e.g., `2026-2027`. If multi-year, comma-separated. |
| R1.C2 | Semestr | O'quv Reja → semester number(s) | e.g., `7`. If multi-semester, comma-separated. |
| R1.C3 | ECTS - Kreditlar | O'quv Reja → credits for this semester | Per-semester credits, not total. |
| R2.C0 | Fan/modul turi | Derived from section | `Majburiy` or `Tanlov` |
| R2.C1 | Ta'lim tili | Config / hardcoded | `O'zbek` (could be configurable) |
| R2.C2 | O'quv rejadagi tartib raqami | O'quv Reja → major code + order number | e.g., `60610100 – 1.19` |
| R2.C3 | Haftadagi dars soatlari | O'quv Reja → weekly hours for this semester | e.g., `6` |
| R3.C0 | Fanning nomi | O'quv Reja → course title | Spans 3 grid columns, merged vertically with R4–R5 |
| R3.C1 | Jami yuklama (soat) | Label only | Value goes in R5 |
| R3.C2 | Auditoriya mashg'ulotlari jami | Computed | `Auditoriya mashg'ulotlari jami – {N} soat, shundan:` |
| R4.C2–C4 | Ma'ruza / Amaliy / Lab-ya | Labels | Only include columns for hour types that exist (>0) |
| R5.C1 | Total hours value | O'quv Reja → total hours | e.g., `180` |
| R5.C2 | Lecture hours | O'quv Reja → ma'ruza hours | e.g., `24` |
| R5.C3 | Practice hours | O'quv Reja → amaliy hours | e.g., `24` |
| R5.C4 | Lab hours | O'quv Reja → lab hours | e.g., `24`. Omit column if 0. |
| R5.C5 | Independent study hours | O'quv Reja → mustaqil ta'lim | e.g., `108` |
| R5.C6 | Course project | O'quv Reja → kurs ishi | `-` if none, `Kurs ishi` if present |

> **Note on Seminar:** the hour-type sub-headers (Row 4) show only the types that apply. This example has Ma'ruza, Amaliy, Lab-ya (no Seminar). If a course has Seminar hours instead of Lab, the column should say `Seminar`. The columns are dynamic based on which hour types are non-zero.

---

## 4. Main Table — Sections 2–4 (Teacher-Filled)

These sections are **not pre-filled** by the platform. The teacher writes the content.

| Section | Row | Title | Content |
|---|---|---|---|
| **2** | R7 | Fanning mazmuni | Course purpose and objectives (free text) |
| **3** | R10 | Boshlang'ich bilimlar | Prerequisite courses (teacher lists them) |
| **4** | R15 | Ta'lim natijalari (TN) | Learning outcomes: TN1, TN2, ... (teacher writes) |

The platform generates these section headers with empty content rows.

---

## 5. Main Table — Section 5: Fan mazmuni va mashg'ulotlar (Lesson Tables)

This is the largest section. The platform **pre-generates the row structure** — the correct number of empty rows per hour type. The teacher fills in the topic descriptions.

### Structure:

```
Row N+0:  "5."  |  "Fan mazmuni va mashg'ulotlar shakli:"  |  "Soat"

Row N+1:  ""    |  "Ma'ruza (M)"                           |  {total_lecture_hours}
Row N+2:  "M1"  |  {empty — teacher fills}                 |  2
Row N+3:  "M2"  |  {empty}                                 |  2
  ...           (one row per lesson: total = lecture_hours / 2)

Row M+0:  ""    |  "Amaliy mashg'ulot (A)"                 |  {total_practice_hours}
Row M+1:  "A1"  |  {empty}                                 |  2
Row M+2:  "A2"  |  {empty}                                 |  2
  ...           (one row per lesson: total = practice_hours / 2)

Row L+0:  ""    |  "Laboratoriya mashg'ulot (L)"           |  {total_lab_hours}
Row L+1:  "L1"  |  {empty}                                 |  2
  ...           (one row per lesson: total = lab_hours / 2)

[Seminar section if applicable, same pattern with "S1", "S2", ...]
```

### Pre-fill rules:

| What | Value | Source |
|---|---|---|
| Sub-section headers | `Ma'ruza (M)`, `Amaliy mashg'ulot (A)`, `Laboratoriya mashg'ulot (L)`, `Seminar (S)` | Hardcoded labels |
| Total hours per sub-section | The number in the last column of the header row | O'quv Reja |
| Number of lesson rows | `hours / 2` per type | Computed |
| Row labels | `M1`, `M2`, ..., `A1`, `A2`, ..., `L1`, `L2`, ... | Sequential |
| Hours per lesson | Always `2` | Hardcoded |
| Topic/description cell | **Empty** | Teacher fills |

**Only include sub-sections for hour types that have non-zero hours.** If a course has no lab hours, omit the Laboratoriya section entirely.

---

## 6. Main Table — Section 6: Mustaqil ta'lim (Independent Study)

Same pattern as Section 5 but for independent study tasks.

```
Row:  "6."  |  "Mustaqil ta'lim topshiriqlari*"  |  {total_independent_hours}
Row:  "1"   |  {empty — teacher fills}            |  {hours_per_task}
Row:  "2"   |  {empty}                            |  {hours_per_task}
  ...
```

### Pre-fill rules:

| What | Value |
|---|---|
| Total hours | From O'quv Reja → mustaqil ta'lim |
| Number of rows | `independent_hours / hours_per_task` |
| Hours per task | Typically `4` (observed), but may need to be configurable |
| Row labels | `1`, `2`, `3`, ... (plain numbers, not prefixed) |
| Description cells | **Empty** — teacher fills |

---

## 7. Footer Table — Sections 7–10 (Teacher-Filled)

A separate table after the main table. The platform generates the section headers only. All content is teacher-filled.

| Section | Title | Content |
|---|---|---|
| **7** | Ta'lim texnologiyalari va metodlari | Teaching methods (free text) |
| **8** | Talabalar tomonidan kreditlarni olish uchun talablar | Credit requirements (free text) |
| **9** | Talabalar bilimini baholash mezoni | Grading criteria (free text) |
| **10** | Foydalanilgan adabiyotlar | References — sub-sections: Asosiy adabiyotlar, Qo'shimcha adabiyotlar, Axborot manbalari |

---

## 8. Generation Summary

What the platform generates vs. what the teacher fills:

```
PLATFORM PRE-FILLS:                      TEACHER FILLS:
─────────────────                        ─────────────
Cover page:                              Cover page:
  ✓ University name                        ✗ Author (Tuzuvchi)
  ✓ Course title                           ✗ Reviewers (Taqrizchilar)
  ✓ Study format label
  ✓ Bilim sohasi + code                  Section 2: Course description
  ✓ Ta'lim sohasi + code                 Section 3: Prerequisites
  ✓ Ta'lim yo'nalishi + code             Section 4: Learning outcomes (TN1–TNx)
  ✓ City + year
  ✓ Department attribution               Section 5: Lesson topics
                                            (rows are pre-created, content empty)
Section 1: Full course info table
  ✓ Course code                           Section 6: Independent study tasks
  ✓ Academic year                           (rows are pre-created, content empty)
  ✓ Semester
  ✓ Credits                               Section 7: Teaching methods
  ✓ Course type (Majburiy/Tanlov)         Section 8: Credit requirements
  ✓ Order number                          Section 9: Grading criteria
  ✓ Weekly hours                          Section 10: References
  ✓ Course title
  ✓ Hours breakdown
  ✓ Kurs ishi indicator

Section 5: Lesson table structure
  ✓ Sub-section headers + totals
  ✓ Row labels (M1, A1, L1...)
  ✓ "2" in hours column

Section 6: Independent study structure
  ✓ Row count + labels
  ✓ Hours per task
```

---

## 9. Conditional Sections

The document structure adapts to the course:

| Condition | Effect |
|---|---|
| No lecture hours | Omit `Ma'ruza (M)` sub-section in Section 5 |
| No practice hours | Omit `Amaliy mashg'ulot (A)` sub-section |
| No lab hours | Omit `Laboratoriya mashg'ulot (L)` sub-section |
| No seminar hours | Omit `Seminar (S)` sub-section |
| No course project | Row 5 last cell = `-` instead of `Kurs ishi` |
| Multi-semester course | Comma-separated semesters and years in Section 1 |
| Seminar label in hour table | Use `Seminar` column header instead of `Lab-ya` (Row 4 adapts) |