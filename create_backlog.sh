#!/usr/bin/env bash
# Creates the Hostel Management System backlog on GitHub (labels, milestones, epics, sub-issues).
# Usage:   ./create_backlog.sh <owner>/<repo>        (needs: gh CLI, `gh auth login`)
# Preview: DRY_RUN=1 ./create_backlog.sh <owner>/<repo>
set -euo pipefail
REPO="${1:?Usage: ./create_backlog.sh <owner>/<repo>}"
DRY="${DRY_RUN:-0}"
N=0; LAST=0

run() { if [[ "$DRY" == "1" ]]; then echo "[dry-run] $*"; else "$@"; fi; }

label() { run gh label create "$1" --color "$2" --description "$3" --repo "$REPO" --force >/dev/null; }
milestone() { run gh api -X POST "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null 2>&1 || echo "milestone exists: $1"; }

# issue TITLE LABELS MILESTONE BODY [PARENT_NUMBER]  -> sets LAST to the new issue number
issue() {
  local title="$1" labels="$2" ms="$3" body="$4" parent="${5:-}" url cid
  if [[ "$DRY" == "1" ]]; then
    N=$((N+1)); LAST=$N; echo "[dry-run] #$LAST $title  {$labels | $ms}${parent:+  (sub-issue of #$parent)}"; return
  fi
  url=$(gh issue create --repo "$REPO" --title "$title" --label "$labels" --milestone "$ms" --body "$body")
  LAST="${url##*/}"
  echo "created #$LAST  $title"
  if [[ -n "$parent" ]]; then
    cid=$(gh api "repos/$REPO/issues/$LAST" --jq .id)
    gh api -X POST "repos/$REPO/issues/$parent/sub_issues" -F sub_issue_id="$cid" >/dev/null
  fi
  sleep 1   # stay under GitHub's secondary rate limits
}

echo '== Labels =='
label 'epic' 5319E7 'Epic (parent issue)'
label 'story' 1D76DB 'User story'
label 'task' C5DEF5 'Engineering / process task'
label 'nfr' B60205 'Non-functional requirement'
label 'test' FBCA04 'Testing work'
label 'docs' 0E8A16 'Documentation'
label 'inferred' D4C5F9 'Not explicit in the source docs - confirm scope'
label 'P0-critical' B60205 'Must have'
label 'P1-high' D93F0B 'Should have'
label 'P2-normal' FEF2C0 'Nice to have'
label 'role:student' BFD4F2 'Student actor'
label 'role:warden' BFD4F2 'Warden actor'
label 'role:admin' BFD4F2 'Administrator actor'
label 'module:allocation' 006B75 'Module: allocation'
label 'module:attendance' 006B75 'Module: attendance'
label 'module:complaint' 006B75 'Module: complaint'
label 'module:crosscut' 006B75 'Module: crosscut'
label 'module:docs' 006B75 'Module: docs'
label 'module:fee' 006B75 'Module: fee'
label 'module:leave' 006B75 'Module: leave'
label 'module:login' 006B75 'Module: login'
label 'module:nfr' 006B75 'Module: nfr'
label 'module:notice' 006B75 'Module: notice'
label 'module:qa' 006B75 'Module: qa'
label 'module:room' 006B75 'Module: room'
label 'module:setup' 006B75 'Module: setup'
label 'module:student' 006B75 'Module: student'
label 'module:visitor' 006B75 'Module: visitor'

echo '== Milestones =='
milestone 'Sprint 1 - Foundation & Login' 'HMS sprint'
milestone 'Sprint 2 - Students & Rooms' 'HMS sprint'
milestone 'Sprint 3 - Allocation & Fees' 'HMS sprint'
milestone 'Sprint 4 - Discipline & Attendance' 'HMS sprint'
milestone 'Sprint 5 - Visitors, Leave & Notices' 'HMS sprint'
milestone 'Sprint 6 - Hardening & Release' 'HMS sprint'

echo '== Project Foundation & DevOps =='
issue '[EPIC] SETUP - Project Foundation & DevOps' 'epic,module:setup' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**Epic:** Project Foundation & DevOps

Repository, GitHub Project board automation, architecture, database, CI, app shell and shared services that every functional module depends on.

- Requirement: NFR-06, NFR-07
- Use case: -
- Actors: Team

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[SETUP.01] Create GitHub repository with README, .gitignore and branch protection' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a repository with protected `main` so that all work flows through pull requests.

**Acceptance criteria**
- [ ] Repo created with README describing HMS and its 3 roles
- [ ] `main` requires a PR before merging
- [ ] All members added as collaborators

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.02] Add issue templates and PR template that requires a `Fixes #<issue>` keyword' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want issue/PR templates so that every PR is traceable to a backlog item.

**Acceptance criteria**
- [ ] Templates for story, task and bug
- [ ] PR template has a 'Fixes #' line and a test-case checklist
- [ ] Follows the GitHub Projects lab guideline on linking keywords (Fixes / Closes)

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.03] Create the '\''Sprint Board'\'' GitHub Project (v2) with Todo / In Progress / In Review / Done' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a project board linked to the repository so that work status is visible.

**Acceptance criteria**
- [ ] Board template used, named Sprint Board
- [ ] Columns: Todo, In Progress, In Review, Done
- [ ] Project linked to the repository

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.04] Enable GitHub Project workflows (auto-add, default status, PR linking, merge, auto-close)' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want board automation so that status follows real git activity.

**Acceptance criteria**
- [ ] Auto-add to project enabled with filter on this repo
- [ ] Item added -> status Todo
- [ ] Auto-add sub-issues to project enabled
- [ ] PR linked to issue -> In Progress
- [ ] PR merged -> Done
- [ ] Auto-close issue enabled

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.05] Define labels, sprint milestones and Definition of Done' 'task,module:setup,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a shared label set, milestones and DoD so that backlog grooming is consistent.

**Acceptance criteria**
- [ ] Labels for type, module, role, priority (P0-P2)
- [ ] Six sprint milestones created
- [ ] DoD: code reviewed, tests from Test Plan pass, PR merged with `Fixes #N`

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.06] Spike: choose tech stack and high-level architecture' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want an agreed stack and layered/modular architecture so that modules stay independent.

**Acceptance criteria**
- [ ] Decision recorded (ADR) for front end, back end, database
- [ ] Module boundaries match the 10 SRS modules
- [ ] Approach supports adding hostels/modules without redesign (NFR-06, NFR-07)

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.07] Design ER diagram and relational schema' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want a data model covering all modules so that integrity rules can be enforced.

**Acceptance criteria**
- [ ] Entities: User, Student, Room, Allocation, Fee, Payment, Complaint, DemeritRule, Attendance, Visitor, Leave, Notice, Notification
- [ ] Keys/constraints for unique Roll No., Room No., one active allocation per student
- [ ] Diagram committed to the repo

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.08] Implement database schema and migrations' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want a versioned schema so that every environment is reproducible.

**Acceptance criteria**
- [ ] Migrations create all tables with constraints
- [ ] Migrations run cleanly on an empty database

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.09] Create seed / test-data script matching the Test Plan data' 'task,module:setup,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want repeatable seed data so that Test Plan cases can be executed as written.

**Acceptance criteria**
- [ ] Users: stu1023 (student), wdn05 (warden), admin01 (admin), stu9999 (inactive)
- [ ] Students such as Arjun Rao (CSE2201) and Divya S.; rooms A-101 (cap 3), B-204, C-102
- [ ] Script is idempotent

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.10] Set up CI pipeline (build, lint, run tests on every PR)' 'task,module:setup,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want automatic checks on PRs so that broken code is not merged.

**Acceptance criteria**
- [ ] Workflow runs on pull_request
- [ ] Failing tests block merge

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.11] Build application shell: layout, navigation and role-based menus' 'task,module:setup,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want a common layout with menus that depend on the user's role so that modules plug in easily.

**Acceptance criteria**
- [ ] Student / Warden / Administrator menus differ
- [ ] Placeholder dashboard per role
- [ ] Simple, consistent layout (NFR-02)

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.12] Create shared validation and error-message framework' 'task,module:setup,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want consistent validation and messages so that modules report errors the same way.

**Acceptance criteria**
- [ ] Reusable validators (required, numeric, date range, unique)
- [ ] Messages such as 'Room number already exists' are standardised

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[SETUP.13] Create in-app notification service' 'task,module:setup,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want a notification service so that students are told about allocations, complaints and leave decisions.

**Acceptance criteria**
- [ ] API: notify(student, type, message)
- [ ] Notifications persisted and marked read/unread
- [ ] Used by FR-04, FR-06, FR-09

**Traceability**
- Requirement: NFR-06, NFR-07
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== User Login =='
issue '[EPIC] FR-01 - User Login' 'epic,module:login' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**Epic:** User Login

Secure login with unique credentials and role-based access control; redirects each role to its own dashboard.

- Requirement: FR-01 (R1)
- Use case: UC-01
- Actors: Student, Warden, Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-01.01] Display login page with username and password fields' 'story,module:login,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As an **user**, I want to see a login page with Username, Password and Submit.

**Acceptance criteria**
- [ ] Page loads at the application URL
- [ ] Username and Password fields and a Submit button are shown
- [ ] Password input is masked

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: UT_01

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.02] Authenticate valid Student credentials' 'story,module:login,P0-critical,role:student' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to log in with my credentials so that I reach my dashboard.

**Acceptance criteria**
- [ ] Valid credentials (e.g. stu1023) authenticate the user
- [ ] Redirect to the Student dashboard
- [ ] Credentials are validated against stored records

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: UT_02

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.03] Reject invalid credentials with an error message' 'story,module:login,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As an **user**, I want a clear error on wrong credentials so that I can retry.

**Acceptance criteria**
- [ ] Wrong password shows 'Invalid username or password'
- [ ] Access is denied and the user can retry
- [ ] Message does not reveal which field was wrong

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: UT_03

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.04] Role-based redirection to Warden and Administrator dashboards' 'story,module:login,P0-critical,role:warden' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to be redirected to a dashboard with menus for my role.

**Acceptance criteria**
- [ ] wdn05 lands on the Warden dashboard with warden menu
- [ ] admin01 lands on the Administrator dashboard with full admin menu
- [ ] System identifies the role after validation

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: IT_01, IT_02

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.05] Block login for inactive or locked accounts' 'story,module:login,P0-critical' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** The **system** shall deny access to inactive or locked accounts so that only active users get in.

**Acceptance criteria**
- [ ] Login for stu9999 is refused
- [ ] Message states the account is inactive/locked and why
- [ ] No session is created

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: IT_03

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.06] Validate empty credentials before authenticating' 'story,module:login,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As an **user**, I want validation on blank fields so that I don't submit an empty form.

**Acceptance criteria**
- [ ] Blank username/password shows validation errors
- [ ] No authentication attempt is made

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: ST_02

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.07] Maintain session across module navigation' 'story,module:login,P0-critical,role:student' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to stay logged in while moving between modules.

**Acceptance criteria**
- [ ] Navigating Fee Management -> Notices does not re-prompt for login
- [ ] Session ends on logout or timeout

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: ST_01

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.08] Logout' 'story,module:login,P1-high,inferred' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As an **user**, I want to log out so that my session is closed safely.

**Acceptance criteria**
- [ ] Logout ends the session
- [ ] Back button does not reopen protected pages

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.09] Forgot password / password reset flow' 'story,module:login,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As an **user**, I want to reset a forgotten password so that I can regain access.

**Acceptance criteria**
- [ ] 'Forgot Password' link on login page (alternate flow 3a)
- [ ] Reset completes without submitting normal credentials
- [ ] Add matching test cases (not in current Test Plan)

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.10] Administrator manages user accounts and roles' 'story,module:login,P1-high,role:admin,inferred' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to create, deactivate and reactivate user accounts and assign roles.

**Acceptance criteria**
- [ ] Unique usernames enforced
- [ ] Role is one of Student/Warden/Administrator
- [ ] Deactivated accounts cannot log in (see IT_03)

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: IT_03
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-01.11] Lock account after repeated failed logins' 'story,module:login,P2-normal,inferred' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** The **system** shall lock an account after repeated failed logins so that brute-force attempts are limited.

**Acceptance criteria**
- [ ] Threshold configurable
- [ ] Locked message shown (UC-01 exception 4b)
- [ ] Administrator can unlock

**Traceability**
- Requirement: FR-01 (R1)
- Use case: UC-01
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Student Registration =='
issue '[EPIC] FR-02 - Student Registration' 'epic,module:student' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**Epic:** Student Registration

Administrator adds, updates and maintains student personal, academic and contact details.

- Requirement: FR-02 (R2)
- Use case: UC-02
- Actors: Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-02.01] Add New Student form shows all required fields' 'story,module:student,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want an Add Student form so that I can capture student details.

**Acceptance criteria**
- [ ] Fields: Name, Roll No., Contact, Address, Course, Year
- [ ] Reachable via Student Management -> Add New Student

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: UT_04

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.02] Register student with valid data and generate unique Student ID' 'story,module:student,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to save a valid student so that a record and unique ID are created.

**Acceptance criteria**
- [ ] Save creates the record
- [ ] Unique Student ID generated
- [ ] Success confirmation displayed

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: UT_05

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.03] Reject duplicate Roll Number / Student ID / email' 'story,module:student,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want duplicates to be blocked so that no student is recorded twice.

**Acceptance criteria**
- [ ] 'Roll number already exists' shown for CSE2201 duplicate
- [ ] Submission blocked
- [ ] Errors highlighted (UC-02 exception 5a)

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: UT_06

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.04] Validate mandatory fields on registration' 'story,module:student,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want required fields to be enforced so that incomplete records are not saved.

**Acceptance criteria**
- [ ] Blank Name and Roll No. are highlighted
- [ ] Save is prevented

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: ST_04

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.05] Validate contact number format' 'story,module:student,P1-high,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want phone validation so that only valid contact numbers are stored.

**Acceptance criteria**
- [ ] 'abcde12' is rejected with a format error
- [ ] Valid 10-digit number accepted

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: IT_06

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.06] Update an existing student'\''s details' 'story,module:student,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to search a student and edit details such as phone so that records stay current.

**Acceptance criteria**
- [ ] Edit phone to 9123456789 and save
- [ ] Change appears in the student list
- [ ] Same validation rules as create

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: IT_04

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.07] Search and filter students by name' 'story,module:student,P1-high,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to search by name so that I find records quickly.

**Acceptance criteria**
- [ ] Searching 'Arjun' lists matching students
- [ ] Empty result handled gracefully

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: ST_03

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.08] Make newly registered students eligible in Room Allocation' 'story,module:student,P0-critical,role:warden' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want new students without a room to appear as candidates so that I can allocate them.

**Acceptance criteria**
- [ ] Registered-but-unallocated student appears in allocation module

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: IT_05

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.09] Student profile page (room, fees, attendance, visitors, complaints, leave)' 'story,module:student,P1-high,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a single profile view so that I see everything about a student.

**Acceptance criteria**
- [ ] Attendance and visitor entries appear only under the correct student
- [ ] Sections link to their modules

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: IT_21, IT_23

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.10] Create login credentials linked to the student record' 'story,module:student,P1-high,role:admin,inferred' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want an account created with the student so that they can log in.

**Acceptance criteria**
- [ ] Username linked one-to-one to the student
- [ ] Initial password flow defined

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-02.11] Deactivate / archive a student record' 'story,module:student,P2-normal,role:admin,inferred' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to deactivate a student who leaves so that active lists stay accurate.

**Acceptance criteria**
- [ ] Deactivated student cannot log in
- [ ] Room released (see FR-04 vacate story)

**Traceability**
- Requirement: FR-02 (R2)
- Use case: UC-02
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Room Management =='
issue '[EPIC] FR-03 - Room Management' 'epic,module:room' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**Epic:** Room Management

Maintain room inventory (number, capacity, type) and keep vacancy/occupancy status up to date.

- Requirement: FR-03 (R3)
- Use case: UC-03
- Actors: Administrator (Warden: view / update availability)

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-03.01] Add room with number, capacity and type' 'story,module:room,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to add a room so that it can be allocated.

**Acceptance criteria**
- [ ] A-101, capacity 3, Triple saves successfully
- [ ] New room status is 'Vacant'

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: UT_07

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.02] Reject duplicate room number' 'story,module:room,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want duplicate room numbers to be blocked so that every room is unique.

**Acceptance criteria**
- [ ] 'Room number already exists' shown for A-101
- [ ] Creation blocked

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: UT_08

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.03] Validate capacity is a positive integer' 'story,module:room,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want capacity validation so that rooms are meaningful.

**Acceptance criteria**
- [ ] -2 and 0 rejected with validation error
- [ ] Non-numeric rejected

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: UT_09

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.04] Edit room details' 'story,module:room,P1-high,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to change room number, capacity and type.

**Acceptance criteria**
- [ ] Same validation as create
- [ ] Changes saved and listed

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: IT_09

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.05] Auto-update occupancy and vacancy status' 'story,module:room,P0-critical' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** The **system** shall update occupancy and vacancy status automatically after allocation, transfer or vacating.

**Acceptance criteria**
- [ ] A-101 with 1/3 occupied shows '2 vacant' after one more allocation
- [ ] Status Vacant/Partially/Full derived from occupancy

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: IT_07

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.06] Exclude fully occupied rooms from allocation lists' 'story,module:room,P0-critical,role:warden' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want full rooms hidden from allocation so that I cannot pick them.

**Acceptance criteria**
- [ ] A-101 at 3/3 is not in the vacant room list

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: IT_08

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.07] Room detail changes reflect in the student'\''s room view' 'story,module:room,P1-high,role:student' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to see up-to-date room information.

**Acceptance criteria**
- [ ] Type change to 'Deluxe Triple' visible to allocated student

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: IT_09

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.08] Student views own allocated room details' 'story,module:room,P1-high,role:student' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to see my room number, type and roommates' count.

**Acceptance criteria**
- [ ] Shown on student dashboard / room page
- [ ] Empty state when not allocated

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: IT_09

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.09] Filter rooms by vacancy status' 'story,module:room,P1-high,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to filter 'Vacant only' so that I find rooms with space.

**Acceptance criteria**
- [ ] Only rooms with available capacity listed

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: ST_05

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.10] Prevent deletion of occupied rooms; deactivate unoccupied rooms' 'story,module:room,P0-critical,role:admin' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want rooms to be removed only when nobody lives in them.

**Acceptance criteria**
- [ ] Delete on A-101 with occupants is blocked with a reassign message
- [ ] Unoccupied room can be deleted/deactivated

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: ST_06

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.11] Warden views and updates room availability' 'story,module:room,P1-high,role:warden' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to view rooms and update availability.

**Acceptance criteria**
- [ ] Warden menu shows room availability
- [ ] Update rules as for Administrator

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-03.12] Prevent lowering capacity below current occupancy' 'story,module:room,P1-high,role:admin,inferred' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want capacity not to drop below current occupancy.

**Acceptance criteria**
- [ ] Reduction below occupants rejected with message

**Traceability**
- Requirement: FR-03 (R3)
- Use case: UC-03
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Room Allocation =='
issue '[EPIC] FR-04 - Room Allocation' 'epic,module:allocation' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**Epic:** Room Allocation

Warden allocates rooms to students based on vacancy and priority rules, including transfers.

- Requirement: FR-04 (R4)
- Use case: UC-04
- Actors: Warden

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-04.01] Show vacant rooms for a selected student' 'story,module:allocation,P0-critical,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to select a student and see suggested vacant rooms.

**Acceptance criteria**
- [ ] Only rooms with available capacity are listed

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: UT_10

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.02] Allocate a vacant room to a student' 'story,module:allocation,P0-critical,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to allocate e.g. B-204 to Divya S.

**Acceptance criteria**
- [ ] Allocation saved
- [ ] Student record shows B-204
- [ ] Vacancy decreases by 1

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: UT_11

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.03] Define and store allocation priority rules' 'story,module:allocation,P1-high,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want priority rules (e.g. seniority, category) configurable.

**Acceptance criteria**
- [ ] Rules stored and editable
- [ ] Rules documented in SRS after clarification

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: UT_12

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.04] Apply priority rules when allocating' 'story,module:allocation,P1-high,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want seniors prioritised over juniors.

**Acceptance criteria**
- [ ] Junior before senior on waitlist is flagged
- [ ] Vacant rooms ordered by rules

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: UT_12

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.05] Maintain waitlist of unallocated students' 'story,module:allocation,P2-normal,role:warden,inferred' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a waitlist so that requests are handled in order.

**Acceptance criteria**
- [ ] Add/remove from waitlist
- [ ] Ordered by priority

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: UT_12
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.06] Block allocation to full/unavailable room and refresh list' 'story,module:allocation,P0-critical,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want full rooms to be blocked.

**Acceptance criteria**
- [ ] 'Room unavailable' shown for full B-204
- [ ] Vacancy list refreshes (UC-04 exception 5a)

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: IT_10

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.07] Prevent second allocation; require transfer' 'story,module:allocation,P0-critical,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want already-allocated students to need a transfer.

**Acceptance criteria**
- [ ] Allocating B-204 student to C-102 is redirected to transfer

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: IT_11

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.08] Room transfer between rooms' 'story,module:allocation,P0-critical,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to transfer a student between rooms.

**Acceptance criteria**
- [ ] Student moves B-204 -> C-102
- [ ] Old vacancy +1, new vacancy -1
- [ ] Transfer confirmed before saving

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: IT_12

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.09] Notify student of allocation or transfer' 'story,module:allocation,P1-high,role:student' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to be notified of my room.

**Acceptance criteria**
- [ ] Notification created (UC-04 step 6)

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.10] Handle '\''no vacant rooms'\'' gracefully' 'story,module:allocation,P1-high,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a friendly message when everything is full.

**Acceptance criteria**
- [ ] 'No vacant rooms available' shown; no error/crash

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: ST_08

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.11] Allocation history / report' 'story,module:allocation,P1-high,role:warden' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want an allocation report for a date range/semester.

**Acceptance criteria**
- [ ] Lists students, rooms and dates

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: ST_07

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.12] Prevent concurrent over-allocation of the last bed' 'story,module:allocation,P1-high,inferred' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** The **system** shall handle concurrent allocations safely so that a room's capacity is never exceeded.

**Acceptance criteria**
- [ ] Transaction/locking ensures capacity never exceeded
- [ ] Second warden sees exception flow 5a

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: IT_10
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-04.13] Vacate / release a room' 'story,module:allocation,P2-normal,role:warden,inferred' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to release a room when a student leaves.

**Acceptance criteria**
- [ ] Occupancy decreases; status updated

**Traceability**
- Requirement: FR-04 (R4)
- Use case: UC-04
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Fee Management =='
issue '[EPIC] FR-05 - Fee Management' 'epic,module:fee' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**Epic:** Fee Management

Record hostel fee payments and maintain payment status (Paid / Partially Paid / Due).

- Requirement: FR-05 (R5)
- Use case: UC-05
- Actors: Administrator, Student

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-05.01] Define fee structure for a student' 'story,module:fee,P0-critical,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to set the fee structure so that balances can be computed.

**Acceptance criteria**
- [ ] Total fee per student stored
- [ ] Editable with validation

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_13

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.02] View fee details: total, paid and outstanding' 'story,module:fee,P0-critical,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to see the fee summary for a student.

**Acceptance criteria**
- [ ] Total, paid and outstanding balance displayed

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_13

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.03] Record full payment' 'story,module:fee,P0-critical,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to record a payment equal to the balance.

**Acceptance criteria**
- [ ] Amount 50000 Online saves
- [ ] Status 'Paid'
- [ ] Receipt generated

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_14

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.04] Record partial payment' 'story,module:fee,P0-critical,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to record part payment.

**Acceptance criteria**
- [ ] 20000 of 50000 -> 'Partially Paid'
- [ ] Balance recalculated to 30000

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_15

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.05] Reject payment exceeding balance' 'story,module:fee,P0-critical,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want payments larger than the due balance to be blocked so that the ledger stays consistent.

**Acceptance criteria**
- [ ] 15000 vs due 10000 rejected
- [ ] Validation error displayed

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: IT_13

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.06] Reject negative or non-numeric payment amounts' 'story,module:fee,P0-critical,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want negative or non-numeric amounts to be blocked so that the ledger stays valid.

**Acceptance criteria**
- [ ] -500 and 'abc' rejected

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: IT_14

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.07] Compute payment status Due / Partially Paid / Paid' 'story,module:fee,P0-critical' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** The **system** shall recompute the payment status (Due, Partially Paid, Paid) after every payment.

**Acceptance criteria**
- [ ] Status recalculated on every payment

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_14, UT_15

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.08] Generate receipt for each payment' 'story,module:fee,P1-high,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a receipt for each payment so that there is proof of payment.

**Acceptance criteria**
- [ ] Receipt has student, amount, date, mode
- [ ] Printable/PDF

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_14

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.09] Student views own fee status, balance and history' 'story,module:fee,P0-critical,role:student' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to see my payments.

**Acceptance criteria**
- [ ] Recorded payment reflected immediately
- [ ] View-only, no edit

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: IT_15

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.10] Payment history in chronological order' 'story,module:fee,P1-high,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a payment history with dates, amounts and modes so that I can audit transactions.

**Acceptance criteria**
- [ ] All entries correct and sorted

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: ST_09

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.11] Prevent duplicate payment submission' 'story,module:fee,P1-high,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want resubmitted or double-clicked payments to be caught so that no payment is recorded twice.

**Acceptance criteria**
- [ ] Duplicate blocked or warned

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: ST_10

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.12] Record payment mode' 'story,module:fee,P1-high,role:admin' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to select the payment mode (e.g. Online) when recording a payment.

**Acceptance criteria**
- [ ] Modes configurable (e.g. Online); required field

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: UT_14

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-05.13] Outstanding dues report' 'story,module:fee,P2-normal,role:admin,inferred' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a report of students with outstanding dues so that I can follow up.

**Acceptance criteria**
- [ ] Filter by status
- [ ] Export

**Traceability**
- Requirement: FR-05 (R5)
- Use case: UC-05
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Complaint Management =='
issue '[EPIC] FR-06 - Complaint Management' 'epic,module:complaint' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**Epic:** Complaint Management

Record complaints and misconduct cases, assign severity and cumulative demerit points, track status and notify students.

- Requirement: FR-06 (R6)
- Use case: UC-06
- Actors: Student, Warden, Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-06.01] Student submits a complaint' 'story,module:complaint,P0-critical,role:student' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to submit a complaint with a category and description so that hostel staff can act on it.

**Acceptance criteria**
- [ ] Category (e.g. Maintenance, Discipline) and description are captured
- [ ] Complaint saved with status 'Open', a unique complaint ID and the date
- [ ] Confirmation is shown to the student

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: UT_16

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.02] Validate incomplete complaints' 'story,module:complaint,P0-critical,role:student' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **student**, I want the complaint form to reject a blank description so that incomplete complaints are never recorded.

**Acceptance criteria**
- [ ] Blank description shows a validation error
- [ ] Submission is blocked until required fields are filled (UC-06 exception 4a)

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: UT_17

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.03] Warden / Administrator logs a misconduct case' 'story,module:complaint,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to log a misconduct case against a student so that discipline is tracked.

**Acceptance criteria**
- [ ] Warden or Administrator can create the case
- [ ] Student, date, category and description are recorded
- [ ] Case appears in the complaint list

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_16

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.04] Filter and view complaints by status' 'story,module:complaint,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to filter complaints by status so that I can work through the open ones.

**Acceptance criteria**
- [ ] Filter 'Open' lists all open complaints
- [ ] Each row shows the student and category

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: UT_18

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.05] Configure severity levels and demerit-point rules' 'story,module:complaint,P0-critical,role:admin' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to configure severity levels and their demerit points so that penalties are applied consistently.

**Acceptance criteria**
- [ ] Levels (e.g. Minor, Major) with their points are stored
- [ ] Values are editable by the Administrator
- [ ] Actual point values agreed and recorded in the SRS (currently undefined)

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_16

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.06] Assign severity and auto-assign demerit points' 'story,module:complaint,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to pick a severity when reviewing a complaint so that demerit points are assigned automatically.

**Acceptance criteria**
- [ ] Selecting 'Major' assigns the predefined points
- [ ] Points are stored against the student and the complaint

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_16

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.07] Accumulate demerit points per student' 'story,module:complaint,P0-critical' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** The **system** shall add new demerit points to a student's running total so that repeat offences are visible.

**Acceptance criteria**
- [ ] A student with 2 points plus a new 3-point case shows 5
- [ ] Total is visible to Warden and Administrator

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_18

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.08] Update status Open / Under Review / Resolved with remarks' 'story,module:complaint,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to move a complaint through Open, Under Review and Resolved with remarks so that its progress is clear.

**Acceptance criteria**
- [ ] Status and remarks are saved
- [ ] Student sees the updated status and remarks on their dashboard

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_17

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.09] Notify student of complaint outcome' 'story,module:complaint,P1-high,role:student' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to be notified when my complaint's status changes so that I know the outcome.

**Acceptance criteria**
- [ ] Notification created on each status change (UC-06 step 6)
- [ ] Appears in the notification inbox

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_17

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.10] Escalate repeated or severe complaint to the administrator' 'story,module:complaint,P2-normal,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to escalate a repeated or severe complaint so that the administrator can take further action.

**Acceptance criteria**
- [ ] Escalate action available on a complaint
- [ ] Administrator can see escalated items
- [ ] Add a matching test case (none in the Test Plan)

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.11] Prevent editing resolved complaints without reopening' 'story,module:complaint,P1-high,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want resolved complaints to be locked so that history is not altered by accident.

**Acceptance criteria**
- [ ] Editing a resolved complaint's description is blocked
- [ ] A Reopen action returns it to Open / Under Review

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: ST_12

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.12] Student views own complaints and demerit points' 'story,module:complaint,P1-high,role:student' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to view my complaints and demerit total so that I can follow their status.

**Acceptance criteria**
- [ ] List of my complaints with status and remarks
- [ ] Total demerit points shown
- [ ] No access to other students' complaints

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: IT_17

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-06.13] Complaint summary report by category' 'story,module:complaint,P1-high,role:admin' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a complaint summary grouped by category so that I can spot recurring problems.

**Acceptance criteria**
- [ ] Counts grouped by Maintenance, Discipline and other categories
- [ ] Numbers match the seeded data

**Traceability**
- Requirement: FR-06 (R6)
- Use case: UC-06
- Test Plan cases: ST_11

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Attendance Management =='
issue '[EPIC] FR-07 - Attendance Management' 'epic,module:attendance' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**Epic:** Attendance Management

Maintain student attendance from recorded check-in and check-out times.

- Requirement: FR-07 (R7)
- Use case: UC-07
- Actors: Warden, Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-07.01] Record student check-in' 'story,module:attendance,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to record a student's check-in so that arrivals are timestamped.

**Acceptance criteria**
- [ ] Select a student and mark Check-in; the time (e.g. 08:00 PM) is stored
- [ ] Administrator has the same ability

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: UT_19

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.02] Record student check-out' 'story,module:attendance,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to record a student's check-out so that the attendance entry is completed.

**Acceptance criteria**
- [ ] Check-out (e.g. 09:30 AM next day) is saved on the open entry
- [ ] Entry is marked complete

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: UT_20

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.03] Flag duplicate check-in without check-out' 'story,module:attendance,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a second check-in without a check-out to be flagged so that attendance stays consistent.

**Acceptance criteria**
- [ ] No duplicate open entry is created
- [ ] Inconsistency message shown (UC-07 exception 4a)

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: UT_21

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.04] Error when checking out without an active check-in' 'story,module:attendance,P0-critical,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a clear error when I check out a student who has no active check-in.

**Acceptance criteria**
- [ ] Error says no active check-in exists
- [ ] No record is created

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: ST_14

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.05] Restrict attendance to students with an allocated room' 'story,module:attendance,P1-high' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** The **system** shall offer attendance marking only for registered students who have an allocated room.

**Acceptance criteria**
- [ ] Unallocated students are not selectable
- [ ] Matches the documented UC-07 pre-condition

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.06] Bulk attendance marking' 'story,module:attendance,P1-high,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to mark check-in for many students at once so that group arrivals are quick.

**Acceptance criteria**
- [ ] Selecting 10 students and choosing bulk check-in records all of them
- [ ] Duplicate rule applies to each student

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: IT_20

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.07] Daily attendance summary (present / absent)' 'story,module:attendance,P1-high,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a daily attendance summary so that I can see who is present or absent.

**Acceptance criteria**
- [ ] Summary lists present/absent per student for the day
- [ ] Present/absent rule confirmed and added to the SRS (open question)

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: IT_19

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.08] Attendance history on the student profile' 'story,module:attendance,P1-high,role:admin' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want each student's attendance history on their profile so that I can review their record.

**Acceptance criteria**
- [ ] Entries appear only under the correct student

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: IT_21

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-07.09] Attendance report by date range' 'story,module:attendance,P1-high,role:warden' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want an attendance report filtered by date range.

**Acceptance criteria**
- [ ] Range 'last 7 days' returns only records in that range

**Traceability**
- Requirement: FR-07 (R7)
- Use case: UC-07
- Test Plan cases: ST_13

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Visitor Management =='
issue '[EPIC] FR-08 - Visitor Management' 'epic,module:visitor' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**Epic:** Visitor Management

Record and update visitor check-in and check-out details.

- Requirement: FR-08 (R8)
- Use case: UC-08
- Actors: Administrator, Warden

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-08.01] Add Visitor form' 'story,module:visitor,P0-critical,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want an Add Visitor form so that I can capture visitor details.

**Acceptance criteria**
- [ ] Fields: visitor name, ID proof, purpose and student visited
- [ ] Warden can also record visitors

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: UT_22

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.02] Visitor check-in with timestamp' 'story,module:visitor,P0-critical,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to check a visitor in so that the visit is logged with a timestamp.

**Acceptance criteria**
- [ ] Ramesh Kumar visiting Arjun Rao gets a check-in timestamp
- [ ] Entry is saved to the visitor log

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: UT_23

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.03] Reject check-in with missing mandatory details' 'story,module:visitor,P0-critical,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want check-in to be blocked when mandatory details such as ID proof are missing.

**Acceptance criteria**
- [ ] Blank ID proof shows a validation error
- [ ] No log entry is created (UC-08 exception 3a)

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: UT_24

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.04] Visitor check-out updates the same log entry' 'story,module:visitor,P0-critical,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to record a visitor's departure on the same log entry so that visit duration is known.

**Acceptance criteria**
- [ ] Check-out time saved on the active entry
- [ ] Visit duration is calculated

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: IT_22

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.05] Prevent double check-out' 'story,module:visitor,P1-high,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want an already checked-out entry to be protected so that visit times are not overwritten.

**Acceptance criteria**
- [ ] Second check-out attempt is blocked
- [ ] A clear message is shown

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: ST_16

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.06] Link visitor log to the visited student' 'story,module:visitor,P1-high,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want each visitor entry linked to the visited student so that a student's visitors can be reviewed.

**Acceptance criteria**
- [ ] Entry appears in Arjun Rao's visitor history

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: IT_23

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.07] Search visitor logs by student or date' 'story,module:visitor,P1-high,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to search visitor logs by student name or date so that I can trace visits.

**Acceptance criteria**
- [ ] Searching 'Arjun Rao' returns only matching entries
- [ ] Date filter supported (UC-08 alternate flow 2a)

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: IT_24

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-08.08] Visitor report for a date range' 'story,module:visitor,P2-normal,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a visitor report for a date range so that I can review visits over time.

**Acceptance criteria**
- [ ] Lists all entries with check-in/out times in the range
- [ ] Report can be exported

**Traceability**
- Requirement: FR-08 (R8)
- Use case: UC-08
- Test Plan cases: ST_15

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Home / Long-Leave Application =='
issue '[EPIC] FR-09 - Home / Long-Leave Application' 'epic,module:leave' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**Epic:** Home / Long-Leave Application

Students apply for long leave; warden or administrator review, approve or reject, and the records are maintained.

- Requirement: FR-09 (R9)
- Use case: UC-09
- Actors: Student, Warden, Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-09.01] Submit leave application' 'story,module:leave,P0-critical,role:student' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to submit a leave application with dates and a reason so that the warden can review it.

**Acceptance criteria**
- [ ] From, To and Reason are captured
- [ ] Saved with status 'Pending'

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: UT_25

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.02] Validate leave date range' 'story,module:leave,P0-critical,role:student' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **student**, I want the form to reject an end date before the start date so that invalid leave is not recorded.

**Acceptance criteria**
- [ ] From 15-Sep to 10-Sep is rejected
- [ ] Decide whether past dates are allowed (Test Plan dates are in Sep 2026)

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: UT_26

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.03] Require a leave reason' 'story,module:leave,P0-critical,role:student' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **student**, I want the reason to be mandatory so that reviewers have context.

**Acceptance criteria**
- [ ] Blank reason shows a validation error
- [ ] Submission is blocked

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: UT_27

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.04] Warden reviews pending applications' 'story,module:leave,P0-critical,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a list of pending leave applications so that I can review them.

**Acceptance criteria**
- [ ] Pending applications listed with student, dates and reason
- [ ] Administrator can also review and maintain records

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: IT_25

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.05] Approve application and notify student' 'story,module:leave,P0-critical,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to approve a pending application so that the student is cleared to leave.

**Acceptance criteria**
- [ ] Status becomes 'Approved'
- [ ] Student is notified
- [ ] Decision is recorded

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: IT_25

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.06] Reject application with remarks' 'story,module:leave,P0-critical,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to reject an application with remarks so that the student knows why.

**Acceptance criteria**
- [ ] Rejection remarks are required
- [ ] Status 'Rejected' and remarks visible to the student
- [ ] Student is notified

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: IT_26

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.07] Flag overlapping leave dates' 'story,module:leave,P1-high,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want overlaps with an approved leave to be flagged so that I do not approve conflicting dates.

**Acceptance criteria**
- [ ] 12-18 Sep against an approved 10-15 Sep is flagged before approval (UC-09 exception 3a)

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: IT_27

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.08] Request more information from the student' 'story,module:leave,P2-normal,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to return an application to the student asking for more information.

**Acceptance criteria**
- [ ] Return action with a message
- [ ] Student can update and resubmit
- [ ] Add a test case (none in the Test Plan)

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.09] Student leave application history' 'story,module:leave,P1-high,role:student' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **student**, I want to see my past and current applications so that I can track their status.

**Acceptance criteria**
- [ ] All applications shown with dates and status

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: ST_17

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-09.10] Administrator consolidated leave records' 'story,module:leave,P1-high,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want a consolidated list of all students' leave records.

**Acceptance criteria**
- [ ] Lists status and dates for all students

**Traceability**
- Requirement: FR-09 (R9)
- Use case: UC-09
- Test Plan cases: ST_18

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Notice / Information Management =='
issue '[EPIC] FR-10 - Notice / Information Management' 'epic,module:notice' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**Epic:** Notice / Information Management

Maintain and publish hostel notices visible to the intended audience.

- Requirement: FR-10 (R10)
- Use case: UC-10
- Actors: Warden, Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[FR-10.01] Create and publish a notice' 'story,module:notice,P0-critical,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to create and publish a notice with a title and content so that students get important information.

**Acceptance criteria**
- [ ] Title and content are required
- [ ] Notice is stored with a timestamp
- [ ] Administrator can do the same

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: UT_28

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.02] Validate empty notice title or content' 'story,module:notice,P0-critical,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want publishing to be blocked when required fields are empty.

**Acceptance criteria**
- [ ] Blank title shows a validation error
- [ ] Blank content is rejected (UC-10 exception 3a)

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: UT_29

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.03] Show published notices on the student dashboard' 'story,module:notice,P0-critical,role:student' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **student**, I want new notices to appear on my dashboard so that I see hostel announcements.

**Acceptance criteria**
- [ ] A published 'Hostel Maintenance' notice is visible after login

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: UT_30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.04] Target audience for notices' 'story,module:notice,P1-high,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to choose the target audience so that only relevant students see a notice.

**Acceptance criteria**
- [ ] Audience options defined (e.g. all students, block, year) - clarify with the team
- [ ] Non-target students do not see the notice

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: UT_30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.05] Edit an existing notice' 'story,module:notice,P1-high,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to edit a published notice so that information stays correct.

**Acceptance criteria**
- [ ] Students see the updated content

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: IT_28

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.06] Delete or expire a notice' 'story,module:notice,P1-high,role:admin' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want to delete or expire a notice so that outdated information disappears.

**Acceptance criteria**
- [ ] Removed notice no longer appears on the student dashboard
- [ ] Expiry date is optional

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: IT_29

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.07] Order notices newest first' 'story,module:notice,P1-high,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want notices listed newest first so that recent information is on top.

**Acceptance criteria**
- [ ] List is in descending publish-date order

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: IT_30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.08] Search notices by keyword' 'story,module:notice,P2-normal,role:warden' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want to search notices by keyword.

**Acceptance criteria**
- [ ] Keyword 'Maintenance' returns only matching notices

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: ST_19

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.09] Restrict notice authoring to Warden and Administrator' 'story,module:notice,P0-critical' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** The **system** shall allow only Warden and Administrator roles to create, edit or delete notices.

**Acceptance criteria**
- [ ] Students cannot see the creation option
- [ ] Direct URL access by a student is denied

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: ST_20

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[FR-10.10] Student notices page' 'story,module:notice,P1-high,role:student' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **student**, I want a page listing all notices so that I can read past announcements.

**Acceptance criteria**
- [ ] Shows current notices newest first

**Traceability**
- Requirement: FR-10 (R10)
- Use case: UC-10
- Test Plan cases: UT_30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Dashboards, Reports & Notifications =='
issue '[EPIC] X - Dashboards, Reports & Notifications' 'epic,module:crosscut' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**Epic:** Dashboards, Reports & Notifications

Role dashboards, a reports hub, shared export and the student notification inbox that tie the modules together.

- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Actors: Student, Warden, Administrator

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[X.01] Student dashboard' 'story,module:crosscut,P0-critical,role:student' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **student**, I want a dashboard showing my room, fee status, latest notices, complaints and leave status.

**Acceptance criteria**
- [ ] Sections use data from FR-03, FR-05, FR-06, FR-09 and FR-10
- [ ] Empty states are handled

**Traceability**
- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Test Plan cases: UT_30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[X.02] Warden dashboard' 'story,module:crosscut,P1-high,role:warden,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **warden**, I want a dashboard with pending leave, open complaints, vacancy and today's attendance.

**Acceptance criteria**
- [ ] Each widget links to its module

**Traceability**
- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[X.03] Administrator dashboard' 'story,module:crosscut,P1-high,role:admin,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want an overview of totals (students, rooms, dues) with quick links.

**Acceptance criteria**
- [ ] Totals match module data

**Traceability**
- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[X.04] Reports hub' 'story,module:crosscut,P1-high,role:admin' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want one page linking every report so that I can find them easily.

**Acceptance criteria**
- [ ] Links: allocation, fee history, complaint summary, attendance, visitor log, leave records

**Traceability**
- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Test Plan cases: ST_07, ST_09, ST_11, ST_13, ST_15

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[X.05] Reusable CSV / PDF export' 'story,module:crosscut,P2-normal,role:admin,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As an **administrator**, I want reports to be exportable as CSV or PDF.

**Acceptance criteria**
- [ ] One shared export component used by all reports

**Traceability**
- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Test Plan cases: ST_15
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[X.06] Student notification inbox' 'story,module:crosscut,P1-high,role:student' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **student**, I want an inbox for my notifications so that I can see allocation, complaint and leave updates.

**Acceptance criteria**
- [ ] Read / unread state
- [ ] Unread count badge

**Traceability**
- Requirement: SRS section 4 (user-wise summary)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Non-Functional Requirements =='
issue '[EPIC] NFR - Non-Functional Requirements' 'epic,module:nfr' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**Epic:** Non-Functional Requirements

Security, usability, performance, reliability, data integrity, maintainability, scalability and availability.

- Requirement: NFR-01 to NFR-08
- Use case: -
- Actors: All

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[NFR.01] NFR-01: Enforce role-based access control on every route and API' 'nfr,module:nfr,P0-critical' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** The **system** shall check the caller's role on every endpoint so that only permitted users can act.

**Acceptance criteria**
- [ ] Server-side role checks on all endpoints
- [ ] A Student calling Warden/Administrator endpoints is denied

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: ST_20

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.02] NFR-01: Secure password storage and session handling' 'nfr,module:nfr,P0-critical,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** The **system** shall store passwords hashed and expire idle sessions.

**Acceptance criteria**
- [ ] No plain-text passwords
- [ ] Session timeout configured

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: ST_01
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.03] NFR-01: Students can only see their own records' 'nfr,module:nfr,P0-critical' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** The **system** shall restrict students to their own room, fee, complaint and leave data.

**Acceptance criteria**
- [ ] Cross-student access is denied
- [ ] Covered by tests

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.04] NFR-01: Input sanitisation against injection and XSS' 'nfr,module:nfr,P1-high,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** The **system** shall sanitise all user input and use parameterised queries.

**Acceptance criteria**
- [ ] No string-built SQL
- [ ] Output is escaped

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.05] NFR-02: Usability review with sample users' 'nfr,module:nfr,P2-normal' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a usability check so that staff need minimal training.

**Acceptance criteria**
- [ ] At least 3 sample users complete key tasks unaided
- [ ] Findings logged as issues

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.06] NFR-03: Performance baseline under 3 seconds' 'nfr,module:nfr,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** The **system** shall respond to login, search, room allocation and record updates in under 3 seconds under normal load.

**Acceptance criteria**
- [ ] Timings measured and recorded
- [ ] Slow paths are logged as bugs

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.07] NFR-03: Database indexes and paginated lists' 'nfr,module:nfr,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want indexes on lookup columns and paginated lists so that large tables stay fast.

**Acceptance criteria**
- [ ] Indexes on Roll No., Room No., dates and status columns
- [ ] Long lists are paginated

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.08] NFR-04: Backup and restore procedure' 'nfr,module:nfr,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a documented backup and restore procedure so that data loss is minimised.

**Acceptance criteria**
- [ ] Backup taken and a restore test performed
- [ ] Procedure documented

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.09] NFR-04: Transactional writes and graceful failure handling' 'nfr,module:nfr,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** The **system** shall wrap multi-step updates in transactions and show friendly errors on failure.

**Acceptance criteria**
- [ ] Allocation, transfer and payment roll back on error
- [ ] No stack traces shown to users

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.10] NFR-05: Database constraints and server-side integrity rules' 'nfr,module:nfr,P0-critical' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want constraints and validation that prevent duplicate students, invalid allocations and inconsistent payment or leave records.

**Acceptance criteria**
- [ ] Unique constraints on Roll No. and Room No.
- [ ] Foreign keys everywhere
- [ ] Rules enforced server-side, not only in the UI

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: UT_06, UT_08, IT_10, IT_13

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.11] NFR-06: Modular code structure and coding standards' 'nfr,module:nfr,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want modules organised so that new hostel functions can be added with minimal impact.

**Acceptance criteria**
- [ ] One module per SRS function
- [ ] Linter and code-review checklist in place

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.12] NFR-07: Support multiple hostels or blocks in the data model' 'nfr,module:nfr,P2-normal' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want hostel/block as a first-class attribute so that the system scales with the institution.

**Acceptance criteria**
- [ ] Rooms belong to a hostel/block
- [ ] Reports can filter by hostel

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[NFR.13] NFR-08: Health check and maintenance-window handling' 'nfr,module:nfr,P2-normal' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a health endpoint and a planned-downtime approach so that the system is available during working hours.

**Acceptance criteria**
- [ ] Health check endpoint
- [ ] Maintenance notice can be published via the Notice module

**Traceability**
- Requirement: NFR-01 to NFR-08
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Testing & Quality Assurance =='
issue '[EPIC] QA - Testing & Quality Assurance' 'epic,module:qa' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**Epic:** Testing & Quality Assurance

Execute the 80 Test Plan cases (30 unit, 30 integration, 20 system) across 10 modules and record results.

- Requirement: Test Plan (80 cases)
- Use case: -
- Actors: Team

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[QA.01] Set up test framework and fixtures' 'test,module:qa,P0-critical' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want a test framework wired to the seed data so that Test Plan cases can be automated.

**Acceptance criteria**
- [ ] Runs locally and in CI
- [ ] Fixtures load the seed data

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.02] Execute Login test cases' 'test,module:qa,P1-high' 'Sprint 1 - Foundation & Login' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_01-03, IT_01-03, ST_01-02 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_01-03, IT_01-03, ST_01-02

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.03] Execute Student Registration test cases' 'test,module:qa,P1-high' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_04-06, IT_04-06, ST_03-04 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_04-06, IT_04-06, ST_03-04

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.04] Execute Room Management test cases' 'test,module:qa,P1-high' 'Sprint 2 - Students & Rooms' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_07-09, IT_07-09, ST_05-06 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_07-09, IT_07-09, ST_05-06

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.05] Execute Room Allocation test cases' 'test,module:qa,P1-high' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_10-12, IT_10-12, ST_07-08 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_10-12, IT_10-12, ST_07-08

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.06] Execute Fee Management test cases' 'test,module:qa,P1-high' 'Sprint 3 - Allocation & Fees' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_13-15, IT_13-15, ST_09-10 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_13-15, IT_13-15, ST_09-10

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.07] Execute Complaint Management test cases' 'test,module:qa,P1-high' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_16-18, IT_16-18, ST_11-12 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_16-18, IT_16-18, ST_11-12

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.08] Execute Attendance Management test cases' 'test,module:qa,P1-high' 'Sprint 4 - Discipline & Attendance' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_19-21, IT_19-21, ST_13-14 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_19-21, IT_19-21, ST_13-14

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.09] Execute Visitor Management test cases' 'test,module:qa,P1-high' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_22-24, IT_22-24, ST_15-16 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_22-24, IT_22-24, ST_15-16

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.10] Execute Leave Application test cases' 'test,module:qa,P1-high' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_25-27, IT_25-27, ST_17-18 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_25-27, IT_25-27, ST_17-18

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.11] Execute Notice Management test cases' 'test,module:qa,P1-high' 'Sprint 5 - Visitors, Leave & Notices' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want to execute UT_28-30, IT_28-30, ST_19-20 and record the Actual Result and Test Result columns so that the module is verified.

**Acceptance criteria**
- [ ] All 8 cases executed
- [ ] Actual Result and Test Result filled in the Test Plan
- [ ] Failures logged as bug issues

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_28-30, IT_28-30, ST_19-20

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.12] Automate the 30 unit tests' 'test,module:qa,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want UT_01-UT_30 automated so that regressions are caught early.

**Acceptance criteria**
- [ ] All 30 unit cases automated
- [ ] Run on every PR

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: UT_01-30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.13] Automate the 30 integration tests' 'test,module:qa,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want IT_01-IT_30 automated so that module interactions stay correct.

**Acceptance criteria**
- [ ] All 30 integration cases automated
- [ ] Run on every PR

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: IT_01-30

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.14] Automate the 20 system tests' 'test,module:qa,P2-normal' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want ST_01-ST_20 automated as end-to-end checks.

**Acceptance criteria**
- [ ] All 20 system cases automated or documented as manual

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: ST_01-20

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.15] Add missing test cases for coverage gaps' 'test,module:qa,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want extra cases for behaviour the Test Plan does not cover.

**Acceptance criteria**
- [ ] Forgot password
- [ ] Complaint escalation
- [ ] Leave request-more-info
- [ ] Notifications
- [ ] NFR checks

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.16] Bug template and triage routine' 'test,module:qa,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want a bug template and triage routine so that defects show up on the board.

**Acceptance criteria**
- [ ] Template includes test case ID and steps
- [ ] Bugs labelled and prioritised

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[QA.17] Regression run and final test summary report' 'test,module:qa,P0-critical' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **tester**, I want a full regression run and summary so that release readiness is clear.

**Acceptance criteria**
- [ ] All 80 cases re-run
- [ ] Pass/fail summary per module

**Traceability**
- Requirement: Test Plan (80 cases)
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo '== Documentation & Requirement Clarifications =='
issue '[EPIC] DOC - Documentation & Requirement Clarifications' 'epic,module:docs' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**Epic:** Documentation & Requirement Clarifications

Resolve document inconsistencies, keep traceability and produce setup and user documentation.

- Requirement: All
- Use case: -
- Actors: Team

Child stories are attached as **sub-issues** (they are auto-added to the Sprint Board).
Close this epic only when every sub-issue is Done.
__BODY__
)"
EPIC=$LAST
issue '[DOC.01] Spike: resolve requirement ambiguities' 'docs,module:docs,P0-critical' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want answers to the open questions so that implementation is not guesswork.

**Acceptance criteria**
- [ ] Allocation priority rules
- [ ] Demerit points per severity
- [ ] How present/absent is derived
- [ ] Whether past leave dates are allowed
- [ ] Notification channel
- [ ] Notice audience options
- [ ] SRS updated with the answers

**Traceability**
- Requirement: All
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[DOC.02] Align use case diagram with SRS and Use Case Flow' 'docs,module:docs,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a corrected diagram so that actor-to-use-case links match the SRS.

**Acceptance criteria**
- [ ] Student not linked to Registration/Allocation unless intended
- [ ] Add Student and Warden links to Notices as needed
- [ ] Add Administrator link to Complaints and Warden link to Room Management

**Traceability**
- Requirement: All
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[DOC.03] Requirements traceability matrix' 'docs,module:docs,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a matrix from FR to use case to test case to issue.

**Acceptance criteria**
- [ ] Every FR maps to a UC, its test cases and issue numbers

**Traceability**
- Requirement: All
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[DOC.04] README and setup guide' 'docs,module:docs,P1-high' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **developer**, I want install and run steps so that anyone can start the project.

**Acceptance criteria**
- [ ] Prerequisites, setup, seed data and test commands

**Traceability**
- Requirement: All
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[DOC.05] User manual per role' 'docs,module:docs,P2-normal,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a short manual for Student, Warden and Administrator.

**Acceptance criteria**
- [ ] One page per role with screenshots

**Traceability**
- Requirement: All
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"
issue '[DOC.06] Final demo and report' 'docs,module:docs,P1-high,inferred' 'Sprint 6 - Hardening & Release' "$(cat <<'__BODY__'
**User story:** As a **team member**, I want a demo script and report for the final review.

**Acceptance criteria**
- [ ] Demo covers the 10 modules
- [ ] Board screenshots showing the automation flow

**Traceability**
- Requirement: All
- Use case: -
- Test Plan cases: none in the current Test Plan (add one)
- Note: **inferred** - not stated explicitly in the SRS/Use Case docs; confirm scope with the team.

**Definition of Done**
- [ ] Code reviewed and merged via PR containing `Fixes #<this issue number>`
- [ ] Related Test Plan cases executed and Actual/Test Result recorded
- [ ] Board shows the card in Done
__BODY__
)" "$EPIC"

echo 'Done. Open the Sprint Board - everything should be in Todo.'
