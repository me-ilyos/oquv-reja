# O'quv Reja Excel Document Map

Structural reference for parsing the O'quv Reja `.xlsx` files. Based on analysis of 8 real files across different majors, durations (3–4 years), academic years (2023–2026), and universities.

**Rule: always parse the first sheet only.**

---

## 1. Overall Layout

The sheet has three vertical zones, always in this order:

```
┌─────────────────────────────────────────────┐
│  ZONE A: Header / Program Metadata          │  rows ~1–8
├─────────────────────────────────────────────┤
│  ZONE B: Academic Calendar Table            │  rows ~9–22  (skip — not parsed)
│  "I. O'QUV JARAYONI JADVALI"               │
├─────────────────────────────────────────────┤
│  ZONE C: Course Table                       │  rows ~23–end
│  "II. O'QUV REJASI"                        │
└─────────────────────────────────────────────┘
```

Exact row numbers shift between files. Never hardcode them — locate each zone by its landmark text.

---

## 2. Zone A: Program Metadata

### 2.1. How to find metadata

Metadata fields are scattered across the first ~8 rows. There is **no fixed row or column**. Both the row and column positions vary significantly across files:

| Field | Column observed at | Row observed at |
|---|---|---|
| `Akademik daraja` | BR-CC (≈ C70-C81) | R2, R3, R5 |
| `O'qish muddati` / `O'quv muddati` | BR-CC (≈ C70-C81) | R3, R4, R6 |
| `O'qish shakli` (study system) | BR-CC (≈ C70-C81), same column as `Ta'lim shakli` | one row **above** `Ta'lim shakli` |
| `Ta'lim shakli` | BR-CC (≈ C70-C81) | R5, R6, R7 |
| `Ta'lim yo'nalishi` | C17, C19, C35 | R3, R5 |
| `O'quv yili` | C30, C35, C75, C80, C81 | R4, R7 |

**Strategy:** scan every cell in rows 1–10. For each non-empty cell, check if its text contains one of the metadata keywords. Extract the value from the same cell (after the `-` or `:` separator).

### 2.2. Field formats and extraction

**Akademik daraja**
- Text pattern: `Akademik daraja - BAKALAVR` or `Akademik daraja - MAGISTR`
- Extract: everything after the `-` separator, stripped and uppercased.

**O'qish muddati** (also appears as `O'quv muddati`)
- Text patterns: `O'qish muddati - 4 yil`, `O'qish muddati -4 yil`, `O'quv muddati - 4 yil`
- Extract: the integer before `yil`. Possible values: `3`, `4`, `5`.
- This value determines semester count: 3 years = 6 semesters, 4 years = 8, 4.5 years = 9, 5 years = 10.

**O'qish shakli** (study system — not the same field as `Ta'lim shakli`)
- Text pattern: `O'qish shakli - Kredit-modul`
- Values observed: `Kredit-modul` (14 files), `kredit tizimi` (3), `Kredit modul` (1, no hyphen).
- Sits one row **above** `Ta'lim shakli`, same column. Every sheet has both
  cells, and both contain the bare substring `shakli` — matching on `shakli`
  alone hits this cell first and silently produces the wrong `talim_shakli`
  value. The label match must use the full two-word needle `ta'lim shakli`.
- This field is not currently stored; it exists only to explain the collision.

**Ta'lim shakli**
- Text pattern: `Ta'lim shakli - kunduzgi`
- Extract: value after `-`. One of: `kunduzgi`, `kechgi`/`kechki`, `sirtqi` (case varies).
- Must match the full two-word label `ta'lim shakli`, not the bare `shakli` —
  see `O'qish shakli` above.

**Ta'lim yo'nalishi**
- Two formats exist:
  - Separate label and value: label cell = `Ta'lim yo'nalishi:`, value in a nearby cell below or beside → `60310200 - Xalqaro munosabatlar`
  - Combined: `Ta'lim yo'nalishi: 60110500 - Boshlang'ich ta'lim` (label + value in one cell)
- Extract: the 8-digit code and the title after the `–` or `-` separator.

**O'quv yili**
- Text patterns: `2025-2026 o'quv yili`, `2023/2024 o'quv yili`
- Extract: the year range (e.g., `2025-2026`). Separator may be `-` or `/`.

### 2.3. Metadata search pseudocode

```
for row in 1..10:
    for col in 1..max_col:
        text = cell(row, col).lower().strip()
        if "akademik daraja" in text → parse degree type
        if "muddati" in text       → parse duration
        if "ta'lim shakli" in text  → parse study format
        if "yo'nalishi" in text     → parse major code + title
        if "o'quv yili" in text     → parse academic year
```

---

## 3. Zone B: Academic Calendar (Skip)

Starts at the row containing `I. O'QUV JARAYONI JADVALI`. Contains a visual week-by-week calendar grid. The parser does **not** need data from this zone — skip to Zone C.

---

## 4. Zone C: Course Table

### 4.1. Finding the table start

Search for the row containing `II. O'QUV REJASI` (in column 1–4). Observed at rows 23–28 depending on file. The course table header rows begin immediately after this landmark.

### 4.2. Table Header Structure

The header spans **4–6 rows** between the `II. O'QUV REJASI` landmark and the first course data row. These header rows define three column groups:

```
┌────────┬──────────┬───────────────────────────┬───────────────────────────┬──────────────────────────┬───────┐
│ T/r    │ Fan kodi │ Fan nomi                  │ Yuklama (soatlarda)       │ Soatlar taqsimoti        │ Kredit│
│ (order)│ (code)   │ (title)                   │ (hours workload)          │ (semester distribution)  │ (sum) │
├────────┼──────────┼───────────────────────────┼───────────────────────────┼──────────────────────────┼───────┤
│        │          │                           │ Umumiy │ Audit. │ Mustaqil│ Weekly hrs │ Credits     │       │
│        │          │                           │ hajmi  │ mashg. │ ta'lim  │ per sem.   │ per sem.    │       │
│        │          │                           │        │        │         │            │             │       │
│        │          │                           │ soat│% │Jami│...│         │ 1│2│3│...│N│ 1│2│3│...│N │       │
└────────┴──────────┴───────────────────────────┴────────┴────────┴─────────┴────────────┴─────────────┴───────┘
```

### 4.3. Locating Columns by Label

**Do not hardcode column indices.** Find each column by searching the header rows for its label text.

#### Fixed columns (always at the start)

| What | Identifying logic |
|---|---|
| Order number | Column 1 (always) |
| Course code | Column 2 (always) |
| Course title | Column 3 (always) |

> Exception: in some files (Boshlangich), the code is at C2 but the *Jami* column starts later (C34 instead of C28). The gap between C3 and the hours columns varies.

#### Hours columns — find by label

Search the header rows for these labels. The **order of these columns varies between files.**

| Label to search | Normalized key | Spelling variants observed |
|---|---|---|
| `Jami` | `classroom_total` | `Jami` (always consistent) |
| `Ma'ruza` | `lecture` | `Ma'ruza` (consistent) |
| `Amaliy` | `practice` | `Amaliy`, `Amaliy ` (trailing space) |
| `Laboratoriya` | `lab` | `Laboratoriya`, `Labaratoriya` (common typo), `Laboratoriya ` |
| `Seminar` | `seminar` | `Seminar` (consistent) |
| `Kurs ishi` | `course_project` | `Kurs ishi`, `Kurs loyihasi (ishi)`, `Kurs ishi\n/loyiha` |
| `Mustaqil ta'lim` | `independent` | `Mustaqil ta'lim` (consistent) |
| `Umumiy yuklama` | `total_hours` | `Umumiy yuklamaning hajmi`, `Umumiy yuklama hajmi` |

**Observed column orderings:**

```
Layout A (most files):   Jami → Ma'ruza → Amaliy → Labaratoriya → Seminar → Kurs ishi
Layout B (Boshlangich):  Jami → Ma'ruza → Amaliy → Seminar → Laboratoriya → Kurs ishi
Layout C (Turizm):       Jami → Ma'ruza → Amaliy → Laboratoriya → Seminar → Kurs loyihasi
```

Not all columns are present in every file. A major with no lab courses may still have the `Laboratoriya` header but all values will be 0 or empty.

#### Column spacing

The gap between hour-type columns is **not consistent.** In most 2025-26 files, columns are spaced 3 apart (C28, C31, C34, C37...). In Turizm (2023-24), they're spaced 2 apart (C28, C30, C32, C34...). In Boshlangich, they're spaced 5 apart (C34, C39, C44, C49...).

**Always search by label, never by offset.**

#### Semester columns

After the hour-type columns, there are two parallel semester-distribution sections:

1. **Weekly hours per semester** — label: `Semestrdagi haftalar soni` or `Kurslardagi haftalar soni`
2. **Credits per semester** — label: `Semestrdagi kreditlar taqsimoti` or similar

Each section has N sub-columns numbered 1 through N, where N = total semesters:
- 3-year program → 6 semester columns
- 4-year program → 8 semester columns
- 4.5-year program → 9 semester columns
- 5-year program → 10 semester columns

**How to find semester columns:** locate the row that contains semester numbers (1, 2, 3, ..., N). These numbers appear in the header rows, directly below the `kurs` labels. Count how many consecutive semester numbers you find — this gives you both the column positions and the semester count.

> Amendment (verified against `sources/`): the N sub-columns are not always
> adjacent. Maktabgacha ta'lim (60110200, 3-year) groups them under a
> `1-kurs`/`2-kurs`/`3-kurs` row and spaces them 3 apart even within one
> group (e.g. weekly columns at 48, 51, 54, 57, 60, 63) — the same spacing
> variance §4.3 documents for the hour-type columns applies here too. Bound
> the search window by the *other* group's header column when one is known,
> not by a fixed `N`-sized guess.
>
> The same file also has a header cell typed as `Кreditlarning …` with a
> Cyrillic `К` (U+041A) instead of Latin `K` — invisible on screen, fatal to
> a plain substring search. Normalize common Cyrillic look-alikes to Latin
> before matching header labels.

The last column after all semester credits is **Jami kreditlar** (total credits).

### 4.4. Column-Number Row

Most files contain a row where the cells read `1, 2, 3, ..., 29` (numbering the logical columns). This row immediately precedes the first data row. It can serve as an anchor: the row after it is the first section marker or course row.

Observed positions: R29, R31, R33, R36. **Not present in all files.**

---

## 5. Course Rows

### 5.1. Section Markers

Courses are divided into two sections by marker rows:

| Section | Marker value in Column 1 | Label in Column 3 |
|---|---|---|
| Mandatory | `1.00`, `1.0`, `1`, `1,00`, `1,0` | `Majburiy fanlar` |
| Elective | `2.00`, `2.0`, `2`, `2,00`, `2,0`, `2.00.` | `Tanlov fanlar` / `Tanlov fanlari` |

**Detection:** read column 1, convert commas to dots, strip trailing dots, compare against `1.0`, `1.00`, `1`, `2.0`, `2.00`, `2`.

The marker row also contains **aggregate totals** for the section in the hours columns. These are summary values, not course data.

### 5.2. Mandatory Course Row

Each row below the `1.00` marker until the `2.00` marker (or until a total row) is one course:

```
C1: Order number    — e.g., 1.01, 1.02 (may use comma: 1,01)
C2: Course code     — e.g., O'YT1104, FAL1304
C3: Course title    — e.g., Falsafa
[hours columns]:    — values at the column positions found in step 4.3
[semester columns]: — weekly hours per semester, then credits per semester
[last]:             — total credits
```

**Empty cells** in hour-type or semester columns mean zero for that type/semester.

### 5.3. Elective Course Rows (Tanlov)

Elective slots have **one primary row and one or more alternative rows** immediately below:

```
R60: C1=2.01  C2=SITQ2       C3=Sohada IT texnologiyalarini qo'llash    [hours...]
R61:           C2=BSAT204     C3=Boshlang'ich sinflarda axborot texnologiyalari
R62: C1=2.02  C2=SYIT2       C3=Sohaga yo'naltirilgan ingliz tili        [hours...]
R63:           C2=KSXT204     C3=Kasbiy sohada xorijiy tillar
```

**How to identify:**
- The primary row has an order number in C1 (e.g., `2.01`).
- Alternative rows have **no value in C1**, but have a course code in C2 and a title in C3.
- The hours/credits on the primary row apply to the entire slot. Alternatives share the same total hours and credits but may have different hour-type breakdowns.
- An alternative row only has values in C2 and C3 (code and title). All hours and semester data come from the primary row.

**Grouping rule:** starting from a row with an order number in C1, collect all subsequent rows that have no C1 value — those are alternatives for the same elective slot.

### 5.4. End-of-Section and Total Rows

After the last course in each section, there are summary/total rows:

| Text in C3 | Meaning |
|---|---|
| `Jami:` or `JAMI:` | Section subtotal (mandatory courses total, or elective courses total) |
| `Malakaviy amaliyot` / `Malaka amaliyot` | Internship hours (not a course) |
| `Yakuniy davlat attestatsiyasi` / `Yakuniy davlat attestatsiyasi, BMI` | Final state attestation |
| `Hammasi` / `Hammasi ` | Grand total of all courses |

These rows should be **skipped** by the course parser. Detect them by checking if C1 is empty and C3 matches one of the above labels.

---

## 6. Variation Summary Table

| Property | Range of values | How to detect |
|---|---|---|
| Metadata column | BR-CC (≈ C70-C81) | Text search in rows 1–10 |
| `O'qish shakli` vs `Ta'lim shakli` | Both contain `shakli`; `O'qish shakli` sits one row above | Match the full two-word label `ta'lim shakli`, never the bare `shakli` |
| `II. O'QUV REJASI` row | R23 – R28 | Text search in C1–C4 |
| Hour-type header row | R26 – R31 | Search for `Ma'ruza` label |
| Column spacing | 2, 3, or 5 cols apart | Label-based lookup |
| Hour-type order | 3 known layouts (A/B/C) | Label-based lookup |
| Semester count | 6, 8, 9, 10 | Count sub-columns or derive from duration |
| Section markers | Various formatting | Normalize: comma→dot, strip dots, compare |
| Column-number row | R29 – R36 (or absent) | Row where C1=1, C2=2 or C3=2 |
| Tanlov label | `Tanlov fanlar` / `Tanlov fanlari` | Either form valid |
| Course project label | `Kurs ishi` / `Kurs loyihasi (ishi)` | Check for `kurs` keyword |
| `Laboratoriya` spelling | `Laboratoriya` / `Labaratoriya` | Check for `la` + `oratoriya` |
| `O'qish muddati` label | `O'qish muddati` / `O'quv muddati` | Check for `muddati` |
| Independent study label | `Mustaqil ta'lim` | Consistent |

---

## 7. Parsing Sequence (Recommended)

```
1. Open workbook, select first sheet.

2. METADATA PASS — scan rows 1–10, all columns:
   For each non-empty cell, match against metadata keywords.
   Extract: degree_type, duration, study_format, major_code, major_title, academic_year.
   Derive: semester_count from duration.

3. FIND COURSE TABLE — scan column 1–4 for "II. O'QUV REJASI".
   Record this row as TABLE_START.

4. FIND COLUMN POSITIONS — scan rows TABLE_START to TABLE_START+8:
   Search for hour-type labels (Jami, Ma'ruza, Amaliy, etc.).
   Search for semester numbers (1, 2, 3, ..., N) in two groups:
     - First group = weekly hours per semester
     - Second group = credits per semester
   Record each label → column index mapping.

5. FIND FIRST DATA ROW — look for the column-number row (C1=1, C2=2)
   or the section marker row (C1 matches 1.00/1.0/1).
   The first course row is the row after the 1.00 marker.

6. PARSE COURSES — iterate rows:
   If C1 matches 1.00/2.00 pattern → section marker (record section type, skip row).
   If C1 has an order number (e.g., 1.01) → primary course row.
   If C1 is empty AND C2 has a code → elective alternative row (attach to previous slot).
   If C3 matches total-row labels → skip.
   Otherwise → skip.

7. For each course row, read values at the column positions found in step 4.
```

---

## 8. Observed File Signatures

For quick reference during testing:

| File | Duration | Semesters | Hour-type order | Col spacing | Majburiy row | Tanlov row |
|---|---|---|---|---|---|---|
| XM 60310200 (25-26) | 4 yr | 8 | A (standard) | 3 | R34 | R53 |
| JI 60411100 (25-26) | 4 yr | 8 | A | 3 | R32 | — |
| XTA 60110900 (25-26) | 4 yr | 8 | A | 3 | R33 | — |
| JM 60111200 (25-26) | 3 yr | 6 | A | 3 | R30 | R52 |
| O'zb tili 60110700 (24-25) | 4 yr | 8 | A | 3 | R35 | — |
| Matematika 60540100 (24-25) | 4 yr | 8 | A | 3 | R32 | R55 |
| Turizm 61010400 (23-24) | 4 yr | 8 | C | 2 | R37 | R65 |
| Boshlangich 60110500 (23-24) | 4 yr | 8 | B (reordered) | 5 | R37 | R59 |