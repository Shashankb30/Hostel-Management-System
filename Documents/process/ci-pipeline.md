# CI Pipeline and Merge Protection (SETUP.10 · Issue #11)

Traceability: NFR-06, NFR-07 · Test case: `UT_SETUP_08`

## What runs

Workflow: `.github/workflows/ci.yml`, job **Build, Lint & Test Validation**.
It runs on every `pull_request` into `main` or `dev`, and on pushes to those two branches.

| # | Step | Command | Catches |
|---|------|---------|---------|
| 1 | Install | `pip install -r requirements-dev.txt` | Broken or missing dependencies |
| 2 | Lint | `ruff check .` | Syntax errors, unused or undefined names (rules `E9`, `F`, see `ruff.toml`) |
| 3 | Django check | `python manage.py check` | Misconfigured settings, models, apps |
| 4 | SQL schema | `python scripts/verify_schema.py` | Schema constraints in `Documents/design/schema.sql` |
| 5 | Migrate | `python manage.py migrate --noinput` | Migrations failing on an empty database |
| 6 | Tests | `python manage.py test --verbosity 2` | Any failing unit or integration test |

If any step fails, the job fails and the PR shows a red check.

Run the same checks locally before pushing:

```bash
pip install -r requirements-dev.txt
ruff check .
python manage.py check
python scripts/verify_schema.py
python manage.py test
```

## Making a failing check block the merge

A failing workflow only blocks merging when a **branch ruleset** requires it.
(Settings → Rules → Rulesets → New ruleset → New branch ruleset)

| Setting | Value |
|---------|-------|
| Ruleset name | `Protect main` |
| Enforcement status | Active |
| Bypass list | empty |
| Target branches | Add target → Include default branch |
| Restrict deletions | on |
| Require a pull request before merging | on, 1 required approval |
| Require status checks to pass | on, add **Build, Lint & Test Validation** and **Verify PR Traceability & Description** |
| Block force pushes | on |

The check names only appear in the picker after the workflow has run once on a PR.

## Verification (UT_SETUP_08)

1. Open a PR with a deliberately failing test: the **Build, Lint & Test Validation** check turns red and the Merge button is disabled ("Merging is blocked").
2. Close that PR without merging and delete its branch.
3. Open a PR with passing code: all checks turn green and merging is allowed once approved.
