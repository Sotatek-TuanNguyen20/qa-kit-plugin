---
description: Chạy test case của module. Automatable -> script. Còn lại -> checklist tay.
argument-hint: <module> [--only-auto|--only-manual]
allowed-tools: Read, Write, Bash
---

# /qa-kit:run $1 --build=<version> [--round=<N>] [--scope=<file>]

Đọc `testcases/$1.yaml`, chạy, ghi `results/$1-r<N>.yaml`.

## `--build` BẮT BUỘC

Không có build_version -> **DỪNG**. Kết quả không gắn build là kết quả vô nghĩa:
không trả lời được "case này pass ở build nào?", không vẽ được bug convergence,
không đối chiếu được khi khách hỏi.

## Round >= 2 phải có `--scope`

Chạy từ `work/$1/retest-scope-r<N>.md` do `/qa-kit:retest` sinh + human duyệt.
Không có scope -> DỪNG. Cấm tự quyết định round 2 chạy gì.

## Tiền điều kiện — không đủ thì DỪNG

- `testcases/$1.yaml` đã qua human review (có commit, không phải working dir bẩn)
- Env target là **test env**. Đọc `config/env.yaml`.
  Quét TẤT CẢ giá trị chuỗi trong `environments.<target>` (không chỉ `base_url`/`db.host`
  — hệ CLI/daemon dùng field khác như `ssh_host`/`spool_root`/`external_mock_url`, xem
  mục System Profile trong `CLAUDE.md` để biết field nào dự án này dùng) đối chiếu
  `forbidden_patterns`. Khớp bất kỳ pattern nào -> **DỪNG NGAY**, không hỏi lại.
- `environments.<target>` không có giá trị chuỗi nào để quét (block rỗng hoặc chỉ còn
  comment mẫu — như biến thể mobile app/`khác` do `/qa-kit:init` sinh ra) -> KHÔNG được
  coi là an toàn. Guard không có gì để quét nghĩa là chưa ai xác nhận đây không phải
  prod, chứ không phải đã xác nhận là test -> **DỪNG NGAY**, không hỏi lại. Lý do khác
  với case khớp forbidden pattern: đây không phải lỗi chính tả cần sửa pattern, mà là
  `config/env.yaml` chưa được điền field thật — báo tester điền field host/url thật của
  test env vào `environments.<target>` trong `config/env.yaml` rồi chạy lại.

## Nhánh AUTO (`automatable: true`)

Xem `verify[]` của case dùng họ `method` nào:

- **Toàn bộ `ui_*`/`http_*`/`db_query`** (web/API):
  1. Sinh script từ `steps[]` + `verify[]` -> `e2e/$1.spec.ts`
  2. Chạy: `npx playwright test e2e/$1.spec.ts`
  3. Ghi kết quả -> `results/$1-r<N>.yaml`

- **Toàn bộ `cli_exit_code`/`cli_output`/`file_exists`/`file_content`/`log_grep`**
  (CLI-daemon):
  1. Sinh script từ `steps[]` + `verify[]` -> `e2e/$1.sh` (bash)
  2. Dùng field tương ứng trong `config/env.yaml` (`ssh_host`, `spool_root`, hoặc field
     khác đã khai báo ở đó) để SSH vào server test, chạy lệnh CLI, kiểm tra exit
     code/file/log đúng theo từng `verify[]` entry
  3. Script tự `exit 0` (pass toàn bộ) / `exit 1` (có ít nhất 1 verify fail)
  4. Chạy: `bash e2e/$1.sh`
  5. Ghi kết quả -> `results/$1-r<N>.yaml`

- **Case trộn cả 2 họ trong cùng 1 `verify[]`** (vd 1 entry `ui_visible` + 1 entry
  `cli_exit_code` trong cùng 1 case): KHÔNG tự động hoá — chuyển nhánh MANUAL, ghi lý do
  "verify method trộn họ, chưa có cách tự động định tuyến an toàn".

Case thiếu `verify[]` -> KHÔNG tự chế cách verify. Chuyển sang nhánh manual, ghi lý do.

## Nhánh MANUAL

Sinh `results/$1-r<N>-checklist.md`: mỗi case 1 dòng, có precondition, steps,
expected, ô trống cho actual + pass/fail + note.
Tester tick tay, commit lại.

## Kết quả -> results/$1-r<N>.yaml

Theo `${CLAUDE_PLUGIN_ROOT}/schemas/result.schema.yaml`. Bắt buộc: `round`, `build_version`, `scope_reason`.

Với round >= 2, mỗi case phải có `prev_status` (lấy từ round trước).
`prev_status: pass` + `status: fail` = **regression**, /qa-kit:report sẽ đẩy lên đầu.

## status — 5 giá trị, đừng gộp

| | Nghĩa |
|---|---|
| `pass` | Đã test, đúng |
| `fail` | Đã test, sai |
| `blocked` | **Chưa test được** — bug khác chặn. Phải có `blocked_by`. |
| `skipped` | Cố ý bỏ. Phải có `skip_reason`. |
| `not_run` | Chưa tới lượt |

Gộp `blocked` vào `fail` -> thổi phồng số bug.
Gộp `blocked` vào `skipped` -> giấu rủi ro.

## Cấm

- Chạy khi env không phải test
- Ghi DB. `verify.db_query` chỉ SELECT.
- Sửa `testcases/$1.yaml` ở bước này. Run là read-only với test case.
- Tự chạy /qa-kit:eval sau khi xong.
