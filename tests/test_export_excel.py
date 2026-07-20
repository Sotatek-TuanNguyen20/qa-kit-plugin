import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from export_excel import flatten_case, group_cases, sanitize_sheet_name


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
