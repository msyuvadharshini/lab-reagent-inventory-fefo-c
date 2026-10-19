# Test Cases — Reagent Inventory and FEFO

**Observed on 2026-10-19: 68/68 test methods passed.**

The optional suite compiles this repository's `main.c` with C11, strict warnings, conversion/shadow checks and warnings treated as errors. Runtime records are isolated in temporary folders.

## Main scenarios

| Scenario | Expected result | Actual |
|---|---|---|
| Receive a new product/batch | One canonical six-field row saved | PASS |
| Receive another batch of the same code | Saved name/unit reused | PASS |
| Earlier expiry entered later | Earlier-expiring eligible batch allocated first | PASS |
| Equal expiry dates | Lexicographic batch-ID tie-break | PASS |
| Expired/empty stock | Not allocated or included as valid availability | PASS |
| Insufficient valid total | Entire request refused, original bytes unchanged | PASS |
| Cancel or EOF before confirmation | Preview consumes nothing | PASS |
| Save failure after confirmation | Proposed in-memory quantities restored; checked failure cases keep main bytes unchanged | PASS |
| Per-code report | Separate totals/units and threshold flags | PASS |
| Full-capacity quantities | Total 300000000 represented without overflow | PASS |
| Reference-oracle comparison | 50 fixed-seed cases match sorted FEFO and conservation checks | PASS |

## Named test catalogue

The 50 random scenarios are subcases of one named method below, not 50 extra methods. Other methods also include boundary subcases.

| Test method | Expected behaviour checked | Actual |
|---|---|---|
| `test_all_stock_expired` | When all batches are expired, valid availability is zero and nothing is issued. | PASS |
| `test_batch_limit` | At 300 batches another receipt is refused without changing saved bytes. | PASS |
| `test_blank_binary_and_overlong_saved_rows` | Blank, null-containing and overlong rows are refused without rewriting data. | PASS |
| `test_cancel_plan` | A displayed plan with n/N confirmation consumes no stock. | PASS |
| `test_case_sensitive_codes` | Case-sensitive reagent codes remain distinct inventory products. | PASS |
| `test_clean_start_list` | A fresh project is empty and does not invent or automatically seed records. | PASS |
| `test_crlf_and_unterminated_saved_rows` | CRLF records and a valid final row without newline load correctly. | PASS |
| `test_crlf_console_input` | CRLF input leaves no stray newline/menu errors. | PASS |
| `test_date_junk_not_truncated` | Trailing text after a date is rejected rather than truncated into a valid date. | PASS |
| `test_duplicate_batch` | Duplicate batch IDs are rejected before requesting more fields. | PASS |
| `test_duplicate_saved_id` | Duplicate IDs on disk are caught before any editing. | PASS |
| `test_empty_report` | An empty report gives a no-records message without unnecessary date prompts. | PASS |
| `test_empty_saved_file` | An existing empty file is a valid clean inventory. | PASS |
| `test_eof_during_confirmation` | EOF after a plan but before confirmation leaves inventory unchanged. | PASS |
| `test_eof_menu` | EOF at the menu exits cleanly rather than looping forever. | PASS |
| `test_eof_registration` | EOF before all required receipt fields cancels the incomplete batch. | PASS |
| `test_exact_available_issue` | An issue equal to the available total consumes all eligible stock, never below zero. | PASS |
| `test_exact_menu` | Trailing text, a leading zero and arbitrary words are not menu numbers. | PASS |
| `test_excess_batch_file` | A 301-row file is rejected instead of silently dropping the final record. | PASS |
| `test_expired_batches_excluded` | Expired stock is neither allocated nor counted toward valid availability. | PASS |
| `test_expiry_date_inclusive_model` | The documented classroom rule permits a batch on its recorded expiry date. | PASS |
| `test_extra_saved_field` | Extra record fields are detected by the bounded scan's final character check. | PASS |
| `test_failed_backup_keeps_original` | A backup-path replacement failure restores proposed deductions and keeps the main file. | PASS |
| `test_failed_issue_rolls_back_memory_and_disk` | A blocked temporary file leaves both saved data and subsequent search quantities unchanged. | PASS |
| `test_fefo_equal_expiry_tie_break` | Equal expiry dates use lexicographic batch ID for deterministic allocation. | PASS |
| `test_fefo_not_receipt_order` | A later-received batch expiring earlier is issued before the first received batch. | PASS |
| `test_final_input_without_newline` | A final exit choice without a newline is accepted. | PASS |
| `test_id_character_rules` | IDs reject spaces/slashes and accept letters, digits, underscores and hyphens. | PASS |
| `test_inconsistent_saved_product_metadata` | The same code cannot silently mix product names or stock units. | PASS |
| `test_insufficient_no_partial_issue` | Insufficient valid stock makes no partial deductions and does not ask for confirmation. | PASS |
| `test_invalid_confirmation` | Words other than exact y/Y/n/N do not accidentally confirm an issue. | PASS |
| `test_invalid_dates` | Impossible, signed, shortened and out-of-range dates are rejected. | PASS |
| `test_invalid_issue_date` | An invalid issue date prevents planning or stock changes. | PASS |
| `test_invalid_issue_quantity` | Issue requests must be positive digit-only whole quantities within the limit. | PASS |
| `test_invalid_receipt_quantities` | Receipts reject zero, negatives, signs, fractions, exponents, suffixes and over-limit values. | PASS |
| `test_invalid_report_input` | Invalid report dates/thresholds do not edit saved inventory. | PASS |
| `test_invalid_saved_date` | Saved dates are revalidated, not blindly trusted. | PASS |
| `test_invalid_saved_quantity` | Negative, signed, fractional, overflow and excessive saved quantities are refused. | PASS |
| `test_large_valid_total_no_overflow` | The full 300-batch maximum total 300000000 is summed correctly without overflow. | PASS |
| `test_leap_and_supported_year_boundaries` | Leap days in 2000/2028 and the upper supported date 9999-12-31 are accepted. | PASS |
| `test_malformed_middle_row` | A malformed middle row blocks startup and preserves the full original file. | PASS |
| `test_maximum_field_lengths` | Exact documented ID/code/name/unit length limits are accepted without truncation. | PASS |
| `test_multiple_codes_isolated` | An issue for one code never consumes another product, even with an earlier expiry. | PASS |
| `test_one_over_id_length` | An ID exceeding its maximum by one character is rejected, not truncated. | PASS |
| `test_orphan_backup_recovery_warning` | A backup without the main file triggers recovery instead of silently starting empty. | PASS |
| `test_outer_whitespace` | Surrounding console whitespace is trimmed; spaces inside the name remain. | PASS |
| `test_overlong_line_drained` | An overlong ID is rejected and fully consumed before the next menu. | PASS |
| `test_previous_main_backed_up` | A successful replacement preserves the previous main file in .bak. | PASS |
| `test_quantity_erange_and_long_input` | Huge integers and overlong numeric input are rejected without overflow or spillover. | PASS |
| `test_quantity_leading_zeroes` | Digit-only quantities with leading zeroes are saved as canonical integers. | PASS |
| `test_quantity_upper_boundary` | The maximum per-batch quantity 1000000 is accepted. | PASS |
| `test_randomized_fefo_against_python_oracle` | Fifty fixed-seed mixed inventories match an independent sorted FEFO oracle and conservation rules. | PASS |
| `test_reagent_code_character_rules` | Invalid reagent codes are refused before name/unit prompts. | PASS |
| `test_receipt_save_failure` | A blocked temporary path causes no false receipt or in-memory count increase. | PASS |
| `test_receive_existing_product_reuses_metadata` | A later batch of a known code reuses its saved name/unit without reprompting. | PASS |
| `test_receive_new_product` | A valid new product and batch save exactly one canonical six-field row. | PASS |
| `test_repeated_issues_never_negative` | After stock reaches zero, further requests cannot make it negative. | PASS |
| `test_report_does_not_mix_product_units` | Available totals are per reagent code/unit, never one sum of packs and bottles. | PASS |
| `test_restart_persistence` | A saved receipt remains searchable after restarting the application. | PASS |
| `test_search_existing` | Search displays the full code, name, unit, expiry and quantity. | PASS |
| `test_search_missing` | Searching an unknown batch returns a clear not-found message. | PASS |
| `test_stock_report_categories_and_low_threshold` | The report distinguishes eligible/expired/empty lots and flags valid totals at the threshold. | PASS |
| `test_text_validation` | Blank, pipe-containing and control-character names are refused. | PASS |
| `test_unknown_issue_code` | Unknown codes return before asking for a date or quantity. | PASS |
| `test_uppercase_yes_and_restart` | Y confirms an issue and the reduced stock persists after restart. | PASS |
| `test_zero_batches_excluded` | Empty batches are not allocated even if they expire before the stocked batch. | PASS |
| `test_zero_report_threshold` | Threshold zero is allowed and marks an out-of-stock reagent as LOW. | PASS |
| `test_zero_saved_quantity` | A depleted batch with zero quantity remains a valid saved record. | PASS |

## Repeat and inspect

From the repository root: `python3 tests/run_tests.py -v`. GCC and Python are required only to repeat automated checks; Python is not needed to run the C program.
See [TEST_RESULTS.md](TEST_RESULTS.md), [the normal log](tests/LAST_TEST_RUN.txt), [the UBSan log](tests/UBSAN_TEST_RUN.txt) and [COMPILE_TEST.txt](COMPILE_TEST.txt).

Passing these cases does not establish clinical usability, prove every possible input, or simulate all hardware/crash/concurrency failures.
