"""Export testcases/<module>.yaml files into a styled Excel workbook for QC."""

from __future__ import annotations

import re

import pandas as pd

FORBIDDEN_SHEET_CHARS = re.compile(r"[:\\/?*\[\]]")
MAX_SHEET_NAME_LEN = 31


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
