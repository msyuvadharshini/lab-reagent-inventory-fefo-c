# Actual Sample Run — FEFO Inventory

Captured on Linux/GCC on 2026-10-19 in an empty temporary data folder. All records are fictitious. This is actual program output, not a claimed production result or a screenshot.

## What this demonstrates

Three batches are received in an order different from their expiry order. A request for 7 packs consumes 4 from RB102 and 3 from RB101. RB103 is expired on the selected issue date and is excluded. A subsequent report shows 7 eligible packs and a LOW flag at threshold 10.

## Input sequence

Enter these lines only as prompted. A known reagent code reuses its name/unit; it does not ask for those fields again. The sequence is also in `examples/demo_input.txt`.

```text
1
RB101
GLUCOSE_KIT
Glucose Assay Kit
packs
2026-12-31
10
1
RB102
GLUCOSE_KIT
2026-11-05
4
1
RB103
GLUCOSE_KIT
2026-10-18
6
4
GLUCOSE_KIT
2026-10-19
7
y
5
2026-10-19
10
6
```

## Actual captured output

Input is supplied separately above and not echoed by the capture, so adjacent prompts can appear on one line. An interactive terminal usually echoes typed input.

```text
Educational inventory simulation. Use fictitious records only.

LAB REAGENT INVENTORY AND FEFO ALLOCATION
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
Choose an option: Unique batch record ID: Reagent code: Reagent name: Stock unit (e.g. packs): Expiry date (YYYY-MM-DD): Quantity received: Batch saved successfully.

LAB REAGENT INVENTORY AND FEFO ALLOCATION
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
Choose an option: Unique batch record ID: Reagent code: Using saved product: Glucose Assay Kit [packs].
Expiry date (YYYY-MM-DD): Quantity received: Batch saved successfully.

LAB REAGENT INVENTORY AND FEFO ALLOCATION
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
Choose an option: Unique batch record ID: Reagent code: Using saved product: Glucose Assay Kit [packs].
Expiry date (YYYY-MM-DD): Quantity received: Batch saved successfully.

LAB REAGENT INVENTORY AND FEFO ALLOCATION
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
Choose an option: Reagent code to issue: Issue date (YYYY-MM-DD): Quantity requested: 
FEFO PLAN: GLUCOSE_KIT | Glucose Assay Kit | as of 2026-10-19
RB102 | expires 2026-11-05 | issue 4 packs
RB101 | expires 2026-12-31 | issue 3 packs
Requested=7, Available=14 [packs]. Expired/empty batches excluded.
Confirm issue? (y/n): Issue saved successfully. Quantity issued: 7 packs.

LAB REAGENT INVENTORY AND FEFO ALLOCATION
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
Choose an option: Report date (YYYY-MM-DD): Low-stock threshold (each product's own unit): 
BATCH STATUS AS OF 2026-10-19
RB101 | GLUCOSE_KIT | ELIGIBLE | quantity=7 packs | expiry=2026-12-31
RB102 | GLUCOSE_KIT | EMPTY | quantity=0 packs | expiry=2026-11-05
RB103 | GLUCOSE_KIT | EXPIRED | quantity=6 packs | expiry=2026-10-18

AVAILABLE STOCK BY REAGENT (expired stock excluded)
GLUCOSE_KIT | Glucose Assay Kit | available=7 packs | LOW (threshold=10)
Batch summary: Eligible=1, Expired=1, Empty=1, Total=3
Low-stock reagent codes: 1

LAB REAGENT INVENTORY AND FEFO ALLOCATION
1. Receive a batch
2. List batches
3. Search batch ID
4. Plan and confirm FEFO issue
5. Stock and expiry report
6. Exit
Choose an option: Exiting inventory. Thank you.
```

## Saved data after the run

```text
RB101|GLUCOSE_KIT|Glucose Assay Kit|packs|2026-12-31|7
RB102|GLUCOSE_KIT|Glucose Assay Kit|packs|2026-11-05|0
RB103|GLUCOSE_KIT|Glucose Assay Kit|packs|2026-10-18|6
```

## Reproduce safely

Use a separate empty copy of the project folder with no runtime data or backup, compile, and follow the input sequence. On a compatible shell, `./reagent_inventory < examples/demo_input.txt` supplies it automatically.

Alternatively, while closed and in a separate clean demo folder, copy `examples/reagent_batches.demo.txt` to `reagent_batches.txt`, then choose issue/report operations manually. Do not seed that file and then run the clean-start script, because it registers the same IDs itself. Never delete important data just to reproduce a demo.
