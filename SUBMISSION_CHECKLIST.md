# BOBBIE Submission Checklist

Use this checklist to complete and validate final hackathon submission packaging.

## A. Required Assets

- [ ] Public or shareable repository link is ready.
- [x] `README.md` includes setup, architecture, and run commands.
- [x] `DEMO_SCRIPT.md` is finalized for 3-minute narrative.
- [ ] Demo video is recorded.
- [ ] Demo video backup take is recorded.
- [ ] Final video is edited and uploaded.
- [ ] Submission form fields are complete.

## B. Technical Validation

- [x] `python scripts/validate_demo_env.py` passes required file/dependency checks.
- [x] `python scripts/run_dry_runs.py` completes 3/3 deterministic runs.
- [x] `pytest -q` passes on final branch.
- [x] `python run_assessment.py --deterministic` generates expected artifacts.

## C. Artifact Verification

- [x] `assessment_report.json` present and readable.
- [x] `poam.json` present and readable.
- [x] `assessment_summary.txt` present and readable.
- [x] Dry-run report exists: `artifacts/dry_runs/dry_run_report.md`.
- [x] Frozen context and snapshots are included under `data/demo_frozen/`.

## D. Judging Criteria Review

- [ ] Problem statement is clearly explained in demo intro.
- [ ] Technical implementation is demonstrably functional.
- [ ] Deterministic, evidence-driven assessment is shown with real outputs.
- [ ] Business/mission value and user outcome are clearly stated.
- [ ] Architecture and scalability path (20-family target) are communicated.

## E. Final Go/No-Go

- [ ] A teammate can run setup + assessment using only `README.md`.
- [ ] A full dry run is completed within demo time budget.
- [ ] No blocker defects remain open.
- [ ] Submission assets are published and links are verified.

## Current Status Notes (Latest Run)

- `pytest -q`: 38 passed.
- `python3 scripts/run_dry_runs.py`: completed 3/3 runs, 10/10 controls passed each run.
- `.venv/bin/python scripts/validate_demo_env.py`: required files/dependencies passed; AWS credentials not configured in current environment.
- `.venv/bin/python run_assessment.py --deterministic --output-dir artifacts/final_run`: completed; artifacts generated under `artifacts/final_run`.
