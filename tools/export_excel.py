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
