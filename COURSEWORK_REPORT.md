# Case Study — Lab Reagent Inventory and FEFO Allocation

**Language:** C11  
**Submission:** One independent console application  
**Data:** Fictitious laboratory stock only

Add your student details only if required. Describe your own contribution accurately and acknowledge assistance according to your college's rules.

## 1. Aim

Apply C data structures, functions, string handling, selection, loops, sorting and file handling to batch-wise laboratory reagent inventory and a transparent expiry-priority allocation policy.

## 2. Problem statement

A laboratory has multiple lots of one reagent. An older receipt may actually expire later than a newly received lot. A simple first-entered/first-issued list can therefore select the wrong lot under a First Expiry, First Out policy. A useful small prototype should choose by expiry, exclude expired stock, check the full request first, and avoid negative quantities or mixed units.

## 3. Objectives

1. Record unique batch IDs, reagent codes, consistent product metadata, expiry and stock.
2. Search/list batches and preserve records between runs.
3. Plan an issue by earliest eligible expiry, with a deterministic ID tie-breaker.
4. Reject a request if total valid stock is insufficient; do not make a partial issue.
5. Display and confirm the plan before deducting quantities.
6. Restore proposed quantities on a normal save failure.
7. Report expired/empty/eligible batches and per-code valid stock/low-stock flags.
8. Provide repeatable tests and explainable output.

## 4. Proposed solution

Use an array of `Batch` structures, limited to 300 records. Load and validate all saved rows before allowing the menu to edit them. Receive batches through bounded whole-line inputs. Reuse a known code's product name/unit rather than asking for potentially inconsistent values.

For an issue, collect eligible indices, insertion-sort those indices by expiry and ID, check total stock and greedily allocate the complete request. Records remain in their original order. Confirmation applies the proposed deductions; checked file replacement saves them together. Insufficient stock, cancellation or incomplete input changes nothing.

## 5. Worked example

For issue date `2026-10-19`, the input contains:

| Batch | Expiry | Packs |
|---|---|---:|
| RB101 | 2026-12-31 | 10 |
| RB102 | 2026-11-05 | 4 |
| RB103 | 2026-10-18 | 6 |

A request for 7 packs allocates 4 from RB102 and 3 from RB101, leaving 7 and 0 respectively; RB103 remains 6 because it is expired in this report. With a low-stock threshold of 10, the remaining eligible total of 7 is LOW.

This demonstrates FEFO rather than receipt order. The policy is deterministic; no claim is made that it predicts demand or globally minimises all future waste.

## 6. Inputs, outputs and assumptions

- Inputs: identifiers, product name/unit, expiry, received/requested whole quantities, report/issue date, threshold and confirmation.
- Outputs: full ID details, allocation plan, successful issue/cancellation/errors, batch categories and valid totals by product.
- Supported dates: actual `YYYY-MM-DD` dates in years 2000–9999.
- Batch IDs/codes are case-sensitive. One reagent code has one name/unit.
- Quantities are whole stock units from 0 to 1,000,000 per saved batch; receipts/requests require a positive value.
- In this classroom model a positive batch is eligible through its expiry date. Real manufacturer/laboratory cutoff rules may differ.
- A report threshold is applied to each product's own unit; different units are never added into one combined stock quantity.
- Empty batches stay in the register and take the EMPTY category even if their date has passed.

## 7. C concept mapping

| Concept | Application |
|---|---|
| Variables, constants, I/O | Menu/input buffers, capacity and quantity limits, console/file output |
| Conditions and `switch` | Menu choices, eligibility, stock checks and confirmation |
| Loops | Menu repetition, record traversal and allocation |
| Structures and arrays | Batch records, ordered indices and proposed deduction arrays |
| Strings | Codes/names, exact input, ID/date comparison and bounded parsing |
| Functions and pointers | Modular tasks, `int *count`, pointer comparisons, `FILE *` streams |
| Sorting / greedy method | Insertion sort of eligible indices followed by FEFO allocation |
| File handling | Complete validated loading and checked temporary-file/backup replacement |
| Integer validation | `strtol`, `ERANGE`, explicit bounds and a C11 compile-time capacity assertion |

Exact Unit 1–5 numbering is not assigned because the syllabus was not supplied. Confirm the required course alignment with your teacher.

## 8. Testing and observed results

Local Linux GCC verification on 19 October 2026 passed **68/68 integration test methods**. The same suite passed with UndefinedBehaviorSanitizer. One method runs 50 fixed-seed mixed inventories against an independent Python FEFO reference and checks stock conservation, no negative values, isolation of other products and stable file order. Those scenarios are not inflated into extra method counts.

The build treats warnings as errors and also enables conversion/shadow warnings. A separate GCC analyzer compilation completed without diagnostics. See [TEST_RESULTS.md](TEST_RESULTS.md), [TEST_CASES.md](TEST_CASES.md) and [SAMPLE_OUTPUT.md](SAMPLE_OUTPUT.md).

## 9. Limits and safety

Use fictitious records only. The program cannot certify reagent safety, correct storage, identity, suitability or regulatory compliance. It has no cold-chain/quarantine handling, unit conversion, dosing, audit ledger, authentication, encryption, reservations, returns or multi-user locking.

The file save reduces some ordinary write-failure risks but is not a power-failure-safe or crash-atomic database transaction. Only current remaining quantities are stored, not a full issue history. Tests do not prove correctness for every input or suitability for healthcare operation.

## 10. Conclusion and future work

The case study goes beyond basic CRUD by making expiry-priority allocation explicit, testable and explainable in standard C. The useful learning is the connection between a real stock problem, clear invariants, an algorithm, failure handling and evidence.

Possible future work includes per-product reorder settings, a transaction ledger and stronger storage/access control. These are not implemented features. Learn the current functions and practise the [viva guide](VIVA_GUIDE.md) before presenting.
