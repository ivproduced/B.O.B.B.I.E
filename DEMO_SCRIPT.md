# BOBBIE 3-Minute Demo Script

## Objective

Show a complete, evidence-driven 10-control assessment run and resulting remediation artifacts.

## Timing + Talk Track (3:00)

### 0:00-0:20 — Problem + Context

"Federal compliance teams need faster, repeatable control assessments. BOBBIE uses family-based agents to evaluate NIST 800-53 Rev 5 controls with deterministic evidence checks and objective-driven outputs."

### 0:20-0:45 — Architecture in One View

Show:
- `README.md` architecture diagram
- Family-agent routing across active families (AC, AU, CM, IA, PL, PM, RA, SI)

Say:
"The orchestrator dispatches controls by family, isolates failures/timeouts, and aggregates findings into compliance score and POA&M-ready actions."

### 0:45-1:10 — Pre-Demo Confidence Check

Run:

```bash
python scripts/validate_demo_env.py
```

Say:
"This validates required files/dependencies and reports AWS connectivity status with graceful fallback behavior."

### 1:10-2:00 — Live Assessment Run

Run:

```bash
python run_assessment.py --deterministic --output-dir artifacts/demo_run
```

Highlight during output:
- 10 controls assessed
- pass/fail summary
- compliance score
- prioritized findings

### 2:00-2:35 — Artifact Review

Open:
- `artifacts/demo_run/assessment_report.json`
- `artifacts/demo_run/poam.json`
- `artifacts/demo_run/assessment_summary.txt`

Say:
"The output includes machine-readable and human-readable artifacts ready for engineering handoff and remediation tracking."

### 2:35-2:55 — UI Experience (Optional if time permits)

Run:

```bash
streamlit run app.py
```

Show:
- configuration sidebar
- run button
- results + artifact download buttons

### 2:55-3:00 — Close

"BOBBIE demonstrates deterministic, evidence-driven compliance assessment at family-agent scale, with repeatable runs and actionable remediation outputs."

## Presenter Checklist

- Terminal font is readable and zoomed.
- Demo dataset is frozen (`data/demo_frozen/demo_context.json`).
- Commands are pre-staged in a notes window.
- Backup take plan is prepared.
