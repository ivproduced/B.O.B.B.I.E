#!/usr/bin/env python3
"""Quick end-to-end test using mock data files."""
import subprocess
import json
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(BASE, ".venv", "bin", "python")

def run(label, args):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)
    cmd = [PYTHON, "run_assessment.py"] + args
    result = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, timeout=120)
    # Print last 30 lines of output
    lines = (result.stdout + result.stderr).splitlines()
    for line in lines[-30:]:
        print(line)
    return result.returncode

# Run 1: Terraform mock
rc1 = run("Terraform mock", [
    "--infra-source", "terraform",
    "--infra-file", "data/mock/terraform.tfstate",
    "--deterministic",
    "--output-dir", "artifacts/test_tf_run",
    "--system-name", "BOBBIE TF Mock"
])

# Run 2: AWS Config mock
rc2 = run("AWS Config mock", [
    "--infra-source", "aws-config",
    "--infra-file", "data/mock/aws_config_snapshot.json",
    "--deterministic",
    "--output-dir", "artifacts/test_cfg_run",
    "--system-name", "BOBBIE Config Mock"
])

# Check output
print("\n" + "="*60)
print("  Results")
print("="*60)
for run_dir in ["artifacts/test_tf_run", "artifacts/test_cfg_run"]:
    summary_file = os.path.join(BASE, run_dir, "assessment_summary.txt")
    report_file = os.path.join(BASE, run_dir, "assessment_report.json")
    if os.path.exists(report_file):
        with open(report_file) as f:
            data = json.load(f)
        summary = data.get("summary", {})
        print(f"\n{run_dir}:")
        print(f"  Controls: {summary.get('total_controls', '?')}")
        print(f"  Passed:   {summary.get('controls_passed', '?')}")
        print(f"  Failed:   {summary.get('controls_failed', '?')}")
        print(f"  Score:    {summary.get('compliance_score', '?')}")
    else:
        print(f"\n{run_dir}: NO REPORT GENERATED (exit code: {rc1 if 'tf' in run_dir else rc2})")

print(f"\nExit codes: TF={rc1}, Config={rc2}")
