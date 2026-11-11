## Documentation and reports (`docs/`)
| File | Content |
|---|---|
| `docs/SRS.md`, `.docx` | Software Requirements Specification (IEEE 830) |
| `docs/SAD.md`, `.docx` | Software Architecture & Design (IEEE 1016 / 42010) |
| `docs/Test_Plan.md`, `.docx` | Test Plan (IEEE 829) with SRS traceability |
| `docs/DEVIATIONS.md` | Deviations from the submitted documents |
| `docs/CHECKLIST_STATUS.md` | Evaluation checklist status |
| `docs/reports/` | Unit, system validation, code coverage, branch coverage reports |
| `docs/videos/` | Sprint 1 (1 min) and Sprint 2 (2 min) demo videos — add before the viva |

Reproduce the reports: `coverage run manage.py test && coverage report && coverage html`
