# Lab Reagent Inventory & FEFO Allocation — C11

**A menu-driven C case study for batch-wise reagent stock, expiry-aware allocation and checked file persistence.**

FEFO means **First Expiry, First Out**: issue eligible stock from the earliest-expiring batch first, not simply from the batch entered first.

> Educational inventory simulation. Use fictitious records only. The program does not establish clinical suitability, verify storage conditions or replace laboratory procedures.

## Real-life case study

A laboratory stores several batches of the same reagent with different expiry dates. Staff need to see available stock, avoid allocating expired batches, and fulfil a request without making quantities negative or silently issuing only part of a request.

The program applies a deterministic FEFO policy, displays an allocation plan, asks for confirmation, and saves all proposed deductions together through one checked data-file replacement.

## What makes this more than a basic record tracker?

- **Algorithmic allocation:** filter eligible lots, insertion-sort their indices by expiry/ID, then allocate greedily across batches.
- **Clear invariants:** one product code has one name/unit; quantities never become negative; other products are not consumed.
- **All-or-nothing business rule:** insufficient valid stock causes no deductions; cancelling a preview also changes nothing.
- **Failure handling:** failed saves restore the proposed quantities in memory; previous main data is backed up.
- **Repeatable evidence:** 68 integration test methods, including one independent, fixed-seed 50-scenario reference-oracle test.

This is an introductory C project, not a production inventory or healthcare platform. Its value is the explainable algorithm, checks and evidence—not a claim of medical certification or guaranteed portfolio impact.

## Main features

1. Receive a batch with a unique batch-record ID and a reagent code.
2. List batches and search full details by batch ID.
3. Plan a requested issue across eligible batches in FEFO order.
4. Confirm or cancel the plan before changing quantities.
5. Report eligible, expired and empty batches, plus available stock and low-stock flags per reagent code.
6. Save/reload records, reject corrupt/duplicate/inconsistent/excess rows and keep the previous main file as backup.

## Concrete example

Report/issue date: `2026-10-19`; request: **7 packs of GLUCOSE_KIT**.

| Batch | Expiry | Before | Issued | After |
|---|---|---:|---:|---:|
| RB101 | 2026-12-31 | 10 | 3 | 7 |
| RB102 | 2026-11-05 | 4 | 4 | 0 |
| RB103 | 2026-10-18 | 6 | 0 — expired | 6 |

Although RB101 was received first, **RB102 is allocated first because it expires earlier**. The expired batch is retained for visibility but excluded from availability. The issue succeeds only after `y` or `Y` confirmation.

## Compile and run

From this repository's root, with GCC:

```bash
gcc main.c -std=c11 -Wall -Wextra -Wpedantic -o reagent_inventory
./reagent_inventory
```

Windows with GCC/MinGW:

```powershell
gcc main.c -std=c11 -Wall -Wextra -Wpedantic -o reagent_inventory.exe
.\reagent_inventory.exe
```

A C11-capable compiler is required. No database, GUI library, external C dependency or Python installation is required to run the C program. Only Linux GCC execution was tested here; Windows commands are supplied but were not executed in this workspace.

If you cannot install a compiler, you can still read the [actual sample output](SAMPLE_OUTPUT.md) and upload the prepared source/documents. The optional GitHub workflow can run checks after publication; GitHub's repository page itself does not execute the interactive console app.

## Menu

```text
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
```

For a **new reagent code**, receipt asks for name and unit. For a **known code**, its saved name/unit are reused automatically; only the new expiry/quantity are requested after its IDs. This prevents mixing units under the same product code.

## Data model and rules

| Field | Rule |
|---|---|
| Batch-record ID | 1–23 letters/digits/hyphens/underscores; unique and case-sensitive |
| Reagent code | Same character/length rules; identifies a product and may repeat across batches |
| Reagent name | 1–59 printable characters; spaces inside allowed |
| Stock unit | 1–11 printable characters, e.g. `packs`, `bottles`, `kits` |
| Expiry date | Real, fixed-width `YYYY-MM-DD`, years 2000–9999 |
| Quantity | Whole stock units, 0–1,000,000 in saved rows; receipts and requests require 1–1,000,000 |

Capacity: 300 batch records. Console-input whitespace at the ends is trimmed. Empty fields, `|`, control characters and overlong lines are rejected. Basic printable English/ASCII text is intended. Names are shortened in the list view only; Search shows full details.

- Eligibility uses a **user-entered date**, not the computer clock.
- Classroom expiry rule: a batch is eligible **through its recorded expiry date**, provided quantity is positive. Real expiry cutoffs and manufacturer/laboratory rules may differ; the program cannot establish actual usability.
- Equal expiry dates use lexicographic batch ID as a deterministic tie-breaker.
- An issue never mixes different reagent codes. Quantities are discrete stock units, not dosages, volumes or unit conversions.
- The report compares each product's valid total with a user-entered threshold; `available <= threshold` is LOW. This is a report setting, not a validated or product-specific purchasing policy.
- Reports do not sum quantities of different products/units into one misleading total.
- EMPTY takes priority for zero-quantity batches; EXPIRED counts nonempty batches before the report date.

## Saved format

```text
batchID|reagentCode|name|unit|expiryDate|quantity
RB101|GLUCOSE_KIT|Glucose Assay Kit|packs|2026-12-31|10
```

The runtime files are `reagent_batches.txt`, `reagent_batches.txt.tmp` and `reagent_batches.txt.bak`. They are relative to the current working directory and excluded by `.gitignore`. Only fictitious `examples/` files are supplied as versioned data; examples are not loaded automatically.

## Documentation — same layout as the specimen case study

- [Coursework report](COURSEWORK_REPORT.md)
- [Algorithm and flowcharts](ALGORITHM.md)
- [Code explanation](CODE_EXPLANATION.md)
- [Actual sample run](SAMPLE_OUTPUT.md)
- [Test cases](TEST_CASES.md)
- [Test results](TEST_RESULTS.md) and [compile summary](COMPILE_TEST.txt)
- [Viva guide](VIVA_GUIDE.md)
- [GitHub upload instructions](GITHUB_UPLOAD_GUIDE.md)

## Verification

Local verification on **19 October 2026**: **68/68 test methods passed**, then the same suite passed with UndefinedBehaviorSanitizer. GCC also compiled with `-Wconversion`, `-Wshadow`, warnings treated as errors and an additional `-fanalyzer` compilation.

```bash
python3 tests/run_tests.py -v
```

The optional test runner uses only Python's standard library and creates isolated temporary data folders. One test method contains 50 deterministic mixed-inventory scenarios; those are not inflated into 50 additional test counts. See the verification report for actual logs and limits.

## Limits and possible future work

This prototype has no authentication, encryption, reservations, returns, quarantine/cold-chain checks, supplier verification, monetary valuation, full transaction/audit history or multi-user locking. Saved issue deductions are retained, but an issue history is not. Receipt accepts any supported real expiry date so historical/expired lots can be demonstrated; it does not verify a real receipt date.

Use one running copy per data folder and do not edit files while running. Temporary-file/backup replacement is not a crash-atomic or power-failure-safe database transaction. Follow the recovery warning if only the backup remains.

Possible **future work, not implemented**: per-product reorder levels, a transaction log, stronger storage recovery and role-based access. Any real laboratory use would require a substantially different validated system.

The college's Unit 1–5 syllabus was not supplied, so concepts are explained without inventing unit numbers. Study the source and describe your own contribution accurately, acknowledging assistance according to your course's rules.
