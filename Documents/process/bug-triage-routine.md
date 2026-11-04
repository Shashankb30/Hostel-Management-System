# Defect & Bug Triage Routine

## 1. Overview
This document outlines the standard bug filing, categorization, and triage lifecycle for the Hostel Management System (HMS), satisfying **QA.16 (Issue #172)**.

## 2. Bug Issue Template
Defects must be logged using the GitHub issue template at [`.github/ISSUE_TEMPLATE/bug_report.yml`](../../.github/ISSUE_TEMPLATE/bug_report.yml).

### Mandatory Fields
- **Bug Summary**: Concise, high-signal description of the defect.
- **Steps to Reproduce**: Minimal, deterministic steps (1, 2, 3...).
- **Expected vs Actual Behavior**: Contrast what the spec/Test Plan states vs actual observed behavior.
- **Severity**:
  - `P0-critical`: System crash, security flaw, data corruption, or blocker of critical path (e.g. login, payment loss).
  - `P1-high`: Major feature impairment without immediate workaround (e.g. room allocation blockage, wrong calculation).
  - `P2-normal`: Non-critical functional anomaly, cosmetic UI glitch, or minor edge case with available workaround.
- **Environment**: OS, browser version, database engine, Python/Django version.
- **Related Test Plan Case(s)**: Exact Test ID from `TEST_PLAN_MATRIX.md` (e.g., `UT_03_Login`, `IT_13_Fee`), or `None`.

## 3. Triage & Lifecycle Flow
1. **Intake & Labeling**:
   - New issues automatically receive the `bug` label.
   - During weekly/sprint triage, issues are confirmed, prioritized (`P0-critical`, `P1-high`, `P2-normal`), and tagged with the relevant module (e.g., `module:fees`, `module:qa`).
2. **Assignment**: Assigned to the module owner (`@Shashankb30` or `@abhijeetcyalgi`).
3. **Resolution**: Fix implemented on a branch, verified with an automated test case, and merged via PR referencing `Fixes #<issue_number>`.
4. **Closing**: GitHub Project workflows automatically mark the card as `Done` and close the issue upon PR merge to `main`.
