#!/usr/bin/env python3
"""Compile and integration-test the standalone C11 FEFO inventory program.

Run: python3 tests/run_tests.py -v
Only Python's standard library is used; Python is not needed to run main.c.
All executables and runtime records stay in temporary folders. The randomized
oracle test uses a fixed seed and counts as ONE test method, not 50 tests.
"""
import os
from pathlib import Path
import random
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FLAGS = '-std=c11 -Wall -Wextra -Wpedantic -Werror -Wconversion -Wshadow'
DATA_FILE = 'reagent_batches.txt'
CODE = 'GLUCOSE_KIT'
NAME = 'Glucose Assay Kit'


def row(batch_id='RB101', code=CODE, name=NAME, unit='packs', expiry='2026-12-31', quantity=10):
    return f'{batch_id}|{code}|{name}|{unit}|{expiry}|{quantity}\n'


def receive(batch_id='RB101', code=CODE, name=NAME, unit='packs', expiry='2026-12-31', quantity=10, existing=False):
    fields = ['1', batch_id, code]
    if not existing:
        fields += [name, unit]
    fields += [expiry, str(quantity)]
    return '\n'.join(fields) + '\n'


def issue(code=CODE, date='2026-10-19', quantity=7, answer='y'):
    script = f'4\n{code}\n{date}\n{quantity}\n'
    return script if answer is None else script + answer + '\n'


class ReagentInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory(prefix='reagent-fefo-compile-')
        cls.addClassCleanup(cls.build.cleanup)
        cls.executable = Path(cls.build.name) / ('inventory.exe' if os.name == 'nt' else 'inventory')
        command = [os.environ.get('CC', 'gcc')]
        command += shlex.split(os.environ.get('CFLAGS', FLAGS))
        command += [str(ROOT / 'main.c'), '-o', str(cls.executable)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise AssertionError('Compilation failed:\n' + result.stdout + result.stderr)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='reagent-fefo-data-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.data = self.work / DATA_FILE

    def run_app(self, script=''):
        return subprocess.run([str(self.executable)], input=script, text=True,
                              capture_output=True, cwd=self.work, timeout=3)

    def seed(self, content=None):
        self.data.write_bytes((row() if content is None else content).encode('ascii'))

    def saved(self):
        return self.data.read_text() if self.data.exists() else ''

    def quantities(self):
        return {line.split('|')[0]: int(line.split('|')[-1]) for line in self.saved().splitlines()}

    def assert_bad_file_preserved(self, content):
        self.seed(content)
        before = self.data.read_bytes()
        result = self.run_app('6\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Cannot load', result.stderr)
        self.assertEqual(self.data.read_bytes(), before)
        self.assertNotIn('Choose an option:', result.stdout)

    def block_path(self, suffix):
        path = self.work / (DATA_FILE + suffix)
        path.mkdir()
        (path / 'block.txt').write_text('deliberately block this path')

    def test_clean_start_list(self):
        """A fresh project is empty and does not invent or automatically seed records."""
        result = self.run_app('2\n6\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('No reagent batches found.', result.stdout)
        self.assertFalse(self.data.exists())

    def test_eof_menu(self):
        """EOF at the menu exits cleanly rather than looping forever."""
        result = self.run_app()
        self.assertEqual(result.returncode, 0)
        self.assertIn('Input ended.', result.stdout)

    def test_eof_registration(self):
        """EOF before all required receipt fields cancels the incomplete batch."""
        result = self.run_app('1\nRB101\nGLUCOSE_KIT\n')
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.data.exists())

    def test_receive_new_product(self):
        """A valid new product and batch save exactly one canonical six-field row."""
        result = self.run_app(receive() + '6\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Batch saved successfully.', result.stdout)
        self.assertNotIn('Invalid option.', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_receive_existing_product_reuses_metadata(self):
        """A later batch of a known code reuses its saved name/unit without reprompting."""
        self.seed()
        result = self.run_app(receive(batch_id='RB102', expiry='2026-11-05', quantity=4, existing=True) + '6\n')
        self.assertIn('Using saved product: Glucose Assay Kit [packs].', result.stdout)
        self.assertNotIn('Reagent name:', result.stdout)
        self.assertEqual(self.saved(), row() + row(batch_id='RB102', expiry='2026-11-05', quantity=4))

    def test_duplicate_batch(self):
        """Duplicate batch IDs are rejected before requesting more fields."""
        self.seed()
        result = self.run_app('1\nRB101\n6\n')
        self.assertIn('Duplicate batch ID.', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_search_existing(self):
        """Search displays the full code, name, unit, expiry and quantity."""
        self.seed()
        result = self.run_app('3\nRB101\n6\n')
        for expected in ('Batch ID: RB101', 'Reagent code: GLUCOSE_KIT', 'Name: Glucose Assay Kit',
                         'Unit: packs', 'Expiry date: 2026-12-31', 'Quantity: 10'):
            self.assertIn(expected, result.stdout)

    def test_search_missing(self):
        """Searching an unknown batch returns a clear not-found message."""
        self.seed()
        result = self.run_app('3\nUNKNOWN\n6\n')
        self.assertIn('Batch ID not found.', result.stdout)

    def test_restart_persistence(self):
        """A saved receipt remains searchable after restarting the application."""
        self.run_app(receive() + '6\n')
        result = self.run_app('3\nRB101\n6\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Quantity: 10', result.stdout)

    def test_outer_whitespace(self):
        """Surrounding console whitespace is trimmed; spaces inside the name remain."""
        script = '\n'.join('  ' + s + '  ' for s in receive().splitlines()) + '\n6\n'
        self.run_app(script)
        self.assertEqual(self.saved(), row())

    def test_crlf_console_input(self):
        """CRLF input leaves no stray newline/menu errors."""
        result = self.run_app((receive() + '6\n').replace('\n', '\r\n'))
        self.assertIn('Batch saved successfully.', result.stdout)
        self.assertNotIn('Invalid option.', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_final_input_without_newline(self):
        """A final exit choice without a newline is accepted."""
        result = self.run_app(receive() + '6')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Exiting inventory.', result.stdout)

    def test_exact_menu(self):
        """Trailing text, a leading zero and arbitrary words are not menu numbers."""
        result = self.run_app('2junk\n02\nhello\n6\n')
        self.assertEqual(result.stdout.count('Invalid option.'), 3)

    def test_overlong_line_drained(self):
        """An overlong ID is rejected and fully consumed before the next menu."""
        result = self.run_app('1\n' + 'A' * 400 + '\n2\n6\n')
        self.assertIn('Invalid input:', result.stdout)
        self.assertIn('No reagent batches found.', result.stdout)
        self.assertNotIn('Invalid option.', result.stdout)

    def test_id_character_rules(self):
        """IDs reject spaces/slashes and accept letters, digits, underscores and hyphens."""
        for bad in ('BAD ID', 'BAD/ID'):
            result = self.run_app('1\n' + bad + '\n6\n')
            self.assertIn('Invalid ID:', result.stdout)
            self.assertFalse(self.data.exists())
        self.run_app(receive(batch_id='B_01-A', code='R_01-A') + '6\n')
        self.assertTrue(self.saved().startswith('B_01-A|R_01-A|'))

    def test_reagent_code_character_rules(self):
        """Invalid reagent codes are refused before name/unit prompts."""
        result = self.run_app('1\nRB101\nBAD CODE\n6\n')
        self.assertIn('Invalid ID:', result.stdout)
        self.assertFalse(self.data.exists())

    def test_text_validation(self):
        """Blank, pipe-containing and control-character names are refused."""
        for bad in ('   ', 'Bad|Name', 'Bad\tName'):
            with self.subTest(value=repr(bad)):
                result = self.run_app('1\nRB101\nGLUCOSE_KIT\n' + bad + '\n6\n')
                self.assertIn('Invalid input:', result.stdout)
                self.assertFalse(self.data.exists())

    def test_maximum_field_lengths(self):
        """Exact documented ID/code/name/unit length limits are accepted without truncation."""
        batch_id, code, name, unit = 'B' * 23, 'C' * 23, 'N' * 59, 'U' * 11
        result = self.run_app(receive(batch_id=batch_id, code=code, name=name, unit=unit) +
                              '3\n' + batch_id + '\n6\n')
        self.assertIn('Name: ' + name, result.stdout)
        self.assertIn('Unit: ' + unit, result.stdout)
        self.assertEqual(self.saved(), row(batch_id=batch_id, code=code, name=name, unit=unit))

    def test_one_over_id_length(self):
        """An ID exceeding its maximum by one character is rejected, not truncated."""
        result = self.run_app('1\n' + 'B' * 24 + '\n6\n')
        self.assertIn('Invalid input:', result.stdout)
        self.assertFalse(self.data.exists())

    def test_invalid_dates(self):
        """Impossible, signed, shortened and out-of-range dates are rejected."""
        dates = ('2026-01-+1', '2026-02-30', '2026-04-31', '2027-02-29',
                 '2100-02-29', '2026-1-01', '1999-12-31', '2026-00-10')
        for date in dates:
            with self.subTest(date=date):
                result = self.run_app(f'1\nRB101\n{CODE}\n{NAME}\npacks\n{date}\n6\n')
                self.assertIn('Invalid date:', result.stdout)
                self.assertFalse(self.data.exists())

    def test_date_junk_not_truncated(self):
        """Trailing text after a date is rejected rather than truncated into a valid date."""
        result = self.run_app(f'1\nRB101\n{CODE}\n{NAME}\npacks\n2026-10-19junk\n6\n')
        self.assertIn('Invalid input:', result.stdout)
        self.assertNotIn('Invalid option.', result.stdout)
        self.assertFalse(self.data.exists())

    def test_leap_and_supported_year_boundaries(self):
        """Leap days in 2000/2028 and the upper supported date 9999-12-31 are accepted."""
        for date in ('2000-02-29', '2028-02-29', '9999-12-31'):
            with self.subTest(date=date):
                self.seed('')
                self.run_app(receive(expiry=date) + '6\n')
                self.assertIn('|' + date + '|', self.saved())

    def test_invalid_receipt_quantities(self):
        """Receipts reject zero, negatives, signs, fractions, exponents, suffixes and over-limit values."""
        for value in ('0', '-1', '+2', '1.5', '1e3', '12abc', '1000001'):
            with self.subTest(value=value):
                result = self.run_app(receive(quantity=value) + '6\n')
                self.assertIn('Invalid quantity:', result.stdout)
                self.assertFalse(self.data.exists())

    def test_quantity_erange_and_long_input(self):
        """Huge integers and overlong numeric input are rejected without overflow or spillover."""
        for value in ('9' * 31, '9' * 400):
            with self.subTest(length=len(value)):
                result = self.run_app(receive(quantity=value) + '6\n')
                self.assertTrue('Invalid quantity:' in result.stdout or 'Invalid input:' in result.stdout)
                self.assertFalse(self.data.exists())
                self.assertNotIn('Invalid option.', result.stdout)

    def test_quantity_upper_boundary(self):
        """The maximum per-batch quantity 1000000 is accepted."""
        self.run_app(receive(quantity=1000000) + '6\n')
        self.assertEqual(self.quantities(), {'RB101': 1000000})

    def test_quantity_leading_zeroes(self):
        """Digit-only quantities with leading zeroes are saved as canonical integers."""
        self.run_app(receive(quantity='00010') + '6\n')
        self.assertEqual(self.saved(), row())

    def test_batch_limit(self):
        """At 300 batches another receipt is refused without changing saved bytes."""
        content = ''.join(row(batch_id=f'B{i:03}') for i in range(300))
        self.seed(content)
        result = self.run_app('1\n6\n')
        self.assertIn('Batch limit reached', result.stdout)
        self.assertEqual(self.saved(), content)

    def test_excess_batch_file(self):
        """A 301-row file is rejected instead of silently dropping the final record."""
        self.assert_bad_file_preserved(''.join(row(batch_id=f'B{i:03}') for i in range(301)))

    def test_malformed_middle_row(self):
        """A malformed middle row blocks startup and preserves the full original file."""
        self.assert_bad_file_preserved(row() + 'BROKEN\n' + row(batch_id='RB102'))

    def test_duplicate_saved_id(self):
        """Duplicate IDs on disk are caught before any editing."""
        self.assert_bad_file_preserved(row() + row())

    def test_invalid_saved_date(self):
        """Saved dates are revalidated, not blindly trusted."""
        self.assert_bad_file_preserved(row(expiry='2026-02-30'))

    def test_invalid_saved_quantity(self):
        """Negative, signed, fractional, overflow and excessive saved quantities are refused."""
        for quantity in ('-1', '+1', '1.5', '1000001', '9' * 31):
            with self.subTest(quantity=quantity):
                self.assert_bad_file_preserved(row(quantity=quantity))

    def test_zero_saved_quantity(self):
        """A depleted batch with zero quantity remains a valid saved record."""
        self.seed(row(quantity=0))
        result = self.run_app('3\nRB101\n6\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Quantity: 0', result.stdout)

    def test_inconsistent_saved_product_metadata(self):
        """The same code cannot silently mix product names or stock units."""
        for other in (row(batch_id='RB102', name='Different Product'), row(batch_id='RB102', unit='bottles')):
            with self.subTest(other=other):
                self.assert_bad_file_preserved(row() + other)

    def test_extra_saved_field(self):
        """Extra record fields are detected by the bounded scan's final character check."""
        self.assert_bad_file_preserved(row().rstrip('\n') + '|EXTRA\n')

    def test_blank_binary_and_overlong_saved_rows(self):
        """Blank, null-containing and overlong rows are refused without rewriting data."""
        for content in (row() + '\n', row().rstrip('\n') + '\x00junk\n', 'X' * 400 + '\n'):
            with self.subTest(content=repr(content[:30])):
                self.assert_bad_file_preserved(content)

    def test_crlf_and_unterminated_saved_rows(self):
        """CRLF records and a valid final row without newline load correctly."""
        for content in (row().replace('\n', '\r\n'), row().rstrip('\n')):
            self.seed(content)
            result = self.run_app('3\nRB101\n6\n')
            self.assertEqual(result.returncode, 0)
            self.assertIn('Quantity: 10', result.stdout)

    def test_empty_saved_file(self):
        """An existing empty file is a valid clean inventory."""
        self.seed('')
        result = self.run_app('2\n6\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('No reagent batches found.', result.stdout)

    def test_receipt_save_failure(self):
        """A blocked temporary path causes no false receipt or in-memory count increase."""
        self.block_path('.tmp')
        result = self.run_app(receive() + '2\n6\n')
        self.assertIn('Save failed:', result.stdout)
        self.assertNotIn('Batch saved successfully.', result.stdout)
        self.assertIn('No reagent batches found.', result.stdout)
        self.assertFalse(self.data.exists())

    def test_previous_main_backed_up(self):
        """A successful replacement preserves the previous main file in .bak."""
        self.seed()
        self.run_app(receive(batch_id='RB102', existing=True) + '6\n')
        self.assertEqual((self.work / (DATA_FILE + '.bak')).read_text(), row())
        self.assertEqual(len(self.saved().splitlines()), 2)

    def test_orphan_backup_recovery_warning(self):
        """A backup without the main file triggers recovery instead of silently starting empty."""
        backup = self.work / (DATA_FILE + '.bak')
        backup.write_text(row())
        result = self.run_app('6\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Restore the backup', result.stderr)
        self.assertFalse(self.data.exists())
        self.assertEqual(backup.read_text(), row())

    def test_fefo_not_receipt_order(self):
        """A later-received batch expiring earlier is issued before the first received batch."""
        self.seed(row(expiry='2026-12-31', quantity=10) + row(batch_id='RB102', expiry='2026-11-05', quantity=4))
        result = self.run_app(issue(quantity=7) + '6\n')
        self.assertIn('RB102 | expires 2026-11-05 | issue 4 packs', result.stdout)
        self.assertIn('RB101 | expires 2026-12-31 | issue 3 packs', result.stdout)
        self.assertLess(result.stdout.index('RB102 | expires'), result.stdout.index('RB101 | expires'))
        self.assertEqual(self.quantities(), {'RB101': 7, 'RB102': 0})
        self.assertEqual([line.split('|')[0] for line in self.saved().splitlines()], ['RB101', 'RB102'])

    def test_fefo_equal_expiry_tie_break(self):
        """Equal expiry dates use lexicographic batch ID for deterministic allocation."""
        self.seed(row(batch_id='RB_B', quantity=5) + row(batch_id='RB_A', quantity=5))
        result = self.run_app(issue(quantity=3) + '6\n')
        self.assertIn('RB_A | expires 2026-12-31 | issue 3 packs', result.stdout)
        self.assertEqual(self.quantities(), {'RB_B': 5, 'RB_A': 2})

    def test_expired_batches_excluded(self):
        """Expired stock is neither allocated nor counted toward valid availability."""
        self.seed(row(quantity=5) + row(batch_id='OLD', expiry='2026-10-18', quantity=100))
        result = self.run_app(issue(quantity=3) + '6\n')
        self.assertIn('Available=5', result.stdout)
        self.assertNotIn('OLD | expires', result.stdout)
        self.assertEqual(self.quantities(), {'RB101': 2, 'OLD': 100})

    def test_expiry_date_inclusive_model(self):
        """The documented classroom rule permits a batch on its recorded expiry date."""
        self.seed(row(expiry='2026-10-19', quantity=3))
        self.run_app(issue(quantity=3) + '6\n')
        self.assertEqual(self.quantities(), {'RB101': 0})

    def test_zero_batches_excluded(self):
        """Empty batches are not allocated even if they expire before the stocked batch."""
        self.seed(row(quantity=5) + row(batch_id='EMPTY', expiry='2026-10-19', quantity=0))
        result = self.run_app(issue(quantity=2) + '6\n')
        self.assertNotIn('EMPTY | expires', result.stdout)
        self.assertEqual(self.quantities(), {'RB101': 3, 'EMPTY': 0})

    def test_exact_available_issue(self):
        """An issue equal to the available total consumes all eligible stock, never below zero."""
        self.seed(row(quantity=4) + row(batch_id='RB102', expiry='2026-11-05', quantity=3))
        result = self.run_app(issue(quantity=7) + '6\n')
        self.assertIn('Issue saved successfully.', result.stdout)
        self.assertEqual(self.quantities(), {'RB101': 0, 'RB102': 0})

    def test_insufficient_no_partial_issue(self):
        """Insufficient valid stock makes no partial deductions and does not ask for confirmation."""
        self.seed(row(quantity=2) + row(batch_id='OLD', expiry='2026-10-18', quantity=100))
        before = self.data.read_bytes()
        result = self.run_app(issue(quantity=3, answer=None) + '6\n')
        self.assertIn('Insufficient valid stock: available=2, requested=3', result.stdout)
        self.assertNotIn('Confirm issue?', result.stdout)
        self.assertEqual(self.data.read_bytes(), before)

    def test_all_stock_expired(self):
        """When all batches are expired, valid availability is zero and nothing is issued."""
        self.seed(row(expiry='2026-10-18', quantity=100))
        before = self.data.read_bytes()
        result = self.run_app(issue(quantity=1, answer=None) + '6\n')
        self.assertIn('available=0, requested=1', result.stdout)
        self.assertEqual(self.data.read_bytes(), before)

    def test_multiple_codes_isolated(self):
        """An issue for one code never consumes another product, even with an earlier expiry."""
        self.seed(row(quantity=10) + row(batch_id='OTHER', code='BUFFER', name='Buffer', unit='bottles', expiry='2026-10-19', quantity=10))
        self.run_app(issue(quantity=7) + '6\n')
        self.assertEqual(self.quantities(), {'RB101': 3, 'OTHER': 10})

    def test_case_sensitive_codes(self):
        """Case-sensitive reagent codes remain distinct inventory products."""
        self.seed(row() + row(batch_id='OTHER', code='glucose_kit', name='Other Kit', quantity=20))
        self.run_app(issue(quantity=3) + '6\n')
        self.assertEqual(self.quantities(), {'RB101': 7, 'OTHER': 20})

    def test_unknown_issue_code(self):
        """Unknown codes return before asking for a date or quantity."""
        self.seed()
        result = self.run_app('4\nUNKNOWN\n6\n')
        self.assertIn('Reagent code not found.', result.stdout)
        self.assertNotIn('Issue date (', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_invalid_issue_date(self):
        """An invalid issue date prevents planning or stock changes."""
        self.seed()
        result = self.run_app(f'4\n{CODE}\n2026-02-30\n6\n')
        self.assertIn('Invalid date:', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_invalid_issue_quantity(self):
        """Issue requests must be positive digit-only whole quantities within the limit."""
        self.seed()
        for value in ('0', '-1', '+1', '1.5', '1e2', '1000001'):
            result = self.run_app(issue(quantity=value, answer=None) + '6\n')
            self.assertIn('Invalid quantity:', result.stdout)
            self.assertEqual(self.saved(), row())

    def test_cancel_plan(self):
        """A displayed plan with n/N confirmation consumes no stock."""
        self.seed()
        for answer in ('n', 'N'):
            result = self.run_app(issue(quantity=3, answer=answer) + '6\n')
            self.assertIn('FEFO PLAN:', result.stdout)
            self.assertIn('Issue cancelled.', result.stdout)
            self.assertEqual(self.saved(), row())

    def test_invalid_confirmation(self):
        """Words other than exact y/Y/n/N do not accidentally confirm an issue."""
        self.seed()
        result = self.run_app(issue(quantity=3, answer='yes') + '6\n')
        self.assertIn('Issue cancelled: enter y or n.', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_eof_during_confirmation(self):
        """EOF after a plan but before confirmation leaves inventory unchanged."""
        self.seed()
        result = self.run_app(issue(quantity=3, answer=None))
        self.assertEqual(result.returncode, 0)
        self.assertIn('Input ended.', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_uppercase_yes_and_restart(self):
        """Y confirms an issue and the reduced stock persists after restart."""
        self.seed()
        result = self.run_app(issue(quantity=3, answer='Y') + '6\n')
        self.assertIn('Issue saved successfully.', result.stdout)
        after = self.run_app('3\nRB101\n6\n')
        self.assertIn('Quantity: 7', after.stdout)

    def test_failed_issue_rolls_back_memory_and_disk(self):
        """A blocked temporary file leaves both saved data and subsequent search quantities unchanged."""
        self.seed()
        self.block_path('.tmp')
        result = self.run_app(issue(quantity=3) + '3\nRB101\n6\n')
        self.assertIn('Quantities restored in memory; issue was not saved.', result.stdout)
        self.assertIn('Quantity: 10', result.stdout)
        self.assertNotIn('Quantity: 7', result.stdout)
        self.assertEqual(self.saved(), row())

    def test_failed_backup_keeps_original(self):
        """A backup-path replacement failure restores proposed deductions and keeps the main file."""
        self.seed()
        self.block_path('.bak')
        result = self.run_app(issue(quantity=3) + '3\nRB101\n6\n')
        self.assertIn('Save failed: cannot replace the backup.', result.stdout)
        self.assertIn('Quantity: 10', result.stdout)
        self.assertEqual(self.saved(), row())
        self.assertFalse((self.work / (DATA_FILE + '.tmp')).exists())

    def test_repeated_issues_never_negative(self):
        """After stock reaches zero, further requests cannot make it negative."""
        self.seed(row(quantity=3))
        result = self.run_app(issue(quantity=2) + issue(quantity=1) + issue(quantity=1, answer=None) + '6\n')
        self.assertEqual(result.stdout.count('Issue saved successfully.'), 2)
        self.assertIn('Insufficient valid stock: available=0', result.stdout)
        self.assertEqual(self.quantities(), {'RB101': 0})

    def test_empty_report(self):
        """An empty report gives a no-records message without unnecessary date prompts."""
        result = self.run_app('5\n6\n')
        self.assertIn('No reagent batches found.', result.stdout)
        self.assertNotIn('Report date (', result.stdout)

    def test_stock_report_categories_and_low_threshold(self):
        """The report distinguishes eligible/expired/empty lots and flags valid totals at the threshold."""
        self.seed(row(quantity=10) + row(batch_id='OLD', expiry='2026-10-18', quantity=50) + row(batch_id='EMPTY', quantity=0))
        result = self.run_app('5\n2026-10-19\n10\n6\n')
        self.assertIn('RB101 | GLUCOSE_KIT | ELIGIBLE', result.stdout)
        self.assertIn('OLD | GLUCOSE_KIT | EXPIRED', result.stdout)
        self.assertIn('EMPTY | GLUCOSE_KIT | EMPTY', result.stdout)
        self.assertIn('available=10 packs | LOW (threshold=10)', result.stdout)
        self.assertIn('Batch summary: Eligible=1, Expired=1, Empty=1, Total=3', result.stdout)
        self.assertIn('Low-stock reagent codes: 1', result.stdout)

    def test_report_does_not_mix_product_units(self):
        """Available totals are per reagent code/unit, never one sum of packs and bottles."""
        self.seed(row(quantity=12) + row(batch_id='BUF1', code='BUFFER', name='Buffer', unit='bottles', quantity=5))
        result = self.run_app('5\n2026-10-19\n10\n6\n')
        self.assertIn('GLUCOSE_KIT | Glucose Assay Kit | available=12 packs | OK', result.stdout)
        self.assertIn('BUFFER | Buffer | available=5 bottles | LOW', result.stdout)
        self.assertIn('Low-stock reagent codes: 1', result.stdout)

    def test_zero_report_threshold(self):
        """Threshold zero is allowed and marks an out-of-stock reagent as LOW."""
        self.seed(row(quantity=0))
        result = self.run_app('5\n2026-10-19\n0\n6\n')
        self.assertIn('available=0 packs | LOW (threshold=0)', result.stdout)

    def test_invalid_report_input(self):
        """Invalid report dates/thresholds do not edit saved inventory."""
        self.seed()
        bad_date = self.run_app('5\n2026-02-30\n6\n')
        self.assertIn('Invalid date:', bad_date.stdout)
        bad_threshold = self.run_app('5\n2026-10-19\n-1\n6\n')
        self.assertIn('Invalid quantity:', bad_threshold.stdout)
        self.assertEqual(self.saved(), row())

    def test_large_valid_total_no_overflow(self):
        """The full 300-batch maximum total 300000000 is summed correctly without overflow."""
        content = ''.join(row(batch_id=f'B{i:03}', quantity=1000000) for i in range(300))
        self.seed(content)
        result = self.run_app('5\n2026-10-19\n1000000\n6\n')
        self.assertEqual(result.returncode, 0)
        self.assertIn('available=300000000 packs | OK', result.stdout)
        self.assertEqual(self.saved(), content)

    def test_randomized_fefo_against_python_oracle(self):
        """Fifty fixed-seed mixed inventories match an independent sorted FEFO oracle and conservation rules."""
        rng = random.Random(20261019)
        dates = ['2026-10-01', '2026-10-18', '2026-10-19', '2026-10-21', '2027-01-01']
        for case in range(50):
            with self.subTest(case=case):
                records = []
                for i in range(rng.randint(1, 16)):
                    code = CODE if i == 0 or rng.choice([True, True, False]) else 'BUFFER'
                    records.append(dict(batch_id=f'B{case:02}_{i:02}', code=code,
                                        name=NAME if code == CODE else 'Buffer',
                                        unit='packs' if code == CODE else 'bottles',
                                        expiry=rng.choice(dates), quantity=rng.randint(0, 15)))
                rng.shuffle(records)
                requested = rng.randint(1, 40)
                eligible = sorted([r for r in records if r['code'] == CODE and
                                   r['quantity'] > 0 and r['expiry'] >= '2026-10-19'],
                                  key=lambda r: (r['expiry'], r['batch_id']))
                available = sum(r['quantity'] for r in eligible)
                expected = {r['batch_id']: r['quantity'] for r in records}
                planned = []
                if available >= requested:
                    remaining = requested
                    for record in eligible:
                        amount = min(record['quantity'], remaining)
                        if amount:
                            planned.append((record, amount))
                            expected[record['batch_id']] -= amount
                            remaining -= amount
                        if remaining == 0:
                            break
                content = ''.join(row(**r) for r in records)
                self.seed(content)
                answer = 'y' if available >= requested else None
                result = self.run_app(issue(quantity=requested, answer=answer) + '6\n')
                self.assertEqual(result.returncode, 0)
                self.assertEqual(self.quantities(), expected)
                self.assertTrue(all(q >= 0 for q in expected.values()))
                self.assertEqual([line.split('|')[0] for line in self.saved().splitlines()],
                                 [r['batch_id'] for r in records])
                if available < requested:
                    self.assertIn('Insufficient valid stock:', result.stdout)
                    self.assertEqual(self.saved(), content)
                else:
                    self.assertIn('Issue saved successfully.', result.stdout)
                    self.assertEqual(sum(r['quantity'] for r in records) - sum(expected.values()), requested)
                    for record, amount in planned:
                        self.assertIn(f"{record['batch_id']} | expires {record['expiry']} | issue {amount} packs", result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
