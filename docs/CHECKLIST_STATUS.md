# Evaluation checklist — corrected status (2026-11-05)

Legend: **Done** = satisfied by the files in this package · **Verify** = true in the repo but must be checked on GitHub · **YOU** = cannot be produced from source code; action needed.

## Part 1 — Requirements & Design documents
| Item | Status | Evidence |
|---|---|---|
| SRS in IEEE format | Done | `docs/SRS.md` / `.docx` (sections 1–4, IEEE 830) |
| Introductory + descriptive sections | Done | SRS §1 Introduction, §2 Overall description |
| FRs and NFRs clear and measurable | Done | SRS §3.2 (FR-01..10 with IDs + verification), §3.4 (NFR-01..08 with measure column) |
| ≥ 1 UML use case diagram | Done | SRS Figure 1 (`docs/diagrams/uc_diagram.png`) |
| Security: ≥ 2 objectives and ≥ 2 requirements | Done | SRS §3.5: SO-1..4, SR-1..7 |
| Test Plan in IEEE format | Done | `docs/Test_Plan.md` / `.docx` (IEEE 829 sections 1–8) |
| Sections 3, 4, 5 filled | Done | §3 features, §4 approach/criteria, §5 cases. **If your course template numbers sections differently, keep the content and renumber.** |
| Section 5.1 security validation | Done | Test Plan §5.1 (SEC-01..10) |
| Traceability to SRS | Done | SRS column on every case + §6 matrix |
| 7–10 minimum cases, FR + NFR | Done | 80 core + 21 extension + NFR cases (§5.2, 5.3) |
| SAD in IEEE format | Done | `docs/SAD.md` / `.docx` (IEEE 1016 / 42010) |
| Components, pattern, traceability, security architecture | Done | SAD §4.1–4.7, §5 |
| ≥ 2 sequence diagrams | Done | SAD §6.2: SD-1 login/lock-out, SD-2 allocation, SD-3 payment |
| API design, error-handling protocol | Done | SAD §6.3 (80 routes, generated from code), §6.4 |

## Part 2 — Agile planning and repository
| Item | Status | Evidence / action |
|---|---|---|
| GitHub Project linked to repo | Verify | `create_backlog.sh`, `scripts/sync_all_backlog.py` exist; check the board on GitHub |
| Backlog items from FRs/NFRs | Verify | `BACKLOG_SPRINT_PLAN.md` (180 issues); confirm they exist as issues |
| Story points on all items | Verify | Plan assigns points (total 579); confirm every issue has the field set |
| Assigned to members | Verify | Plan splits between two members; confirm assignees |
| Sprint 1 and 2 planned | Verify | Sprint 1: 19–23 Oct, Sprint 2: 26–30 Oct in plan |
| GitHub Actions enabled | Done in repo / Verify run | `.github/workflows/ci.yml` (+ coverage step in this package), `pr-automation.yml`; check the Actions tab is green |
| Code matches SRS/SAD | Done | Compared module by module; differences in `docs/DEVIATIONS.md` |
| PRs raised by assignee; reviewed/merged by owner | **YOU / Verify** | Needs git history (not in zip). Run `git log --format="%an|%s" --shortstat` and check PR list |
| 1-minute Sprint 1 video | **YOU** | Record and commit (e.g. `docs/videos/sprint1.mp4` or link in README) |
| Sprint 2 frozen; deviations documented | Done | `docs/DEVIATIONS.md` (tag a `sprint-2-freeze` release) |
| Documentation finalised | Done | SRS, Test Plan, SAD v2.0 |
| 2-minute Sprint 2 video | **YOU** | Record and commit |

## Part 3 — Testing and QA
| Item | Status | Evidence |
|---|---|---|
| Test cases updated for sprint changes | Done | Test Plan v2.0 §5.2.1 extension cases + RBAC matrix test |
| All tests executed per plan | Done | 681 tests (incl. 2 new RBAC-matrix tests), 0 failures — team's own run, 2026-11-06 (`docs/reports/unit-test-report.md`) |
| Unit test report in `docs/` | Done | `docs/reports/unit-test-report.md` |
| System validation report in `docs/` | Done | `docs/reports/system-validation-report.md` |
| Code coverage report in `docs/` | Done | `docs/reports/code-coverage-report.md` + `coverage/html` + `coverage.xml` — statement 94.9 % |
| Branch coverage report in `docs/` | Done | `docs/reports/branch-coverage-report.md` — branch 84.2 % |

## Part 4 — Final evaluation
| Item | Status | Note |
|---|---|---|
| App functions as designed, core use cases | Done | All 10 modules run; tests pass; `manage.py check` clean |
| Deviations explained | Done | `docs/DEVIATIONS.md` — read §A and §B before the demo |
| Code accessible, readable, version-controlled | Done / Verify | ruff clean; layered structure; confirm history on GitHub |
| Members explain own code and PRs | **YOU** | See viva list below |
| Agile/SDLC understanding | **YOU** | Be ready to defend estimates (579 points / 2 weeks), blockers |
| Justify architecture, API, tests | Done (material) | SAD §4–6, Test Plan §4 |

## Viva questions to prepare (from the code)
1. Why a layered monolith and not microservices? (SAD §4.1)
2. How does `allocate()` prevent two wardens filling the last bed? (`select_for_update` + `transaction.atomic`, SD-2)
3. How does `record_payment()` stop double submission and overpayment? (row lock, 30 s duplicate window, SD-3)
4. Why does the account stay locked until an admin unlocks it, and how does it differ from the first SAD? (D-01)
5. What does 84 % branch coverage miss, and why? (lowest: leave and notice views)
6. Which requirements have no automated test? (NFR-02 usability, NFR-06 cycle check — manual)
7. README mentions audit logs, visitor passes, curfew logs: are they built? (No — D-07..D-12; say so first)
8. Which code was AI-generated, and how did you check it against the SRS/SAD/Test Plan?
