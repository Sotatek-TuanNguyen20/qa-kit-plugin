# Design: System Profile (tổng quát hoá hệ thống không phải web+DB) + `/qa-kit:ready`

Ngày: 2026-07-21

> Thay thế `docs/superpowers/specs/2026-07-17-non-web-system-support-design.md` (spec cũ
> vẫn giữ nguyên làm record lịch sử, đã ghi chú "superseded" ở đầu file đó). Nội dung
> System Profile/enum/routing của spec cũ **giữ nguyên tinh thần, không đổi cách tiếp
> cận** — spec này chỉ viết lại đầy đủ hơn, bổ sung 2 câu hỏi mới (Phần 1) và 1 command
> mới (Phần 4) mà spec cũ chưa có.

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

Đào sâu thêm vào project thật (255 test case Google Sheets thật của ROC-PD-Gateway) lộ ra
2 vấn đề khác spec cũ (2026-07-17) chưa xử lý:

1. **Seed/test data không phải lúc nào cũng là DB row.** Với ROC-PD-Gateway, "seed data"
   là 8 file `.eml` mẫu mô phỏng alert từ nhiều tool giám sát (Nagios, PatrolClarice,
   NetSNMP, eAries, eGemini, MultiReceiver — mỗi tool 1 format/encoding khác nhau, xem
   `Sample Data.html`). Câu hỏi "ai cấp/tạo seed data khi cần case mới" chưa có chỗ trả
   lời trong kit.
2. **"Cô lập môi trường" không phải lúc nào cũng là DB isolation.** ROC-PD-Gateway chỉ có
   **1 server DEV EC2 dùng chung cho cả team** (xem `Test Environment.html`) — không có
   khái niệm "mỗi tester 1 schema riêng". Câu hỏi thật là "nhiều tester chạy cùng lúc trên
   cùng 1 spool directory có đụng nhau không, và team đang xử lý việc đó thế nào (nếu có)".

Quyết định (đã có từ spec cũ, giữ nguyên): sửa ở **plugin dùng chung**, không phải chỉ
riêng dự án ROC — vì đây là công ty outsourcing làm nhiều dự án, pattern này sẽ gặp lại.

Đây là thay đổi vào **schema dùng chung** — theo `README.md` tự đặt policy "Đổi schema ->
major (breaking, mọi dự án phải migrate)".

## Phần 1: `/qa-kit:init` tương tác + System Profile (5 câu hỏi)

### 5 câu hỏi lúc scaffold (ngoài tên dự án `$1`)

1. **Hệ thống test là gì?** — lựa chọn: `web` / `mobile app` / `cli-daemon` / `api-only` / `khác`
2. **Hệ thống có database không?** — có/không
3. **Hệ thống có config file riêng làm nguồn tham số không?** (chỉ hỏi nếu câu 2 = không) — có/không
4. **(Mới) Ai cung cấp seed/test data cho dự án này?** — lựa chọn:
   - `dev/BrSE cấp mẫu thật` (vd: file `.eml` mẫu, tài khoản test thật do dev tạo)
   - `QC tự tạo theo schema/format đã tài liệu hoá` (vd: DDL rõ ràng, format spec rõ ràng —
     QC tự sinh giá trị hợp lệ mà không cần hỏi lại)
   - `chưa xác định` — chưa ai quyết, ghi nhận là rủi ro tường minh, không phải lỗi chặn init
5. **(Mới) Môi trường test này được dùng như thế nào?** — lựa chọn:
   - `Riêng — không ai khác dùng chung`
   - `Dùng chung, có cơ chế cô lập` — hỏi thêm 1 dòng mô tả cơ chế (tự do, vd "mỗi tester
     1 schema DB riêng", "container riêng theo branch"...)
   - `Dùng chung, không có cơ chế cô lập`

### Lưu vào `CLAUDE.md` — mục mới "System Profile"

```markdown
## System Profile
- Loại hệ thống: <câu trả lời 1>
- Database: <có/không>
- Nguồn boundary ưu tiên #1: <db_definition | config_definition | (không có, chỉ còn văn xuôi)>
- Bộ verify.method gợi ý: <danh sách method phù hợp theo câu trả lời 1>
- Nguồn seed/test data: <câu trả lời 4>
- Môi trường: <riêng | dùng chung + mô tả cơ chế cô lập | dùng chung KHÔNG cô lập ⚠️>
```

Bảng suy ra bộ verify.method gợi ý theo loại hệ thống (giữ nguyên spec cũ):

| Loại hệ thống | verify.method gợi ý |
|---|---|
| `web` | `ui_text`, `ui_visible`, `http_status`, `http_body`, `db_query` (nếu có DB) |
| `api-only` | `http_status`, `http_body`, `db_query` (nếu có DB) |
| `cli-daemon` | `cli_exit_code`, `cli_output`, `file_exists`, `file_content`, `log_grep` |
| `mobile app` | `ui_text`, `ui_visible` (chưa có method mobile-specific — dùng tạm bộ web, ghi rõ là tạm) |
| `khác` | Không gợi ý sẵn — tester tự chọn từ toàn bộ enum, ghi lý do |

### `config/env.yaml` scaffold theo loại hệ thống (giữ nguyên spec cũ)

- `web`/`api-only`: `base_url` (+ `db.host` nếu có DB, giữ nguyên field cũ)
- `cli-daemon`: `ssh_host`, `spool_root`, `pagerduty_mock_url` (hoặc mock endpoint tương ứng
  external service của dự án đó — tên field này do tester đặt lại cho khớp domain), `systemd_services`
- `mobile app`/`khác`: giữ template rỗng nhất, ghi chú tester tự điền field phù hợp

### Nguyên tắc quan trọng cho 2 câu hỏi mới (4, 5)

Câu 4 = "chưa xác định" hoặc câu 5 = "dùng chung KHÔNG cô lập" **không phải lỗi chặn**
`/qa-kit:init` — project vẫn scaffold bình thường. Đây là **thông tin rủi ro được ghi nhận
tường minh** ngay từ đầu, để `/qa-kit:ready` (Phần 4) đọc lại và cảnh báo mỗi lần chạy —
đúng tinh thần "không tự giả định an toàn, không im lặng" đã xuyên suốt cả kit (evidence
immutable, `blocked` ≠ `fail`, default `A_bug` khi không chắc...).

## Phần 2: Mở rộng 2 enum trong `schemas/testcase.schema.yaml` (giữ nguyên spec cũ)

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

**Lưu ý liên quan tới plan `design-chain-skills` vừa xong:** `detail-fill/SKILL.md` (không
phải `testcase-generate` nữa) mới là skill thực sự áp dụng bảng ưu tiên nguồn evidence khi
tìm evidence — bảng 5 tầng ở trên khi implement phải sửa ở `detail-fill/SKILL.md`, không
phải `testcase-generate/SKILL.md` như spec cũ (2026-07-17) viết, vì thứ tự đọc evidence đã
chuyển hết sang `detail-fill` từ sau plan đó. `testcase-generate` giờ chỉ lắp ráp case từ
evidence đã có sẵn trong `details.yaml`, không tự áp bảng ưu tiên nào cả.

## Phần 3: `commands/run.md` — nhánh AUTO route theo họ `verify.method` (giữ nguyên spec cũ)

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

## Phần 4 (mới): `/qa-kit:ready` — kiểm tra sẵn sàng trước khi `/qa-kit:run`

### Vì sao command này tồn tại

ISTQB phase 5 "Test implementation" (テスト実装) map vào 2 việc: chuẩn bị môi trường +
chuẩn bị test data. `testcase-generate` đã điền `steps[].data` cụ thể cho từng case, và
thiếu evidence cho data đã được `detail-fill` bắt thành gap **ngay lúc design** — nhưng còn
1 việc chưa ai làm: **trước khi thực sự chạy `/qa-kit:run`, resource vật lý (file mẫu,
service mock, server) cần cho module này đã có sẵn tại chỗ chưa, và môi trường có rủi ro
đụng tester khác không.**

Đây KHÔNG phải là 1 command tự động hoá hạ tầng — `/qa-kit:ready` không tự SSH, không tự
tạo file, không tự kiểm tra trạng thái server thật. QC không tự động hoá infra (ranh giới
đã có sẵn của cả kit). Đây là **1 checklist tĩnh** giúp tester tự soát trước khi chạy thật.

### Input/Output

- Input: `$1` = tên module.
- Đọc: `CLAUDE.md` (mục System Profile), `testcases/$1.yaml`.
- Output: `reports/$1-ready.md`.

### Quy trình

1. Đọc `CLAUDE.md`'s System Profile — lấy 2 dòng "Nguồn seed/test data" và "Môi trường".
2. Đọc `testcases/$1.yaml`, với mỗi case trích:
   - `steps[].data` (giá trị cụ thể cần nhập/dùng) — nguồn chính, có cấu trúc key-value rõ
     ràng. Với case CLI/daemon, giá trị resource-cần-chuẩn-bị (tên file mẫu, service cần
     chạy trước...) cũng nằm ở đây dưới dạng key-value (vd `data: { mail_file:
     "samples/nagios-trigger.eml" }`), không phải chỗ nào khác.
   - `precondition_vi`/`steps[].action_vi` — nguồn phụ, chỉ đọc để lấy thêm ngữ cảnh hiển
     thị trong report (vd tên service/thư mục nhắc tới trong câu mô tả hành động), KHÔNG
     dùng để tự suy luận resource nào cần chuẩn bị nếu `steps[].data` không có — tránh
     đoán mò từ văn xuôi tự do.
3. Gom tất cả case thành 1 danh sách "resource cần chuẩn bị" cho cả module — dedupe (nhiều
   case cùng cần 1 resource thì chỉ liệt kê 1 lần, kèm số lượng case phụ thuộc).
4. Đối chiếu danh sách với "Nguồn seed/test data" trong System Profile:
   - = "chưa xác định" → **toàn bộ danh sách** đánh dấu "⚠️ CHƯA THỂ XÁC NHẬN — chưa rõ ai
     cấp data cho dự án này".
   - Đã xác định (dev/BrSE cấp hoặc QC tự tạo theo schema) → liệt kê từng resource dưới
     dạng checklist tay (`- [ ] <tên resource> (cần cho N case: <id case>)`), tester tự
     tick sau khi xác nhận có sẵn.
5. Đối chiếu "Môi trường" trong System Profile:
   - "dùng chung, KHÔNG có cơ chế cô lập" → **luôn in cảnh báo rủi ro ở đầu report**, bất
     kể module nào, nhắc tester phối hợp lịch chạy với người khác đang dùng chung server/
     resource.
   - "dùng chung, có cơ chế cô lập" → in 1 dòng nhắc lại cơ chế đã khai báo (để tester nhớ
     áp dụng đúng, vd "nhớ tạo schema riêng theo branch trước khi chạy").
   - "riêng" → không in gì thêm.
6. Ghi `reports/$1-ready.md`.

### Gate (mềm, không tự chặn lệnh khác)

Nếu có resource "⚠️ CHƯA THỂ XÁC NHẬN" → dòng đầu report in "❌ CHƯA SẴN SÀNG — cần xác
nhận nguồn data trước khi `/qa-kit:run`". Đây là gợi ý cho tester tự đọc và tự quyết định
có chạy tiếp hay không — **không phải machine gate tự động chặn** như `/qa-kit:design`
(vì `/qa-kit:run` là command riêng biệt, `/qa-kit:ready` không có cơ chế nào tự chèn vào
giữa để chặn nó).

### `reports/$1-ready.md`

```markdown
# Ready Check — <module>

| Module | <module> |
|---|---|
| Generated at | <ISO 8601> |
| Generated by | |
| Trạng thái | ❌ CHƯA SẴN SÀNG — cần xác nhận nguồn data trước khi /qa-kit:run |

## ⚠️ Rủi ro môi trường
Môi trường dùng chung, KHÔNG có cơ chế cô lập (xem CLAUDE.md System Profile) — phối hợp
lịch chạy với các tester khác đang dùng chung server/resource trước khi chạy.

## Resource cần chuẩn bị
- [ ] samples/nagios-trigger.eml (cần cho 3 case: SEND-001, SEND-003, SEND-007)
- [ ] samples/nagios-resolve.eml (cần cho 1 case: SEND-002)
⚠️ CHƯA THỂ XÁC NHẬN — chưa rõ ai cấp data cho dự án này (System Profile: "chưa xác định")
```

`Generated by` luôn để trống — con người tự điền tay lúc review, đúng convention đã có
của `gap-report`/`coverage-check`.

### Không thuộc phạm vi (`/qa-kit:data` bị bỏ, không xây riêng)

Ban đầu có ý định xây `/qa-kit:data` như 1 command riêng (ISTQB phase 5 đôi khi tách môi
trường và data thành 2 việc). Quyết định cuối: **gộp vào `/qa-kit:ready`** — vì (1) giá trị
data cụ thể từng case đã có sẵn trong `testcases/*.yaml` từ `testcase-generate`, (2) thiếu
evidence cho data đã được `detail-fill` bắt thành gap từ lúc design, (3) phần còn lại
("resource vật lý đã sẵn sàng chưa") là 1 checklist đơn giản, không đủ phức tạp để tách
thành 1 command/skill riêng — tránh 2 command chồng chéo nhau cho cùng 1 concept "sẵn
sàng". `/qa-kit:complete` (ISTQB phase 7) vẫn giữ nguyên, ngoài phạm vi spec này.

## Ảnh hưởng lên `ROC-QC` (dự án đã scaffold trước khi có thiết kế này)

`ROC-QC/CLAUDE.md` hiện có mục tạm "Adaptation cho hệ thống CLI/daemon" (viết tay, trước khi
thiết kế này tồn tại) và `ROC-QC/config/env.yaml` đã sửa tay theo đúng tinh thần thiết kế này
(ssh_host/spool_root/pagerduty_mock_url) — trùng khớp ngẫu nhiên với Phần 1. Sau khi plugin có
cơ chế System Profile chính thức, cần thay mục "Adaptation..." viết tay bằng mục "System Profile"
đúng format chuẩn (nội dung gần như giữ nguyên, chỉ đổi format/heading cho khớp cơ chế mới, thêm
2 dòng mới về seed data/môi trường dựa trên thực tế đã biết: nguồn = "dev/BrSE cấp mẫu thật"
(8 file `.eml` trong `Sample Data.html`), môi trường = "dùng chung, KHÔNG có cơ chế cô lập"
(1 server EC2 DEV chung cho cả team, theo `Test Environment.html`)) — việc này nằm trong phạm
vi implementation plan, không phải việc riêng.

## Ngoài phạm vi (out of scope) design này

- Method verify chuyên biệt cho mobile app (chưa có ví dụ thực tế nào yêu cầu, để "khác" tạm
  dùng bộ web, ghi rõ là tạm).
- Tool sinh script tự động cho `e2e/$1.sh` (bash) — bản thân cơ chế sinh script vẫn do
  `commands/run.md` mô tả bằng lời cho Claude tự viết lúc chạy, không phải 1 code generator
  riêng — giữ đúng triết lý "không thêm tool Python" đã áp dụng cho gap-report/coverage-check.
- Không đổi gì ở `qa-eval`/`qa-report`/`qa-retest` — các command này không quan tâm hệ thống
  là gì, chỉ đọc `results/*.yaml` đã có sẵn.
- `/qa-kit:ready` không tự động hoá việc SSH/kiểm tra file thật trên server — chỉ là checklist
  tĩnh, tester tự tick tay. Tự động hoá việc này (nếu cần sau này) là 1 thiết kế riêng.
- `/qa-kit:data` như 1 command riêng — quyết định không xây (xem lý do ở Phần 4).

## Kiểm chứng khi implement

Giống cách đã làm với gap-report/coverage-check và design-chain-skills: dựng fixture cho 2
loại hệ thống (1 web đã có sẵn tinh thần qua `dev-fixtures/login-project/`, cần thêm 1
fixture CLI-daemon mới, có thể dựa 1 phần trên format thật thấy được từ `ROC-Test/test-case/`
— vd sample `.eml`, cấu trúc spool dir) để tự verify:
- `commands/init.md` hỏi đúng 5 câu, sinh đúng `CLAUDE.md` System Profile + `config/env.yaml`
  theo loại hệ thống.
- `commands/run.md` route đúng nhánh AUTO theo họ `verify.method`.
- `/qa-kit:ready` đọc đúng System Profile + `testcases/*.yaml`, sinh đúng checklist + cảnh
  báo rủi ro môi trường + gate "CHƯA SẴN SÀNG" khi nguồn data chưa xác định.
