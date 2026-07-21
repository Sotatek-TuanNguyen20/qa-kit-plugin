---
name: detail-fill
description: >
  Đọc work/$1/conditions.yaml + docs/ + db/, tìm evidence đầy đủ cho từng condition
  (mọi tầng: db_definition/screen_item/message_list/dd/spec), gán boundary operator
  cho DATA-01. Sinh work/$1/details.yaml. Bước 3/6 của chain /qa-kit:design — bước
  DUY NHẤT tìm evidence trong toàn chain (testcase-generate không tự tìm nữa, đọc lại
  từ đây). Expected PHẢI bám doc — không suy diễn.
---

# detail-fill

## Vai trò

Với mỗi condition từ `conditions.yaml`, tìm căn cứ (evidence) đầy đủ trong `docs/`
(+ `db/` nếu có) — đây là bước DUY NHẤT trong chain đọc doc để tìm evidence.
`testcase-generate` (bước 4) không tự tìm evidence nữa, chỉ đọc lại evidence đã có sẵn
từ `details.yaml`.

## Ranh giới

- **Expected PHẢI bám doc, KHÔNG suy diễn.** Condition được vượt ngoài doc (đã làm ở
  `viewpoint-apply`) — nhưng bằng chứng cho kết quả đúng thì KHÔNG được bịa.
- **Đây là bước DUY NHẤT tìm evidence trong chain.** Trước đây `testcase-generate` tự
  tìm evidence — giờ chuyển hết về đây để tránh 2 skill cùng đọc doc độc lập, có thể
  trích 2 quote khác nhau cho cùng 1 điều kiện. `testcase-generate` giờ chỉ lắp ráp từ
  evidence đã có sẵn ở đây.
- **Không tìm được evidence → append gap, GIỮ LẠI entry trong `details.yaml`** (đánh
  dấu `evidence_found: false`), KHÔNG xoá condition khỏi file. `testcase-generate` sẽ
  tự bỏ qua entry này khi lắp ráp case.
- **KHÔNG tự quyết định dừng cả chain.** Việc đếm tỷ lệ >20% thiếu evidence để dừng
  `/qa-kit:design` là việc của `commands/design.md` (orchestration), không phải của
  skill này — `detail-fill` chỉ xử lý từng condition, ghi kết quả, không tự ý dừng vì
  lý do "quá nhiều gap" (trừ gate cấu trúc ở bước 0 dưới đây).

## Bước 0 — gate cấu trúc (kiểm tra 1 lần, TRƯỚC khi xử lý condition nào)

Kiểm tra `docs/` có tồn tại **screen item definition** VÀ **message list** không (2
loại tài liệu, không phải case cụ thể). Thiếu 1 trong 2 → **DỪNG NGAY**, không xử lý
condition nào, báo rõ thiếu loại tài liệu nào. Đây là gate cấu trúc: không có 2 loại
tài liệu này thì không thể có evidence đáng tin cho case normal/error, xử lý tiếp cũng
vô nghĩa.

**Phân biệt với gap per-condition (đọc kỹ trước khi kết luận gate fail):** gate này
kiểm tra ở tầng **loại tài liệu có áp dụng được cho module hay không** — không phải
"đã có đủ 100% field/message cho mọi màn hình chưa". DD ở giai đoạn đầu luôn thiếu sót
(đó là lý do `gaps.yaml` tồn tại). Gate CHỈ fire khi toàn bộ `docs/` **không có bất kỳ
dấu hiệu nào** cho thấy 2 khái niệm này áp dụng cho module — vd: `docs/` rỗng/chỉ có
tiêu đề, hoặc module rõ ràng không phải hệ có màn hình/tương tác người dùng (CLI/daemon
thuần, xem ghi chú ngoài phạm vi bên dưới) nên khái niệm "màn hình"/"message" không có
nghĩa. Nếu DD có nhắc tới màn hình, field, nút bấm, hành vi validate/từ chối — dù rải
rác, dù chưa mô tả đủ cho mọi màn hình hay mọi message cụ thể — thì đó là dấu hiệu 2
loại tài liệu này CÓ áp dụng, gate KHÔNG fire. Case/màn hình/message cụ thể còn thiếu
được xử lý ở bước 5 dưới đây bằng gap per-condition (`missing_screen_item` /
`missing_message_list`), không phải bằng gate này.

## Bảng ưu tiên nguồn evidence

Tái dùng đúng bảng gốc (web-app) đã có trong `context/standards-mapping.md` +
`skills/testcase-generate/SKILL.md` — KHÔNG dùng bảng tổng quát hoá CLI/daemon (spec
`docs/superpowers/specs/2026-07-17-non-web-system-support-design.md` chưa triển khai,
phạm vi rộng hơn riêng skill này, để dành nâng cấp sau):

```
db_definition > screen_item > message_list > dd > spec
```

Mâu thuẫn giữa 2 nguồn (vd DDL nói khác văn xuôi) → KHÔNG tự chọn bên nào, đó là gap
(`gap_type: contradiction`).

### Phạm vi evidence: phải chứng minh ĐÚNG claim đang test, không phải 1 fact liên quan

Evidence tìm được phải trực tiếp chứng minh đúng nội dung `condition_vi` đang test —
không phải một fact liền kề, nghe có vẻ liên quan nhưng thực ra chỉ chứng minh 1
claim hẹp hơn. Ví dụ: rule DDL về ĐỘ DÀI password (`VARCHAR(32) NOT NULL
CHECK (LENGTH(password) >= 8)`) chỉ chứng minh "password đúng định dạng/độ dài này
được chấp nhận, không bị từ chối vì lý do độ dài" — nó KHÔNG chứng minh "đăng nhập
thành công" (kết quả đó còn phụ thuộc thêm: username đúng, password khớp đúng tài
khoản, tài khoản đang hoạt động... — những claim mà rule độ dài không hề nói tới).

Nếu claim của condition rộng hơn phạm vi evidence thực sự chứng minh:
- Claim CỐT LÕI của condition chính là phần vượt quá evidence (vd condition test
  "đăng nhập thành công" mà evidence chỉ có rule độ dài) → coi như KHÔNG có evidence,
  xử lý theo bước 5 dưới đây (gap), KHÔNG ghi `evidence_found: true`.
- Claim cốt lõi của condition là phần ĐƯỢC evidence chứng minh (vd condition test
  boundary độ dài — evidence chứng minh đúng phần này), phần diễn giải đi kèm rộng
  hơn 1 chút không phải cốt lõi → vẫn `evidence_found: true`, nhưng `testcase-generate`
  khi viết `expected_vi` chỉ được khẳng định đúng phần evidence chứng minh, không
  được mở rộng sang kết quả nghiệp vụ rộng hơn.

### Boundary: BẮT BUỘC `evidence.operator` khi `viewpoint: DATA-01`

Bản dịch VI không phân biệt được `>=` và `>` ("trên 8 ký tự" = cả hai). Cấm suy diễn
toán tử từ văn xuôi — ưu tiên tuyệt đối DDL (`VARCHAR(32)` là fact). DDL không có → hỏi
comtor/BrSE. Không ai xác nhận → gap (`gap_type: missing_operator`), KHÔNG tự đoán.

### Dedup: kiểm tra `gaps.yaml` hiện có trước khi append gap mới

Trước khi tạo entry gap mới ở bước 5 dưới đây, đọc TOÀN BỘ `work/$1/gaps.yaml` hiện có
(kể cả entry `status: answered`) — không chỉ phần do `detail-fill` tự ghi — và tìm xem
đã có entry nào cùng `trace` với condition đang xử lý, đang hỏi CÙNG một câu hỏi cốt lõi
hay không (so khớp theo nội dung/ý câu hỏi, không cần trùng chữ 100%). Có 2 trường hợp:

- **Entry trùng đã `status: answered`** → KHÔNG tạo gap mới. Coi `answer_vi` của entry
  đó là evidence cho condition hiện tại: `evidence_found: true`, `evidence.quote` =
  nguyên văn `answer_vi` (không diễn giải lại), `evidence.section` = tham chiếu tới gap
  gốc (vd `"GAP-004 (đã trả lời)"`), `evidence.source_type: spec` (câu trả lời chính
  thức đã được BrSE xác nhận được coi ngang tầng evidence `spec`), `gap_id: null`.
- **Entry trùng đang `status: open`** → KHÔNG tạo gap mới. Dùng `id` có sẵn của entry đó
  làm `gap_id` cho condition hiện tại — nhiều condition có thể cùng trỏ về 1 gap còn mở,
  không tạo thêm entry trùng trong `gaps.yaml`.

Chỉ tạo gap mới (bước 5) khi không có entry nào — mở hay đã trả lời — đang hỏi cùng câu
hỏi đó.

## Quy trình

1. Chạy gate cấu trúc (bước 0 ở trên). Gate fail → dừng, không làm bước nào dưới đây.
2. Đọc `work/$1/conditions.yaml`.
3. Với mỗi condition, tìm evidence theo đúng bảng ưu tiên ở trên — kiểm tra `db/`
   (DDL/ERD) TRƯỚC, rồi mới tới văn xuôi doc.
4. Tìm được → ghi `evidence: {section, quote, source_type, operator}` (operator chỉ
   khi DATA-01) vào `details.yaml`, `evidence_found: true`, `gap_id: null`.
5. Không tìm được (hoặc mâu thuẫn nguồn, hoặc DATA-01 thiếu operator không ai xác
   nhận) → TRƯỚC KHI append gap mới, áp dụng rule dedup ở mục "Dedup: kiểm tra
   `gaps.yaml` hiện có trước khi append gap mới" bên trên. Chỉ khi không có entry nào
   (open lẫn answered) đã hỏi cùng câu hỏi mới append 1 entry mới vào
   `work/$1/gaps.yaml` theo schema đầy đủ trong `skills/gap-report/SKILL.md` (chọn đúng
   `gap_type`: `missing_evidence` / `contradiction` / `missing_operator` /
   `missing_message_list` / `missing_screen_item`; `severity` tính theo bảng floor
   trong file đó; `id` gán theo rule ở đó — đọc `gaps.yaml` hiện có, lấy số lớn nhất +
   1, KHÔNG tái sử dụng ID). Ghi vào `details.yaml`: `evidence_found: false`,
   `evidence: null`, `gap_id: "<id vừa tạo>"`.
6. Giữ nguyên mọi field khác từ `conditions.yaml` (large/medium/small/trace/
   test_level/viewpoint/priority/condition_vi/precondition_vi) — không sửa, chỉ bổ
   sung thêm.

## `work/$1/details.yaml`

Entry có evidence:

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

Entry thiếu evidence:

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

## Self-check trước khi ghi file

- [ ] Gate cấu trúc (screen item + message list) đã kiểm tra TRƯỚC khi xử lý condition
      nào chưa?
- [ ] Đã kiểm tra `db/` (DDL) TRƯỚC văn xuôi doc cho mọi condition chưa?
- [ ] Mọi condition `DATA-01` có `evidence.operator` tường minh, KHÔNG suy diễn từ văn
      xuôi chưa?
- [ ] Mọi condition thiếu evidence đã append gap đúng schema + đúng rule `id`
      (max hiện có + 1) chưa?
- [ ] Trước khi append gap mới, đã đọc hết `gaps.yaml` hiện có (kể cả `answered`) và
      xác nhận không có gap nào khác đang hỏi cùng câu hỏi chưa — không có gap mới nào
      trùng lặp với entry `open` hoặc `answered` đã có sẵn?
- [ ] Mâu thuẫn nguồn (DDL vs văn xuôi) có bị tự chọn 1 bên không, hay đã ghi thành
      gap `contradiction`?
- [ ] Mọi entry `evidence_found: true` — evidence có thực sự chứng minh ĐÚNG claim cốt
      lõi của condition, không phải 1 fact liền kề chỉ nghe có vẻ liên quan chưa?
- [ ] Field kế thừa từ `conditions.yaml` có bị sửa nhầm không (chỉ được bổ sung,
      không sửa)?
