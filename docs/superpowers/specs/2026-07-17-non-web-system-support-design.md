# Design: hỗ trợ hệ thống CLI/daemon (không chỉ web app + DB)

Ngày: 2026-07-17

## Bối cảnh

`qa-kit-plugin` hiện ngầm định hệ thống dưới test luôn là web app + database ở nhiều chỗ:
`schemas/testcase.schema.yaml` (`verify.method`, `evidence.source_type`), `commands/run.md`
(nhánh AUTO luôn sinh Playwright), `skills/testcase-generate/SKILL.md` (bảng ưu tiên nguồn
evidence: DDL/screen item/message list), `templates/project-scaffold/config/env.yaml`
(`base_url`/`db.host`), `commands/init.md` (dòng cứng "db/ -> xin dev DDL + ERD").

Phát hiện qua dự án thật **ROC-PD-Gateway**: 7 binary Go trên RHEL (daemon + CLI), **không
dùng database** (hàng đợi bằng file), **không có UI web**. Test case thật cho dự án này verify
bằng SSH + đọc file JSON trong thư mục spool + `journalctl`/log grep — không cái nào khớp
`ui_*`/`http_*`/`db_query`.

Ban đầu thử "adapt riêng cho dự án ROC-QC" (thêm mục trong `CLAUDE.md` của riêng dự án đó,
sửa `config/env.yaml` riêng) — nhưng quyết định cuối: **sửa ở plugin dùng chung**, vì đây là
pattern sẽ gặp lại ở dự án khác (team QC làm nhiều dự án outsourcing khác nhau), không phải
đặc thù chỉ 1 dự án.

Đây là thay đổi vào **schema dùng chung** — theo `README.md` tự đặt policy "Đổi schema ->
major (breaking, mọi dự án phải migrate)".

## Phần 1: `/qa-kit:init` tương tác + System Profile

### 3 câu hỏi lúc scaffold (ngoài tên dự án `$1`)

1. **Hệ thống test là gì?** — lựa chọn: `web` / `mobile app` / `cli-daemon` / `api-only` / `khác`
2. **Hệ thống có database không?** — có/không
3. **Hệ thống có config file riêng làm nguồn tham số không?** (chỉ hỏi nếu câu 2 = không) — có/không

### Lưu vào `CLAUDE.md` — mục mới "System Profile"

```markdown
## System Profile
- Loại hệ thống: <câu trả lời 1>
- Database: <có/không>
- Nguồn boundary ưu tiên #1: <db_definition | config_definition | (không có, chỉ còn văn xuôi)>
- Bộ verify.method gợi ý: <danh sách method phù hợp theo câu trả lời>
```

Bảng suy ra bộ verify.method gợi ý theo loại hệ thống:

| Loại hệ thống | verify.method gợi ý |
|---|---|
| `web` | `ui_text`, `ui_visible`, `http_status`, `http_body`, `db_query` (nếu có DB) |
| `api-only` | `http_status`, `http_body`, `db_query` (nếu có DB) |
| `cli-daemon` | `cli_exit_code`, `cli_output`, `file_exists`, `file_content`, `log_grep` |
| `mobile app` | `ui_text`, `ui_visible` (chưa có method mobile-specific — dùng tạm bộ web, ghi rõ là tạm) |
| `khác` | Không gợi ý sẵn — tester tự chọn từ toàn bộ enum, ghi lý do |

### `config/env.yaml` scaffold theo loại hệ thống

- `web`/`api-only`: `base_url` (+ `db.host` nếu có DB, giữ nguyên field cũ)
- `cli-daemon`: `ssh_host`, `spool_root`, `pagerduty_mock_url` (hoặc mock endpoint tương ứng
  external service của dự án đó — tên field này do tester đặt lại cho khớp domain), `systemd_services`
- `mobile app`/`khác`: giữ template rỗng nhất, ghi chú tester tự điền field phù hợp

## Phần 2: Mở rộng 2 enum trong `schemas/testcase.schema.yaml`

### `evidence.source_type` — tổ chức lại thành 5 tầng tin cậy, mỗi tầng 2 lựa chọn tương đương

| Tầng | Web app | CLI/backend (mới thêm) |
|---|---|---|
| 1 — cao nhất | `db_definition` (DDL) | `config_definition` (config file sản phẩm) |
| 2 | `screen_item` (màn hình) | `fixed_format` (định dạng file/protocol cố định) |
| 3 | `message_list` (catalog lỗi) | `log_format` (định dạng log/mail alert) |
| 4 | `dd` (văn xuôi DD) | dùng chung |
| 5 — thấp nhất | `spec` (văn xuôi spec) | dùng chung |

Giá trị enum mới: thêm `config_definition`, `fixed_format`, `log_format` vào
`evidence.source_type` (giữ nguyên `spec, dd, db_definition, message_list, screen_item`).

Một dự án chỉ dùng 1 cột — dự án không DB sẽ không bao giờ có case nào ghi
`source_type: db_definition`.

### `verify.method` — thêm 5 giá trị

Thêm: `cli_exit_code`, `cli_output` (stdout/stderr), `file_exists`, `file_content`, `log_grep`.
Giữ nguyên `ui_text, ui_visible, http_status, http_body, db_query`.

### Cập nhật kèm theo: `skills/testcase-generate/SKILL.md`

Bảng ưu tiên nguồn evidence hiện tại ("db_definition > screen_item > message_list > dd > spec")
phải viết lại theo cấu trúc 5 tầng ở trên — mỗi tầng ghi rõ 2 lựa chọn tương đương, không phải
1 chuỗi thứ tự cố định duy nhất. Tham chiếu `CLAUDE.md`'s System Profile để biết cột nào áp dụng
cho dự án đang làm.

## Phần 3: `commands/run.md` — nhánh AUTO route theo họ `verify.method`

```
## Nhánh AUTO (`automatable: true`)

Xem verify[] dùng họ method nào:

- Toàn bộ `ui_*`/`http_*`/`db_query` (web/API)
  -> sinh `e2e/$1.spec.ts`, chạy `npx playwright test e2e/$1.spec.ts` (như cũ)

- Toàn bộ `cli_*`/`file_*`/`log_*` (CLI-daemon)
  -> sinh `e2e/$1.sh` (bash), dùng `ssh_host`/`spool_root` từ `config/env.yaml`,
     SSH vào server test chạy lệnh CLI + check exit code/file/log,
     script tự exit 0 (pass) / 1 (fail)
  -> chạy `bash e2e/$1.sh`

- Case trộn cả 2 họ trong cùng 1 verify[]
  -> KHÔNG tự động hoá — chuyển nhánh MANUAL, ghi lý do "verify method trộn họ,
     chưa có cách auto-route an toàn"

Case thiếu `verify[]` -> vẫn như cũ, chuyển nhánh manual.
```

## Ảnh hưởng lên `ROC-QC` (dự án đã scaffold trước khi có thiết kế này)

`ROC-QC/CLAUDE.md` hiện có mục tạm "Adaptation cho hệ thống CLI/daemon" (viết tay, trước khi
thiết kế này tồn tại) và `ROC-QC/config/env.yaml` đã sửa tay theo đúng tinh thần thiết kế này
(ssh_host/spool_root/pagerduty_mock_url) — trùng khớp ngẫu nhiên với Phần 1. Sau khi plugin có
cơ chế System Profile chính thức, cần thay mục "Adaptation..." viết tay bằng mục "System Profile"
đúng format chuẩn (nội dung gần như giữ nguyên, chỉ đổi format/heading cho khớp cơ chế mới) —
việc này nằm trong phạm vi implementation plan, không phải việc riêng.

## Ngoài phạm vi (out of scope) design này

- Method verify chuyên biệt cho mobile app (chưa có ví dụ thực tế nào yêu cầu, để "khá" tạm
  dùng bộ web, ghi rõ là tạm).
- Tool sinh script tự động cho `e2e/$1.sh` (bash) — bản thân cơ chế sinh script vẫn do
  `commands/run.md` mô tả bằng lời cho Claude tự viết lúc chạy, không phải 1 code generator
  riêng — giữ đúng triết lý "không thêm tool Python" đã áp dụng cho gap-report/coverage-check.
- Không đổi gì ở `qa-eval`/`qa-report`/`qa-retest` — các command này không quan tâm hệ thống
  là gì, chỉ đọc `results/*.yaml` đã có sẵn.

## Kiểm chứng khi implement

Giống cách đã làm với gap-report/coverage-check: dựng fixture cho 2 loại hệ thống (1 web đã có
sẵn tinh thần qua `dev-fixtures/login-project/`, cần thêm 1 fixture CLI-daemon mới) để tự verify
`commands/init.md` hỏi đúng câu, sinh đúng `CLAUDE.md`/`config/env.yaml`, và `commands/run.md`
route đúng nhánh AUTO theo họ verify.method.
