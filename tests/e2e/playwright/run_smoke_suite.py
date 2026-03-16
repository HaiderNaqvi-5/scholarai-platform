from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "public_scholarship_browse_smoke.py",
    "auth_dashboard_smoke.py",
    "seeded_recommendations_smoke.py",
    "document_feedback_smoke.py",
    "interview_practice_smoke.py",
    "curation_smoke.py",
]


def main() -> int:
    failures: list[str] = []

    for script_name in SCRIPTS:
        script_path = ROOT / script_name
        print(f"RUN {script_name}")
        completed = subprocess.run([sys.executable, str(script_path)], cwd=ROOT.parent.parent.parent)
        if completed.returncode == 0:
            print(f"PASS {script_name}\n")
            continue

        failures.append(script_name)
        print(f"FAIL {script_name} (exit {completed.returncode})\n")

    if failures:
        print("Smoke suite completed with failures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Smoke suite completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
