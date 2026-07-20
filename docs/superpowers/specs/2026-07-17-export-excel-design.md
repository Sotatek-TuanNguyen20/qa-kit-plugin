# Design: `tools/export_excel.py`

Ngày: 2026-07-17

## Bối cảnh

`README.md`/`CLAUDE.md` của plugin đã tự đặt nguyên tắc "YAML là source of truth, Excel là
build artifact" từ đầu, nhưng `tools/export_excel.py` chưa từng được xây (⬜ trong status table).
QC không biết code không đọc được `testcases/$1.yaml` thô. Đây là **code Python đầu tiên** trong
plugin — mọi thứ trước giờ chỉ là `SKILL.md`/`commands/*.md` (prompt) và YAML.

Có sẵn mẫu định dạng thật team đang quen dùng: `test-case/` (255 case thật, export Google
Sheets) — nhiều sheet theo component kỹ thuật + 1 sheet Summary, cột `No | TC ID | Sub-Section |
Title | Precondition | Steps | Expected Result | Priority | Status | Tested By | Date | Remarks`,
header màu `#305496` chữ trắng đậm có border. Quyết định: chia sheet theo `category.large`
(business flow, đúng triết lý kit), không theo component (dev view) — dùng "Medium"/"Small" tách
riêng thay vì gộp "Sub-Section" vì schema có 3 tầng category, không phải 1.

## Phạm vi

- Chỉ export **testcases** (giai đoạn design), KHÔNG merge kết quả round nào. Cột
  Status/Tested By/Date/Remarks để trống, tester tự điền tay khi chạy — tương tự tinh thần
  `checklist.md` của nhánh MANUAL trong `commands/run.md`, chỉ khác định dạng.
- Hỗ trợ gộp nhiều module vào 1 workbook trong 1 lần chạy.
- KHÔNG tự dịch tiếng Nhật — Excel ra tiếng Việt, comtor dịch riêng ngoài repo (đã ghi trong
  bối cảnh gốc của cả dự án).
- KHÔNG validate schema (đó là việc của `tools/validate.py`, chưa xây, ngoài phạm vi design này).

## A. Cấu trúc file + CLI

```
qa-kit-plugin/
  pyproject.toml              # mới — uv quản lý, khai báo pandas/openpyxl/pytest
  tools/
    export_excel.py           # script chính, có main() + hàm import được để test
  tests/
    test_export_excel.py      # pytest
```

```bash
uv run python ${CLAUDE_PLUGIN_ROOT}/tools/export_excel.py login payment --out testcases-export.xlsx
```

Chạy từ trong repo dự án (vì `testcases/` nằm ở đó). Khớp cơ chế đã có sẵn trong
`templates/project-scaffold/.claude/settings.json` (đã allow `Bash(python3 tools/*)`) — không
cần thêm `/qa-kit:` command mới.

`--out` không truyền → mặc định `<module đầu tiên>-export.xlsx` (1 module) hoặc
`testcases-export.xlsx` (nhiều module).

Module không có file `testcases/<module>.yaml` → báo lỗi rõ ràng, dừng, không sinh file rỗng.

## B. Cột mỗi sheet (map từ `schemas/testcase.schema.yaml`)

| Cột Excel | Field nguồn | Ghi chú |
|---|---|---|
| No | (số thứ tự) | tự sinh, theo thứ tự trong file YAML |
| TC ID | `id` | |
| Medium | `category.medium` | |
| Small | `category.small` | |
| Title | `condition_vi` | |
| Precondition | `precondition_vi[]` | nối bằng xuống dòng trong cell |
| Steps | `steps[]` | đánh số `1. <action_vi>` (kèm `data` nếu có), nối xuống dòng |
| Expected Result | `expected_vi` | |
| Priority | `priority` | |
| Trace | `trace[]` | nối bằng `, ` |
| Status | (trống) | tester điền tay |
| Tested By | (trống) | tester điền tay |
| Date | (trống) | tester điền tay |
| Remarks | (trống) | tester điền tay |

## C. Tổ chức sheet

- 1 sheet = 1 cặp `(module, category.large)`. Case cùng module + cùng `category.large` vào
  chung 1 sheet dù khác `medium`/`small`.
- Tên sheet: `f"{module}_{sanitize(category.large)}"`, cắt còn tối đa 31 ký tự (giới hạn Excel),
  bỏ ký tự Excel cấm (`: \ / ? * [ ]`). Trùng tên sau khi cắt → thêm hậu tố số (`_2`, `_3`...).
- Style: header row tô `#305496`, chữ trắng đậm, có border mỏng toàn bảng, freeze header row,
  auto-width cột theo nội dung dài nhất (giới hạn max ~60 ký tự để khỏi tràn).
- 1 sheet **Summary** ở đầu workbook: tổng số case theo `priority` (P1/P2/P3) × `module`, dạng
  bảng — KHÔNG có cột Pass/Fail/Blocked (không có dữ liệu kết quả, khác mẫu cũ).

## D. Test — pytest thật

Giới thiệu `pytest` lần đầu vào plugin. Test tối thiểu cho từng hàm thuần (không phụ thuộc I/O
thật khi có thể — dùng fixture YAML nhỏ dựng trong test, không nhất thiết phải đọc
`dev-fixtures/login-project/` thật, vì đó chỉ có 1 case, không đủ để test nhóm-theo-category
hay gộp-đa-module):

1. Flatten 1 test case YAML → 1 row dict đúng cột (test riêng từng field, đặc biệt `steps[]`
   nhiều bước và `precondition_vi[]` nhiều dòng).
2. Group nhiều case theo `(module, category.large)` ra đúng số sheet.
3. Sanitize tên sheet: cắt đúng 31 ký tự, bỏ ký tự cấm, xử lý trùng tên sau khi cắt.
4. Gộp nhiều module trong 1 lần chạy ra đúng số sheet tổng.
5. Module không có file `testcases/<module>.yaml` → raise lỗi rõ ràng, không crash mù mờ.
6. Summary sheet tính đúng tổng theo priority × module.
7. End-to-end: chạy `main()` trên fixture nhỏ dựng trong test, mở lại `.xlsx` bằng `openpyxl`,
   assert đúng số sheet/đúng ô dữ liệu (không assert style — style khó test giòn, chỉ verify
   bằng mắt 1 lần khi implement xong).

`pyproject.toml` khai báo `pandas`, `openpyxl`, `pytest` làm dependencies — `uv sync` trước khi
chạy test.

## Ngoài phạm vi (out of scope)

- `tools/validate.py`, `tools/harness.py` — 2 tool còn lại trong status table, không đụng ở đây.
- Merge kết quả round vào Excel — quyết định rõ ràng: không làm, giữ tách biệt design vs execution.
- Style pixel-perfect giống hệt mẫu cũ (màu chính xác, font family) — bám tinh thần (màu xanh
  đậm, chữ trắng đậm, có border), không cần khớp từng giá trị hex/font.
- Tự dịch tiếng Nhật.
