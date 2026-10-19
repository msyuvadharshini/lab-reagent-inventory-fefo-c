# Understanding `main.c`

## Data structure

```c
typedef struct {
    char id[ID_LEN];
    char reagentCode[CODE_LEN];
    char name[NAME_LEN];
    char unit[UNIT_LEN];
    char expiryDate[DATE_LEN];
    long quantity;
} Batch;
```

A batch ID identifies one inventory-lot record. Several batch records can share a reagent code; that code always uses the same product name and unit. `Batch batches[MAX_BATCHES]` holds up to 300 records. No dynamic allocation is used.

Quantities are `long`, not floating point, because this classroom model handles whole stock units. Dates use 11 bytes: ten visible characters and `\0`.

## Function map

| Function | Responsibility |
|---|---|
| `main` | Load once, repeat the menu, dispatch operations and handle Exit/EOF |
| `findBatch` / `findProduct` | Linear lookup by unique batch ID or first matching reagent code |
| `addBatch` | Validate/reuse metadata, receive a batch, save before increasing the count |
| `listBatches` / `searchBatch` | Shortened table or full record details |
| `earlier` | Compare expiry, then batch ID for deterministic ties |
| `planIssue` | Filter, insertion-sort indices, check stock and construct deductions |
| `issueStock` | Read request, show/confirm plan, save or restore quantities |
| `stockReport` | Classify batches; calculate per-code valid totals and low-stock flags |
| `parseQuantity` / `readQuantity` | Check digit-only bounded integers using `strtol` and `ERANGE` |
| `validDate` / `readDate` | Check exact ISO date syntax, month lengths and leap years |
| `readRawLine`, `readText`, `readId` | Consume complete lines, trim console input and validate fields |
| `openDataFile` / `loadBatches` | Distinguish clean start/recovery and validate every saved row |
| `saveBatches` / `commitFile` | Check temporary-file writes and replace data with a previous-main backup |

## The important algorithm

### 1. Filter eligible indices

Only the requested code, quantity > 0 and expiry >= issue date are selected. The expiry-day rule is a stated classroom assumption, not an actual clinical usability decision.

### 2. Sort indices, not the records

```c
while (j > 0 && earlier(&batches[key], &batches[order[j - 1]])) {
    order[j] = order[j - 1];
    j--;
}
order[j] = key;
```

This is insertion sort. Each `order[]` element is an index into `batches[]`. The original file/list order is preserved, while allocation follows a different expiry-based order.

### 3. Reject an insufficient request first

If eligible availability is below the request, `planIssue` leaves all proposed deductions at zero. The operation does not silently consume a partial amount.

### 4. Greedy allocation

```c
take[index] = batches[index].quantity < remaining
              ? batches[index].quantity : remaining;
remaining -= take[index];
```

`take[]` is only a proposed plan. It never exceeds the batch stock or the request still remaining. Earlier batches are used before later ones.

### 5. Confirm, save, or roll back

Only exact `y`/`Y` applies the plan. The program subtracts `take[i]`, saves the candidate records, and adds the same values back on a normal save failure. Preview/cancellation does not touch inventory. This is a business-rule rollback, not a crash-safe database transaction.

## Numeric safety

- Digit checks reject signs, fractions, exponents and suffixes.
- `strtol` plus `ERANGE` handles extremely large numbers without integer-overflow parsing.
- Every quantity is bounded by 1,000,000.
- At most 300 such records give a maximum total of 300,000,000.
- `_Static_assert` verifies at compile time that this total fits in `long`.
- Zero is valid for a depleted saved batch or report threshold, but not a new receipt/request.

## Other important C concepts

`int *count` lets `addBatch` update its caller's count only after saving succeeds. Bounded scans such as `%23[^|]` leave room for string termination; a final `%c` detects extra fields. The loader revalidates values, rejects duplicates and enforces name/unit consistency per code.

Fixed-width, validated `YYYY-MM-DD` values can be ordered using `strcmp`; that does not hold for arbitrary date formats. `unsigned char` casts make the character-classification calls valid for byte values.

## Complexity

For n stored batches and k eligible batches:

- ID/product search and saving: O(n).
- Filtering: O(n); insertion sort: O(k²); greedy allocation: O(k).
- Loading with duplicate/metadata checks and grouped reporting: O(n²) worst case.
- Working memory: O(n) in fixed arrays; no `malloc`.

The small cap makes insertion sort explainable and adequate here. The program has no issue-history ledger, clinical validation, authentication or concurrent-writer support.
