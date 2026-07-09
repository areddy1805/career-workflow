from __future__ import annotations

from pathlib import Path

README = Path("README.md")
MARKER = "## Local Control Center"

SECTION = """
## Local Control Center

Career Workflow includes a local Streamlit control center for:

- pipeline execution and safe dry/live controls;
- process and stage monitoring;
- run artifact inspection;
- job inspection and filtering;
- application tracking and lifecycle history;
- server application reconciliation;
- manual external-job tracking;
- operational review queues;
- application analytics and reports;
- local system health diagnostics;
- safe read-only operational configuration.

Run:

```bash
python -m streamlit run control_center/app.py
```

The control center is a local operational interface over the existing
Career Workflow engine. It does not require a separate backend service.

Live pipeline execution remains explicitly protected by mode selection,
an application ceiling, and confirmation before launch. Runtime data and
local databases remain local and should stay excluded from Git.
"""

if not README.exists():
    raise SystemExit("README.md not found")

content = README.read_text(encoding="utf-8")
if MARKER not in content:
    README.write_text(content.rstrip() + "\n\n" + SECTION.strip() + "\n", encoding="utf-8")
    print("README updated")
else:
    print("README already contains Local Control Center section")
