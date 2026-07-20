# Design: `scenario-map` + `viewpoint-apply` + `detail-fill`

Ngày: 2026-07-20

## Bối cảnh

`commands/design.md` mô tả sẵn chain 6 bước cho `/qa-kit:design`, nhưng 3 bước đầu
(`scenario-map`, `viewpoint-apply`, `detail-fill`) chưa tồn tại — lệnh fail ngay bước 1.
3 bước cuối (`testcase-generate`, `gap-report`, `coverage-check`) đã xây và đã verify
qua fixture `dev-fixtures/login-project/`.

Đây là mảnh backlog lớn nhất còn lại. Hoàn thành sẽ làm `/qa-kit:design` chạy được
đầu-cuối lần đầu tiên trong đời plugin.

## Phát hiện quan trọng khi brainstorm: overlap evidence-finding

`commands/design.md` (viết từ đầu session, trước khi có skill nào) đã mô tả `detail-fill`
là bước "boundary/data, **PHẢI bám doc**", và machine gate ">20% condition không tìm được
evidence" được đặt **ngay sau bước 3** (detail-fill), không phải sau bước 4. Tín hiệu này
cho thấy `detail-fill` mới là nơi tìm evidence thật sự.

Nhưng `skills/testcase-generate/SKILL.md` (đã build, đã test, đang chạy) hiện tự làm đúng
việc đó trong chính nó (đọc test condition → tìm căn cứ trong `docs/` → trích
`evidence.quote`). Nếu để nguyên cả 2, hai skill sẽ độc lập tự đi tìm evidence trong
cùng 1 tài liệu — tốn công gấp đôi, rủi ro 2 skill trích 2 quote khác nhau cho cùng 1
điều kiện.

**Quyết định:** `detail-fill` tìm evidence đầy đủ (mọi tầng: db_definition/screen_item/
message_list/dd/spec). `testcase-generate` **sửa lại** thành bộ lắp ráp — đọc evidence
đã có sẵn từ `details.yaml`, không tự tìm kiếm trong `docs/` nữa. Đây là thay đổi vào
skill đã shipped, cần cẩn thận không phá vỡ hành vi đã test (evidence immutable, cấm
suy diễn ngoài evidence — 2 luật này giữ nguyên, chỉ đổi NGUỒN đọc evidence).

## Kiến trúc tổng thể

```
docs/login.md
  → scenario-map    → work/login/scenarios.yaml   (大+中: nghiệp vụ + tình huống)
  → viewpoint-apply → work/login/conditions.yaml   (小: điều kiện + viewpoint + priority)
  → detail-fill     → work/login/details.yaml      (evidence đầy đủ, PHẢI bám doc)
  → testcase-generate (SỬA) → testcases/login.yaml  (lắp ráp: expected_vi + steps + schema)
  → gap-report, coverage-check (không đổi)
```

Machine gate ">20% thiếu evidence" và gate DATA-01 thiếu operator tính ở `commands/design.md`
(orchestration) — không phải trong `detail-fill`, đúng nguyên tắc đã áp dụng cho
`gap-report` ("skill chỉ render/phát hiện theo case, không tự quyết định dừng cả chain").
Gate "thiếu screen item definition HOẶC message list" là kiểm tra cấu trúc 1 lần (docs/
có tồn tại 2 loại tài liệu này không), thực hiện ở bước 0 của `detail-fill`, trước khi
xử lý condition nào — không phải theo từng case.

## `scenario-map`

**Input:** `docs/` (BD trước, DD sau).

**Việc:** Tái dùng đúng khung 大/中 đã có sẵn trong `context/conventions.md`, không phát
minh khái niệm mới:
- 大 (`large`) — nghiệp vụ, đơn vị công việc người dùng nhận thức được. Câu hỏi kích
  hoạt: "người dùng nói gì khi kể về việc họ làm?"
- 中 (`medium`) — tình huống/ngữ cảnh của nghiệp vụ đó. Câu hỏi: "cùng nghiệp vụ này có
  mấy hoàn cảnh khác nhau?"

Không làm 小 (điều kiện cụ thể) — đó là việc của `viewpoint-apply`.

**Output `work/$1/scenarios.yaml`:**

```yaml
- large: "Nghiệp vụ đăng nhập"
  trace: [DD-2, DD-2.1]
  actor: "Người dùng đã có tài khoản"
  situations:
    - medium: "Đăng nhập lần đầu sau khi được cấp tài khoản"
      trace: [DD-2.1]
      trigger_vi: "Mở màn hình đăng nhập, nhập username/password"
      precondition_vi: ["Tài khoản đã được cấp, trạng thái hoạt động"]
    - medium: "Quên mật khẩu"
      trace: [DD-3]
      trigger_vi: "Bấm 'Quên mật khẩu' trên màn hình đăng nhập"
      precondition_vi: []
```

**Self-check bắt buộc:** 3 cột (`large`/`medium`/section tương ứng) có copy được nguyên
văn từ mục lục DD không? Nếu có → sai, đang làm view của dev.

## `viewpoint-apply`

**Input:** `scenarios.yaml`.

**Việc:** Với mỗi `situation`, duyệt qua 6 nhóm trong `context/viewpoints.md`
(BIZ/USER/DATA/TIMING/ENV/IMPACT) + `context/viewpoints-local.md` (dự án). KHÔNG áp cả
bảng cho mọi tình huống — chỉ chọn nhóm mà câu hỏi kích hoạt của nó thực sự áp dụng
được. Với mỗi viewpoint được chọn, sinh 1 condition (`small`) cụ thể, gán `viewpoint`
ID và `priority`.

**Tiêu chí gán `priority`** (tái dùng đúng bảng `conventions.md`, không phát minh thêm):
- **P1** — main path của nghiệp vụ chính, HOẶC boundary của nghiệp vụ chính (boundary
  KHÔNG tự động xuống P3 chỉ vì là boundary).
- **P2** — nhánh phụ/ngoại lệ đã có trong spec.
- **P3** — edge case hiếm, không nêu rõ trong spec nhưng hợp lý để kiểm tra.

**Output `work/$1/conditions.yaml`:**

```yaml
- large: "Nghiệp vụ đăng nhập"
  medium: "Đăng nhập lần đầu sau khi được cấp tài khoản"
  conditions:
    - small: "Password đúng biên dưới"
      trace: [DD-2.1]
      test_level: IT
      viewpoint: DATA-01
      priority: P1
      condition_vi: "Password 8 ký tự (min)"
      precondition_vi: ["Tài khoản đã được cấp, trạng thái hoạt động"]
```

`test_level` suy ra từ `trace`: trace về `BD-*` → `ST`, trace về `DD-*` → `IT`.

**Self-check:** mỗi condition có đúng 1 viewpoint ID chính (không trộn nhiều viewpoint
vào 1 condition)? Viewpoint chọn có nằm trong `viewpoints.md`/`viewpoints-local.md` thật
không (không tự bịa ID)?

## `detail-fill`

**Input:** `conditions.yaml` + `docs/` + `db/`.

**Bước 0 — gate cấu trúc:** kiểm tra `docs/` có tồn tại screen item definition VÀ
message list không (2 loại tài liệu, không phải case cụ thể). Thiếu 1 trong 2 →
dừng ngay lập tức, không xử lý condition nào, báo lý do cụ thể.

**Với mỗi condition:** tìm evidence theo đúng bảng 5 tầng gốc đã có sẵn trong
`context/standards-mapping.md`/`skills/testcase-generate/SKILL.md`:

```
db_definition > screen_item > message_list > dd > spec
```

(Không dùng bảng tổng quát hoá CLI/daemon từ spec `2026-07-17-non-web-system-support-
design.md` — spec đó chưa triển khai, phạm vi rộng hơn nhiều so với riêng `detail-fill`.
Đây là ứng viên nâng cấp sau, không trộn 2 việc.)

Với `viewpoint: DATA-01`, bắt buộc gán `evidence.operator` tường minh — không suy diễn
từ văn xuôi VI, ưu tiên DDL. Không có → gap.

Có evidence → ghi đầy đủ vào `details.yaml`, `evidence_found: true`. Không có → append
1 entry vào `work/$1/gaps.yaml` theo schema + rule gán `id` (`GAP-NNN`, max hiện có + 1)
đã định nghĩa trong `skills/gap-report/SKILL.md`; entry trong `details.yaml` vẫn giữ lại
(không xoá condition) nhưng đánh dấu `evidence_found: false`, `gap_id` trỏ đúng gap vừa
tạo.

**Output `work/$1/details.yaml`:**

```yaml
- large: "Nghiệp vụ đăng nhập"
  medium: "Đăng nhập lần đầu sau khi được cấp tài khoản"
  small: "Password đúng biên dưới"
  trace: [DD-2.1]
  test_level: IT
  viewpoint: DATA-01
  priority: P1
  condition_vi: "Password 8 ký tự (min)"
  precondition_vi: ["Tài khoản đã được cấp, trạng thái hoạt động"]
  evidence_found: true
  evidence:
    section: "DD-2.1"
    quote: "Password từ 8 đến 32 ký tự. DDL: VARCHAR(32) NOT NULL CHECK (LENGTH(password) >= 8)"
    source_type: db_definition
    operator: { min: 8, min_op: ">=", max: 32, max_op: "<=" }
  gap_id: null
```

Entry thiếu evidence (ví dụ):

```yaml
- large: "Nghiệp vụ đăng nhập"
  medium: "Đăng nhập lần đầu sau khi được cấp tài khoản"
  small: "Password dưới biên (7 ký tự)"
  trace: [DD-2.1]
  test_level: IT
  viewpoint: DATA-01
  priority: P1
  condition_vi: "Password 7 ký tự (min-1)"
  precondition_vi: ["Tài khoản đã được cấp, trạng thái hoạt động"]
  evidence_found: false
  evidence: null
  gap_id: "GAP-005"
```

**Self-check:** Đã kiểm tra gate cấu trúc (screen item + message list) TRƯỚC khi xử lý
condition nào chưa? Mọi condition thiếu evidence đã append gap đúng schema + đúng rule
`id` chưa? DATA-01 thiếu operator có bị chặn đúng (không suy diễn) chưa?

## `testcase-generate` — thay đổi cần thiết (sửa file đã có)

**Không đổi:** luật "evidence immutable", "cấm suy diễn ngoài evidence", format
`testcases/$1.yaml`, cách sinh `id`/`tags`/`automatable`/`verify[]`, self-check cuối
file (đa số vẫn hợp lệ).

**Đổi:** Quy trình bước 1-5 hiện tại (đọc condition → tự tìm evidence trong `docs/` →
trích quote → ghi source_type → không tìm được thì gap) **thay bằng**: đọc
`work/$1/details.yaml` thay vì `conditions.yaml`; với mỗi entry `evidence_found: true`,
lấy nguyên `evidence` đã có sẵn (không tự tìm lại trong `docs/`), viết `expected_vi` từ
đúng `evidence.quote` đó (vẫn cấm suy diễn ngoài evidence — luật không đổi, chỉ đổi
nguồn), rồi sinh `steps[]`. Entry `evidence_found: false` → **bỏ qua, không tạo case**
(gap đã được `detail-fill` ghi rồi, không ghi trùng).

## Fixture

Viết lại `dev-fixtures/login-project/` chạy thật xuyên suốt: `docs/login.md` (giữ
nguyên nội dung 5 section đã có) → `scenarios.yaml` → `conditions.yaml` → `details.yaml`
→ `testcases/login.yaml`, thay thế case viết tay hiện tại bằng đúng case do chain sinh
ra. Sau khi thay, verify lại `reports/login-gap.md` và `reports/login-coverage.md` vẫn
đúng với `gaps.yaml` mới (nhiều khả năng có thêm gap do `detail-fill` raise, cần tính
lại severity/coverage cho khớp).

## Ngoài phạm vi (out of scope) design này

- Bảng evidence tổng quát hoá cho CLI/daemon (`2026-07-17-non-web-system-support-design.md`)
  — vẫn là mục riêng trong backlog, không trộn vào đây.
- `/qa-kit:ready`, `/qa-kit:data`, `/qa-kit:complete`, `tools/validate.py`,
  `tools/harness.py` — không đụng.
- Excel export, CLAUDE.md/README status update cho phần này — cập nhật khi implement
  xong, không phải quyết định thiết kế.

## Kiểm chứng khi implement

Giống cách đã làm với gap-report/coverage-check/export_excel.py: mỗi skill viết xong,
tự đọc lại như fresh executor, chạy tay trên `dev-fixtures/login-project/`, so output
với kỳ vọng ghi trong plan, sửa wording nếu lệch. Thứ tự bắt buộc: `scenario-map` trước
(vì `viewpoint-apply` cần output thật của nó để verify, không phải giả định trên giấy),
rồi `viewpoint-apply`, rồi `detail-fill`, rồi sửa `testcase-generate`, rồi verify lại
`gap-report`/`coverage-check` trên dữ liệu mới.
