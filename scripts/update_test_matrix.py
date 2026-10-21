#!/usr/bin/env python3
"""Fill the Actual Result and Status columns of TEST_PLAN_MATRIX.md from a real test run.

Every automated test is named after the Test Plan case it checks, for example
``test_UT_02_Login__valid_student_reaches_student_dashboard``. This script runs the
tests, reads the verbose result lines, and updates the matching rows:

    python scripts/update_test_matrix.py                 # run accounts + core tests, update the file
    python scripts/update_test_matrix.py --dry-run       # show what would change, write nothing
    python scripts/update_test_matrix.py --from-file out.txt   # use saved `manage.py test -v 2` output

A row becomes ``Pass`` only when every test carrying its ID passed, and ``Fail`` when
any of them failed or errored. Rows with no automated test are left untouched, so a
row is never marked Pass without a real result behind it.
"""
import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MATRIX = ROOT / 'TEST_PLAN_MATRIX.md'

RESULT_LINE = re.compile(
    r'^(test_\w+) \(([\w.]+)\) \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)\s*$',
    re.MULTILINE)
TEST_ID = re.compile(r'^test_((?:UT|IT|ST)_[A-Za-z0-9]+_[A-Za-z0-9]+)__')
ROW_ID = re.compile(r'^\| \*\*((?:UT|IT|ST)_[A-Za-z0-9]+_[A-Za-z0-9]+)\*\* \| ')
COLUMNS = 9  # Test ID, Module, Description, Pre-conditions, Steps, Data, Expected, Actual, Status


def parse_results(output):
    """Return {test_id: [(dotted_test_name, 'pass' | 'fail'), ...]} from verbose unittest output."""
    results = {}
    for method, dotted, outcome in RESULT_LINE.findall(output):
        found = TEST_ID.match(method)
        if not found:
            continue
        if outcome.startswith('skipped'):
            continue
        status = 'pass' if outcome in ('ok', 'expected failure') else 'fail'
        results.setdefault(found.group(1), []).append((dotted, status))
    return results


def _summary(test_id, tests, today):
    modules = ', '.join(sorted({'.'.join(dotted.split('.')[:2]) for dotted, _ in tests}))
    failed = [dotted for dotted, status in tests if status == 'fail']
    if failed:
        return (f'Automated check on {today}: {len(failed)} of {len(tests)} test(s) FAILED '
                f'(see {modules})', 'Fail')
    return f'Automated check on {today}: {len(tests)} test(s) passed ({modules})', 'Pass'


def update_matrix(text, results, today):
    """Return (new_text, changed_ids, ids_not_in_matrix)."""
    changed, seen = [], set()
    lines = text.split('\n')
    for index, line in enumerate(lines):
        row = ROW_ID.match(line)
        if not row or row.group(1) not in results:
            continue
        test_id = row.group(1)
        seen.add(test_id)
        cells = line[2:].rstrip()
        if cells.endswith(' |'):
            cells = cells[:-2]
        parts = cells.split(' | ')
        if len(parts) != COLUMNS:
            print(f'warning: row {test_id} does not have {COLUMNS} columns; left unchanged',
                  file=sys.stderr)
            continue
        actual, status = _summary(test_id, results[test_id], today)
        parts[7], parts[8] = actual, status
        lines[index] = '| ' + ' | '.join(parts) + ' |'
        changed.append(test_id)
    return '\n'.join(lines), changed, sorted(set(results) - seen)


def run_tests(labels):
    command = [sys.executable, 'manage.py', 'test', *labels, '--verbosity', '2']
    print('Running:', ' '.join(command), flush=True)
    process = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    sys.stdout.write(process.stdout[-3000:])
    return process.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('labels', nargs='*', default=['accounts', 'core'],
                        help='test labels to run (default: accounts core)')
    parser.add_argument('--matrix', type=Path, default=DEFAULT_MATRIX)
    parser.add_argument('--from-file', type=Path, help='read saved verbose test output instead of running')
    parser.add_argument('--dry-run', action='store_true', help='report changes without writing the file')
    args = parser.parse_args(argv)

    output = args.from_file.read_text(encoding='utf-8') if args.from_file else run_tests(args.labels)
    results = parse_results(output)
    if not results:
        print('No Test Plan results found in the test output. Nothing changed.', file=sys.stderr)
        return 1

    original = args.matrix.read_text(encoding='utf-8')
    updated, changed, missing = update_matrix(original, results, date.today().isoformat())
    print(f'\nTest Plan rows updated: {len(changed)}')
    for test_id in changed:
        status = 'Pass' if all(s == 'pass' for _, s in results[test_id]) else 'Fail'
        print(f'  {status:<4}  {test_id}')
    for test_id in missing:
        print(f'  warning: tests mention {test_id} but the matrix has no such row', file=sys.stderr)

    if args.dry_run:
        print('\nDry run: file not written.')
    else:
        args.matrix.write_text(updated, encoding='utf-8')
        print(f'\nWrote {args.matrix}')
    failed = [t for t in changed if any(s == 'fail' for _, s in results[t])]
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
