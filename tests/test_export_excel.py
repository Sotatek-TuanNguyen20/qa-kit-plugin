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
