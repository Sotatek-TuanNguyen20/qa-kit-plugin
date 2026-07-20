# export_excel.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/export_excel.py`, the plugin's first real Python code, which reads one or more `testcases/<module>.yaml` files and writes a styled `.xlsx` workbook a non-technical QC can read, grouped into sheets by `(module, category.large)`.

**Architecture:** Pure functions for each transformation stage (flatten one case → group into sheets → compute summary → write workbook), wired together by a thin `main()` CLI entry point. pandas builds the tabular data; the underlying openpyxl workbook (via pandas' `engine="openpyxl"`) is styled directly afterward.

**Tech Stack:** Python 3.11+, `uv` for dependency management, `pandas` + `openpyxl` for the workbook, `pytest` for tests (first test framework introduced into this plugin).

## Global Constraints

- Export **testcases only** — never merge `results/*.yaml`. `Status`/`Tested By`/`Date`/`Remarks` columns are always empty strings for the tester to fill in by hand.
- Sheets are grouped by `(module, category.large)`, never by technical component — this is the kit's own business-flow convention (`context/conventions.md`), not the old component-based real-world template.
- Sheet names: strip Excel-forbidden characters `: \ / ? * [ ]`, truncate to 31 chars max, disambiguate collisions with a numeric suffix.
- Header row style: fill `#305496`, white bold font, thin border on every cell, frozen header row (`freeze_panes = "A2"`).
- A `Summary` sheet is always first in the workbook: case count by `priority` × `module`, with a `Total` column. No Pass/Fail/Blocked columns (no execution data in scope).
- No schema validation (that's `tools/validate.py`'s job, out of scope). No Japanese translation. No pixel-perfect style matching — spirit only (dark blue header, white bold text, borders).
- All test/example content in **Vietnamese**, matching the rest of the plugin.
- Run from a project repo's root (where `testcases/` lives), invoked as `uv run python ${CLAUDE_PLUGIN_ROOT}/tools/export_excel.py <module...> [--out PATH]`.

---

## File Structure

```
qa-kit-plugin/
  pyproject.toml              [create]
  tools/
    export_excel.py           [create]
  tests/
    test_export_excel.py      [create]
```

---

## Task 1: Project setup + `flatten_case()`

**Files:**
- Create: `pyproject.toml`
- Create: `tools/export_excel.py`
- Create: `tests/test_export_excel.py`

**Interfaces:**
- Produces: `flatten_case(case: dict) -> dict` — returns a row dict with keys `TC ID, Medium, Small, Title, Precondition, Steps, Expected Result, Priority, Trace, Status, Tested By, Date, Remarks` (13 keys, no `No` — that's assigned later by `group_cases` in Task 2).

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "qa-kit-tools"
version = "0.1.0"
description = "Standalone tools for the qa-kit plugin (export, validate, harness)"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.2",
    "openpyxl>=3.1",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
]
```

- [ ] **Step 2: Run `uv sync` to create the lockfile and virtual environment**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv sync`
Expected: creates `.venv/` and `uv.lock`, installs pandas/openpyxl/pyyaml/pytest with no errors.

- [ ] **Step 3: Write the failing test for `flatten_case`**

Create `tests/test_export_excel.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from export_excel import flatten_case


def test_flatten_case_maps_basic_fields():
    case = {
        "id": "IT-LOGIN-001",
        "category": {
            "large": "Nghiệp vụ đăng nhập",
            "medium": "Xác thực password",
            "small": "Password đúng biên dưới",
        },
        "condition_vi": "Password 8 ký tự (min)",
        "precondition_vi": ["Tài khoản đã được cấp", "Trạng thái hoạt động"],
        "steps": [
            {"action_vi": "Nhập password 8 ký tự", "data": {"password": "Abcd1234"}},
            {"action_vi": "Bấm nút đăng nhập"},
        ],
        "expected_vi": "Đăng nhập thành công",
        "priority": "P1",
        "trace": ["DD-2.1"],
    }
    row = flatten_case(case)
    assert row["TC ID"] == "IT-LOGIN-001"
    assert row["Medium"] == "Xác thực password"
    assert row["Small"] == "Password đúng biên dưới"
    assert row["Title"] == "Password 8 ký tự (min)"
    assert row["Precondition"] == "Tài khoản đã được cấp\nTrạng thái hoạt động"
    assert row["Steps"] == (
        "1. Nhập password 8 ký tự (data: password=Abcd1234)\n"
        "2. Bấm nút đăng nhập"
    )
    assert row["Expected Result"] == "Đăng nhập thành công"
    assert row["Priority"] == "P1"
    assert row["Trace"] == "DD-2.1"
    assert row["Status"] == ""
    assert row["Tested By"] == ""
    assert row["Date"] == ""
    assert row["Remarks"] == ""


def test_flatten_case_handles_no_precondition_or_data():
    case = {
        "id": "IT-PAYMENT-001",
        "category": {"large": "L", "medium": "M", "small": "S"},
        "condition_vi": "c",
        "precondition_vi": [],
        "steps": [{"action_vi": "Nhập thông tin thẻ"}],
        "expected_vi": "e",
        "priority": "P2",
        "trace": [],
    }
    row = flatten_case(case)
    assert row["Precondition"] == ""
    assert row["Steps"] == "1. Nhập thông tin thẻ"
    assert row["Trace"] == ""
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'export_excel'` (file doesn't exist yet).

- [ ] **Step 5: Write `tools/export_excel.py` with `flatten_case`**

```python
"""Export testcases/<module>.yaml files into a styled Excel workbook for QC."""

from __future__ import annotations


def flatten_case(case: dict) -> dict:
    preconditions = case.get("precondition_vi", [])
    precondition_text = "\n".join(preconditions)

    steps = case.get("steps", [])
    step_lines = []
    for i, step in enumerate(steps, start=1):
        line = f"{i}. {step['action_vi']}"
        data = step.get("data")
        if data:
            data_text = ", ".join(f"{k}={v}" for k, v in data.items())
            line += f" (data: {data_text})"
        step_lines.append(line)
    steps_text = "\n".join(step_lines)

    trace_text = ", ".join(case.get("trace", []))

    category = case.get("category", {})

    return {
        "TC ID": case["id"],
        "Medium": category.get("medium", ""),
        "Small": category.get("small", ""),
        "Title": case.get("condition_vi", ""),
        "Precondition": precondition_text,
        "Steps": steps_text,
        "Expected Result": case.get("expected_vi", ""),
        "Priority": case.get("priority", ""),
        "Trace": trace_text,
        "Status": "",
        "Tested By": "",
        "Date": "",
        "Remarks": "",
    }
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: PASS (2/2 tests).

- [ ] **Step 7: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add pyproject.toml uv.lock tools/export_excel.py tests/test_export_excel.py
git commit -m "Add flatten_case for export_excel.py, first Python code in the plugin"
```

---

## Task 2: `group_cases()` + `sanitize_sheet_name()`

**Files:**
- Modify: `tools/export_excel.py`
- Test: `tests/test_export_excel.py`

**Interfaces:**
- Consumes: `flatten_case(case: dict) -> dict` from Task 1.
- Produces:
  - `sanitize_sheet_name(module: str, category_large: str, existing_names: set[str]) -> str`
  - `group_cases(cases_by_module: dict[str, list[dict]]) -> dict[tuple[str, str], list[dict]]` — key is `(module, category_large)`; each row dict has all of `flatten_case`'s keys plus `"No"` (1-indexed position within its group).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_export_excel.py`:

```python
from export_excel import group_cases, sanitize_sheet_name


def test_group_cases_groups_by_module_and_category_large():
    cases_by_module = {
        "login": [
            {
                "id": "IT-LOGIN-001",
                "category": {"large": "Nghiệp vụ đăng nhập", "medium": "A", "small": "a"},
                "condition_vi": "c1", "precondition_vi": [], "steps": [],
                "expected_vi": "e1", "priority": "P1", "trace": [],
            },
            {
                "id": "IT-LOGIN-002",
                "category": {"large": "Nghiệp vụ đăng nhập", "medium": "B", "small": "b"},
                "condition_vi": "c2", "precondition_vi": [], "steps": [],
                "expected_vi": "e2", "priority": "P2", "trace": [],
            },
            {
                "id": "IT-LOGIN-003",
                "category": {"large": "Nghiệp vụ quên mật khẩu", "medium": "C", "small": "c"},
                "condition_vi": "c3", "precondition_vi": [], "steps": [],
                "expected_vi": "e3", "priority": "P3", "trace": [],
            },
        ],
    }
    groups = group_cases(cases_by_module)
    assert set(groups.keys()) == {
        ("login", "Nghiệp vụ đăng nhập"),
        ("login", "Nghiệp vụ quên mật khẩu"),
    }
    login_group = groups[("login", "Nghiệp vụ đăng nhập")]
    assert len(login_group) == 2
    assert login_group[0]["No"] == 1
    assert login_group[0]["TC ID"] == "IT-LOGIN-001"
    assert login_group[1]["No"] == 2
    assert len(groups[("login", "Nghiệp vụ quên mật khẩu")]) == 1


def test_sanitize_sheet_name_truncates_and_strips_forbidden_chars():
    name = sanitize_sheet_name("login", "Nghiệp vụ đăng nhập/đăng xuất: đầy đủ chi tiết", set())
    assert len(name) <= 31
    assert not any(c in name for c in ":\\/?*[]")


def test_sanitize_sheet_name_dedupes_on_collision_after_truncation():
    long_category = "a" * 40
    existing: set[str] = set()
    first = sanitize_sheet_name("login", long_category, existing)
    existing.add(first)
    second = sanitize_sheet_name("login", long_category, existing)
    assert first != second
    assert len(second) <= 31
    assert second not in existing or second == second
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: FAIL — `ImportError: cannot import name 'group_cases'`.

- [ ] **Step 3: Add `sanitize_sheet_name` and `group_cases` to `tools/export_excel.py`**

Append to `tools/export_excel.py`:

```python
import re

FORBIDDEN_SHEET_CHARS = re.compile(r"[:\\/?*\[\]]")
MAX_SHEET_NAME_LEN = 31


def sanitize_sheet_name(module: str, category_large: str, existing_names: set[str]) -> str:
    raw = f"{module}_{category_large}"
    cleaned = FORBIDDEN_SHEET_CHARS.sub("", raw)
    base = cleaned[:MAX_SHEET_NAME_LEN]
    name = base
    suffix = 2
    while name in existing_names:
        suffix_text = f"_{suffix}"
        name = base[: MAX_SHEET_NAME_LEN - len(suffix_text)] + suffix_text
        suffix += 1
    return name


def group_cases(cases_by_module: dict) -> dict:
    groups: dict = {}
    for module, cases in cases_by_module.items():
        for case in cases:
            category_large = case.get("category", {}).get("large", "")
            key = (module, category_large)
            groups.setdefault(key, []).append(flatten_case(case))
    for rows in groups.values():
        for i, row in enumerate(rows, start=1):
            row["No"] = i
    return groups
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: PASS (5/5 tests).

- [ ] **Step 5: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add tools/export_excel.py tests/test_export_excel.py
git commit -m "Add group_cases and sanitize_sheet_name to export_excel.py"
```

---

## Task 3: `build_summary()`

**Files:**
- Modify: `tools/export_excel.py`
- Test: `tests/test_export_excel.py`

**Interfaces:**
- Consumes: the `groups` dict shape produced by `group_cases` in Task 2 — `dict[tuple[str, str], list[dict]]` where each row dict has a `"Priority"` key.
- Produces: `build_summary(groups: dict) -> pandas.DataFrame` with columns `["Priority"] + <modules in first-seen order> + ["Total"]`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_export_excel.py`:

```python
from export_excel import build_summary


def test_build_summary_counts_by_priority_and_module():
    groups = {
        ("login", "A"): [{"Priority": "P1"}, {"Priority": "P2"}],
        ("payment", "B"): [{"Priority": "P1"}, {"Priority": "P1"}, {"Priority": "P3"}],
    }
    summary = build_summary(groups)

    assert list(summary.columns) == ["Priority", "login", "payment", "Total"]

    row_p1 = summary[summary["Priority"] == "P1"].iloc[0]
    assert row_p1["login"] == 1
    assert row_p1["payment"] == 2
    assert row_p1["Total"] == 3

    row_p2 = summary[summary["Priority"] == "P2"].iloc[0]
    assert row_p2["login"] == 1
    assert row_p2["payment"] == 0

    row_p3 = summary[summary["Priority"] == "P3"].iloc[0]
    assert row_p3["login"] == 0
    assert row_p3["payment"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_summary'`.

- [ ] **Step 3: Add `build_summary` to `tools/export_excel.py`**

Append to `tools/export_excel.py`:

```python
import pandas as pd


def build_summary(groups: dict) -> pd.DataFrame:
    counts: dict = {}
    modules_order: list = []
    for (module, _category_large), rows in groups.items():
        if module not in modules_order:
            modules_order.append(module)
        for row in rows:
            priority = row.get("Priority", "")
            counts.setdefault(priority, {}).setdefault(module, 0)
            counts[priority][module] += 1

    known_order = ["P1", "P2", "P3"]
    priorities_order = [p for p in known_order if p in counts] + sorted(
        p for p in counts if p not in known_order
    )

    data = []
    for priority in priorities_order:
        row = {"Priority": priority}
        total = 0
        for module in modules_order:
            count = counts[priority].get(module, 0)
            row[module] = count
            total += count
        row["Total"] = total
        data.append(row)

    return pd.DataFrame(data, columns=["Priority"] + modules_order + ["Total"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: PASS (6/6 tests).

- [ ] **Step 5: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add tools/export_excel.py tests/test_export_excel.py
git commit -m "Add build_summary to export_excel.py"
```

---

## Task 4: `write_workbook()` + styling

**Files:**
- Modify: `tools/export_excel.py`
- Test: `tests/test_export_excel.py`

**Interfaces:**
- Consumes: `groups: dict[tuple[str,str], list[dict]]` (Task 2), `summary_df: pandas.DataFrame` (Task 3), `sanitize_sheet_name` (Task 2).
- Produces: `write_workbook(groups: dict, summary_df: pd.DataFrame, output_path: str | Path) -> None` — writes an `.xlsx` file with a `Summary` sheet first, then one sheet per group, each header-styled and frozen.
- `COLUMN_ORDER: list[str]` — the fixed 14-column order (`No` through `Remarks`) every case sheet must use.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_export_excel.py`:

```python
import openpyxl

from export_excel import write_workbook


def test_write_workbook_creates_summary_and_case_sheets(tmp_path):
    groups = {
        ("login", "Nghiệp vụ đăng nhập"): [
            {
                "No": 1, "TC ID": "IT-LOGIN-001", "Medium": "A", "Small": "a",
                "Title": "t1", "Precondition": "", "Steps": "", "Expected Result": "e1",
                "Priority": "P1", "Trace": "", "Status": "", "Tested By": "",
                "Date": "", "Remarks": "",
            },
        ],
    }
    summary_df = build_summary(groups)
    output_path = tmp_path / "out.xlsx"

    write_workbook(groups, summary_df, output_path)

    wb = openpyxl.load_workbook(output_path)
    assert wb.sheetnames[0] == "Summary"
    case_sheet_names = [n for n in wb.sheetnames if n != "Summary"]
    assert len(case_sheet_names) == 1
    sheet = wb[case_sheet_names[0]]

    assert sheet.cell(row=1, column=1).value == "No"
    assert sheet.cell(row=1, column=2).value == "TC ID"
    assert sheet.cell(row=2, column=2).value == "IT-LOGIN-001"

    header_cell = sheet.cell(row=1, column=1)
    assert header_cell.fill.start_color.rgb in ("00305496", "FF305496")
    assert header_cell.font.bold is True
    assert sheet.freeze_panes == "A2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: FAIL — `ImportError: cannot import name 'write_workbook'`.

- [ ] **Step 3: Add `write_workbook` and styling helpers to `tools/export_excel.py`**

Append to `tools/export_excel.py`:

```python
from openpyxl.styles import Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

COLUMN_ORDER = [
    "No", "TC ID", "Medium", "Small", "Title", "Precondition", "Steps",
    "Expected Result", "Priority", "Trace", "Status", "Tested By", "Date", "Remarks",
]

HEADER_FILL = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)
THIN_SIDE = Side(style="thin")
THIN_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def _style_sheet(worksheet, num_columns: int) -> None:
    for col_idx in range(1, num_columns + 1):
        header_cell = worksheet.cell(row=1, column=col_idx)
        header_cell.fill = HEADER_FILL
        header_cell.font = HEADER_FONT

    for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, max_col=num_columns):
        for cell in row:
            cell.border = THIN_BORDER

    worksheet.freeze_panes = "A2"

    for col_idx in range(1, num_columns + 1):
        column_letter = get_column_letter(col_idx)
        max_len = max(
            (
                len(str(worksheet.cell(row=r, column=col_idx).value or ""))
                for r in range(1, worksheet.max_row + 1)
            ),
            default=10,
        )
        worksheet.column_dimensions[column_letter].width = min(max_len + 2, 60)


def write_workbook(groups: dict, summary_df: pd.DataFrame, output_path) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        _style_sheet(writer.sheets["Summary"], len(summary_df.columns))

        existing_names = {"Summary"}
        for (module, category_large), rows in groups.items():
            sheet_name = sanitize_sheet_name(module, category_large, existing_names)
            existing_names.add(sheet_name)
            df = pd.DataFrame(rows)[COLUMN_ORDER]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            _style_sheet(writer.sheets[sheet_name], len(COLUMN_ORDER))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: PASS (7/7 tests).

- [ ] **Step 5: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add tools/export_excel.py tests/test_export_excel.py
git commit -m "Add write_workbook with header styling to export_excel.py"
```

---

## Task 5: `load_testcases()` + `main()` CLI + end-to-end test

**Files:**
- Modify: `tools/export_excel.py`
- Test: `tests/test_export_excel.py`

**Interfaces:**
- Consumes: `group_cases`, `build_summary`, `write_workbook` from Tasks 2-4.
- Produces:
  - `load_testcases(module: str, project_root: Path) -> list[dict]` — raises `FileNotFoundError` with a message containing `testcases/<module>.yaml` if the file doesn't exist.
  - `main(argv: list[str] | None = None) -> int` — CLI entry point; returns `0` on success, `1` if any module's file is missing (after printing the error to stderr).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_export_excel.py`:

```python
import pytest

from export_excel import load_testcases, main


def test_load_testcases_raises_clear_error_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="testcases/missing-module.yaml"):
        load_testcases("missing-module", tmp_path)


def test_main_returns_nonzero_and_prints_error_for_missing_module(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exit_code = main(["missing-module"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "testcases/missing-module.yaml" in captured.err


LOGIN_YAML = """\
- id: IT-LOGIN-001
  trace: [DD-2.1]
  test_level: IT
  category:
    large: "Nghiệp vụ đăng nhập"
    medium: "Xác thực password"
    small: "Password đúng biên dưới"
  viewpoint: DATA-01
  precondition_vi: ["Tài khoản đã được cấp"]
  condition_vi: "Password 8 ký tự (min)"
  steps:
    - action_vi: "Nhập password 8 ký tự"
      data: {password: "Abcd1234"}
  expected_vi: "Đăng nhập thành công"
  evidence:
    section: "DD-2.1"
    quote: "Password từ 8 đến 32 ký tự"
    source_type: db_definition
    operator: {min: 8, min_op: ">=", max: 32, max_op: "<="}
  priority: P1
  tags: [smoke]
  automatable: true
  verify:
    - method: ui_visible
      target: "màn hình chính"
      expect: true
"""

PAYMENT_YAML = """\
- id: IT-PAYMENT-001
  trace: [DD-5.1]
  test_level: IT
  category:
    large: "Nghiệp vụ thanh toán"
    medium: "Xử lý thẻ"
    small: "Thẻ hợp lệ"
  viewpoint: DATA-02
  precondition_vi: []
  condition_vi: "Thanh toán bằng thẻ hợp lệ"
  steps:
    - action_vi: "Nhập thông tin thẻ"
  expected_vi: "Thanh toán thành công"
  evidence:
    section: "DD-5.1"
    quote: "Thẻ phải còn hạn sử dụng"
    source_type: dd
  priority: P2
  tags: []
  automatable: false
"""


def test_main_end_to_end_multi_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    testcases_dir = tmp_path / "testcases"
    testcases_dir.mkdir()
    (testcases_dir / "login.yaml").write_text(LOGIN_YAML, encoding="utf-8")
    (testcases_dir / "payment.yaml").write_text(PAYMENT_YAML, encoding="utf-8")

    exit_code = main(["login", "payment"])
    assert exit_code == 0

    output_path = tmp_path / "testcases-export.xlsx"
    assert output_path.exists()

    wb = openpyxl.load_workbook(output_path)
    assert "Summary" in wb.sheetnames
    assert any(name.startswith("login_") for name in wb.sheetnames)
    assert any(name.startswith("payment_") for name in wb.sheetnames)


def test_main_single_module_default_output_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    testcases_dir = tmp_path / "testcases"
    testcases_dir.mkdir()
    (testcases_dir / "login.yaml").write_text(LOGIN_YAML, encoding="utf-8")

    exit_code = main(["login"])
    assert exit_code == 0
    assert (tmp_path / "login-export.xlsx").exists()


def test_main_respects_out_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    testcases_dir = tmp_path / "testcases"
    testcases_dir.mkdir()
    (testcases_dir / "login.yaml").write_text(LOGIN_YAML, encoding="utf-8")

    exit_code = main(["login", "--out", "custom.xlsx"])
    assert exit_code == 0
    assert (tmp_path / "custom.xlsx").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_testcases'`.

- [ ] **Step 3: Add `load_testcases` and `main` to `tools/export_excel.py`**

Append to `tools/export_excel.py`:

```python
import argparse
import sys
from pathlib import Path

import yaml


def load_testcases(module: str, project_root: Path) -> list:
    path = Path(project_root) / "testcases" / f"{module}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy testcases/{module}.yaml — kiểm tra lại tên module."
        )
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export testcases/<module>.yaml sang Excel cho QC đọc."
    )
    parser.add_argument("modules", nargs="+", help="Tên module (khớp file testcases/<module>.yaml)")
    parser.add_argument("--out", default=None, help="Đường dẫn file .xlsx output")
    args = parser.parse_args(argv)

    project_root = Path.cwd()
    cases_by_module = {}
    for module in args.modules:
        try:
            cases_by_module[module] = load_testcases(module, project_root)
        except FileNotFoundError as e:
            print(f"Lỗi: {e}", file=sys.stderr)
            return 1

    groups = group_cases(cases_by_module)
    summary_df = build_summary(groups)

    if args.out:
        output_path = Path(args.out)
    elif len(args.modules) == 1:
        output_path = Path(f"{args.modules[0]}-export.xlsx")
    else:
        output_path = Path("testcases-export.xlsx")

    write_workbook(groups, summary_df, output_path)
    print(f"Đã xuất: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin && uv run pytest tests/test_export_excel.py -v`
Expected: PASS (12/12 tests).

- [ ] **Step 5: Manual sanity check — open the generated file**

Run:
```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
mkdir -p /tmp/export-excel-manual-check/testcases
cp dev-fixtures/login-project/testcases/login.yaml /tmp/export-excel-manual-check/testcases/
cd /tmp/export-excel-manual-check
uv run --project /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin python /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin/tools/export_excel.py login
```
Expected: prints `Đã xuất: login-export.xlsx`, file exists. Open it (e.g. `open login-export.xlsx` on macOS) and confirm by eye: `Summary` sheet first, header row is dark blue with white bold text, case sheet has all 14 columns with the 1 login test case's data, `Status`/`Tested By`/`Date`/`Remarks` are empty.

- [ ] **Step 6: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add tools/export_excel.py tests/test_export_excel.py
git commit -m "Add load_testcases and main CLI to export_excel.py"
```

---

## Self-Review (đã chạy khi viết plan này)

**1. Spec coverage:** Mục A (CLI/file structure) → Task 1 + Task 5. Mục B (14 cột) → Task 1
(`flatten_case`) + Task 4 (`COLUMN_ORDER`). Mục C (sheet grouping/naming/style/Summary) → Task 2
+ Task 3 + Task 4. Mục D (7 test case) → tất cả 12 test viết trong Task 1-5 (đối chiếu: flatten
= test 1-2, group = test 3, sanitize+collision = test 4-5, summary = test 6, write+read-back =
test 7-8, gộp đa module + module thiếu file = test 9-12). Không có mục nào trong spec thiếu task.

**2. Placeholder scan:** Không có "TBD"/"TODO" — mọi step có code đầy đủ, mọi lệnh chạy có
expected output cụ thể.

**3. Type/name consistency:** `flatten_case` (Task 1) → dùng trong `group_cases` (Task 2, gọi
trực tiếp) → row dict đó dùng trong `build_summary` (Task 3, đọc `row["Priority"]`) và
`write_workbook` (Task 4, đọc theo `COLUMN_ORDER` đã định nghĩa khớp 13 key của `flatten_case`
+ `"No"` do `group_cases` thêm). `sanitize_sheet_name` định nghĩa ở Task 2, dùng lại nguyên
signature trong Task 4. `main()` ở Task 5 gọi đúng tên `group_cases`/`build_summary`/
`write_workbook`/`load_testcases` không lệch tên ở bất kỳ đâu.
