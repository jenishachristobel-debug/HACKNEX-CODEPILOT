import json
from datetime import datetime
from typing import Dict, Any


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Produces a clean, human-readable verification report in Markdown."""
    created_at = report_data.get("timestamp", datetime.utcnow().isoformat())
    task = report_data.get("task", {})
    project = report_data.get("project", {})
    verification = report_data.get("verification", {})
    baseline = report_data.get("baseline_tests", {})
    post_patch = report_data.get("post_patch_tests", {})
    diff = report_data.get("patch_diff", "")

    md = f"""# CodePilot AI — Evidence-Based Verification Report

**Project**: {project.get('name', 'N/A')}  
**Task ID**: {task.get('id', 'N/A')}  
**Date**: {created_at}  
**Classification**: `{verification.get('classification', 'PENDING')}`  

---

## 1. Executive Summary
- **Bug Title**: {task.get('bug_title', '')}
- **Root Cause**: {report_data.get('root_cause_summary', 'N/A')}
- **Target File**: `{report_data.get('target_file', 'N/A')}`
- **Verification Result**: **{verification.get('classification', 'UNKNOWN')}**

---

## 2. Evidence Breakdown
| Metric | Status | Evidence Details |
|---|---|---|
| **Functional Verification** | `{verification.get('functional_status', 'N/A')}` | Tests target bug reproduction assertion |
| **Regression Guardian** | `{verification.get('regression_status', 'N/A')}` | Zero baseline tests regressed from pre-patch state |
| **Syntax Validation** | `{verification.get('syntax_status', 'N/A')}` | AST parsed without syntax or token errors |
| **Security & Sandbox** | `{verification.get('security_status', 'N/A')}` | Isolated execution without privileged escapes |

---

## 3. Test Suite Comparison
- **Baseline Test Run**:
  - Exit Code: `{baseline.get('exit_code', 'N/A')}`
  - Tests Passed: `{baseline.get('passed_count', 0)}`
  - Tests Failed: `{baseline.get('failed_count', 0)}`
  - Duration: `{baseline.get('duration_ms', 0)}ms`

- **Post-Patch Test Run**:
  - Exit Code: `{post_patch.get('exit_code', 'N/A')}`
  - Tests Passed: `{post_patch.get('passed_count', 0)}`
  - Tests Failed: `{post_patch.get('failed_count', 0)}`
  - Duration: `{post_patch.get('duration_ms', 0)}ms`

---

## 4. Proposed & Applied Patch
```diff
{diff if diff else "# No diff available"}
```

---

## 5. Audit & Compliance
- **Sandbox Mode**: `{report_data.get('execution_mode', 'safe_local')}`
- **Repair Attempts**: `{task.get('current_attempt', 1)} / {task.get('max_attempts', 2)}`
- **Certified By**: CodePilot AI Autonomous Verification Engine
"""
    return md

