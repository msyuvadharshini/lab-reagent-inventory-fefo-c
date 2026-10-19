# Viva Guide — Reagent Inventory and FEFO

Use these explanations to understand the source, not to memorise claims you cannot demonstrate. Describe your contribution accurately and follow the college's rules for acknowledging assistance.

## Introduction to adapt

> This C case study manages fictitious reagent batches. Its main feature is FEFO allocation: select eligible stock by earliest expiry, not receipt order. It displays a complete plan, rejects insufficient stock without partial deductions, and asks for confirmation before saving. The program uses structures, arrays, functions, strings, insertion sort and text files.

## Questions and answers

### 1. What is FEFO, and how is it different from FIFO?

FEFO is First Expiry, First Out. FIFO is First In, First Out. A batch received later can expire sooner, so the policies can choose different batches. This program sorts by expiry, not receipt order.

### 2. Why have both a batch ID and a reagent code?

The batch ID identifies one stock-lot record. A reagent code identifies a product and can appear on several batches. The same code must have one product name/unit.

### 3. Why use an array of structures?

A structure groups each batch's related fields. An array makes a small collection easy to traverse. A fixed cap avoids dynamic-allocation complexity.

### 4. Why is `int *count` passed to registration?

The function must update the caller's count after a successful save. `(*count)++` changes that integer. A failed save leaves the candidate outside the active range.

### 5. Why sort indices instead of records?

`order[]` contains positions into `batches[]`. Sorting those positions lets FEFO use a different order without rearranging the displayed/saved register.

### 6. Which sort is used and what is its complexity?

Insertion sort. Filtering is O(n), sorting k eligible indices is O(k²), and allocation is O(k). It is simple and adequate for at most 300 records.

### 7. How are equal expiry dates handled?

Lexicographic batch ID order is the deterministic tie-breaker. It does not mean numeric ID order or imply a clinical priority.

### 8. How are expired or empty batches handled?

They remain stored for visibility but are excluded from issuing. The model treats expiry equal to the issue date as eligible if stock is positive. Real laboratory rules may use different cutoff/quality requirements.

### 9. Why check total availability before allocating?

If valid total is below the request, the whole operation is refused. This prevents silently issuing only part of the requested amount.

### 10. How does the greedy allocation work?

For each FEFO-ordered batch, take the smaller of its quantity and the remaining request. Deduct that amount from the remaining request and move to the next batch if needed. Each proposed amount is bounded by available stock.

### 11. Does displaying a plan change stock?

No. `take[]` is a proposed deduction array. Only exact `y` or `Y` confirmation applies it. Cancellation, invalid confirmation and EOF leave quantities unchanged.

### 12. What happens if saving an issue fails?

The function adds back the same proposed deductions, restoring memory during normal failure handling. The save routine preserves/restores the old main file where possible and reports recovery instructions if required. This is not a guarantee of crash-safe database transactions.

### 13. Why use `long` and `strtol` instead of `atoi` or floats?

Stock is whole units. `strtol` provides an end pointer and `ERANGE` error reporting; digit checks reject signs/fractions/suffixes. Explicit limits prevent oversized values. `atoi` cannot report errors in the same controlled way.

### 14. How is total overflow prevented?

Every saved batch is at most 1,000,000 and there are at most 300 batches. The maximum total is 300,000,000. A C11 `_Static_assert` checks that the configured maximum fits in `long`.

### 15. Why is zero valid on disk but not for a receipt/request?

A used-up batch legitimately has zero remaining quantity. A receipt or issue request must be positive. The same numeric helper accepts a different minimum depending on context.

### 16. Can packs and bottles be added together?

No. Name/unit are consistent under each product code, issuing is isolated to that code, and reports calculate separate per-code quantities. There is no unit conversion or grand total across unlike units.

### 17. Why can dates be compared with `strcmp`?

Only strictly validated, fixed-width `YYYY-MM-DD` dates are compared. Year/month/day order then matches chronological order. The program does not calculate elapsed days or use the computer clock.

### 18. What does LOW mean?

The valid total is less than or equal to the threshold entered for that report, interpreted in each product's own unit. It is not a validated clinical or purchasing rule.

### 19. Why read the whole line?

It prevents extra characters/newlines from leaking into the next prompt. Overlong lines are drained and rejected rather than silently truncated. EOF is handled explicitly.

### 20. Why validate saved data again?

Local files can be edited or damaged. The loader refuses bad fields/dates/quantities, duplicate IDs, inconsistent metadata and excess rows before allowing any editing.

### 21. Does it keep every issue as an audit history?

No. It stores current remaining quantities and a previous-main backup, not a complete ledger of issues/users/timestamps. That would be future work.

### 22. What does the test count prove?

It proves those checked cases passed in the recorded environment, not all possible inputs. There are 68 test methods; one of them compares 50 fixed-seed scenarios to an independent reference. They are not counted as 118 tests.

## Short demonstration

Use an empty copied project folder, not important existing data.

1. Receive RB101/GLUCOSE_KIT, name Glucose Assay Kit, unit packs, expiry 2026-12-31, quantity 10.
2. Receive RB102 for the same code, expiry 2026-11-05, quantity 4. Explain that name/unit are reused.
3. Receive RB103 for that code, expiry 2026-10-18, quantity 6.
4. Request 7 packs on 2026-10-19. Explain RB102=4, RB101=3, and why RB103 is excluded.
5. Confirm and run a stock report with threshold 10. Explain 7 eligible packs, 1 empty lot, 1 expired lot and the LOW flag.
6. Restart and search to show persistence.
7. Explain cancellation and insufficient-stock tests without pretending that the program certifies reagent safety.
