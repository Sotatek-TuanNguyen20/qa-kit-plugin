---
name: testcase-generate
description: >
  Sinh test case YAML từ work/$1/details.yaml (output của detail-fill — evidence
  đã được tìm sẵn cho từng entry, đánh dấu evidence_found true/false). Dùng khi đã
  chạy xong scenario-map, viewpoint-apply và detail-fill, cần ra artifact test
  case cuối cùng theo schemas/testcase.schema.yaml. Việc tìm evidence trong docs/
  đã chuyển sang detail-fill — skill này chỉ lắp ráp case từ evidence có sẵn,
  KHÔNG tự tìm evidence. KHÔNG dùng để đọc source code. KHÔNG dùng để sinh Excel
  trực tiếp.
---

# testcase-generate

## Vai trò

Biến test condition → test case YAML hợp lệ schema. Đây là bước **điền expected**,
là bước duy nhất trong pipeline **bị cấm sáng tạo**.

## Ranh giới bất di bất dịch

| Việc | Được phép sáng tạo? |
|---|---|
| Nghĩ ra condition cần test | ✅ Có (đã làm ở viewpoint-apply) |
| Điền expected result | ❌ **KHÔNG.** Phải lấy từ `evidence` có sẵn trong `details.yaml` (đã được `detail-fill` trích từ doc). |

> "Case này cần test" — tester tự nghĩ ra được.
> "Kết quả đúng là X" — phải có người xác nhận.

**Entry `evidence_found: false` trong `details.yaml` → KHÔNG tạo case.** Gap đã được
`detail-fill` ghi sẵn vào `work/$1/gaps.yaml` rồi, không tự tìm lại hay ghi trùng.

Đây là failure mode nguy hiểm nhất: model sẽ bịa expected result rất trôi chảy,
nghe hợp lý, và reviewer sẽ không bắt được. Thà thiếu case còn hơn có case sai
mà không ai biết.

## Nguồn được đọc

Chỉ đọc:
- `work/$1/details.yaml` — output của `detail-fill`, nguồn DUY NHẤT cho evidence.
  Mỗi entry đã có sẵn `evidence_found` + (`evidence.section`/`quote`/`source_type`/
  `operator` nếu tìm thấy) hoặc `gap_id` (nếu không), cùng mọi field kế thừa từ
  `conditions.yaml` (`large/medium/small/trace/test_level/viewpoint/priority/
  condition_vi/precondition_vi`). Skill này KHÔNG tự đọc `docs/` để tìm hay đối
  chiếu lại evidence nữa — đó là việc của `detail-fill`.
- `${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md`, `${CLAUDE_PLUGIN_ROOT}/context/conventions.md`,
  `./context/project-glossary.md`, `./context/viewpoints-local.md` — để kiểm tra
  `viewpoint` ID hợp lệ và `category` bám business flow khi lắp ráp case.

**Cấm tuyệt đối:** tự đọc `docs/` để tìm/đối chiếu lại evidence, source code, DB
thật, staging. Nghi ngờ evidence trong `details.yaml` sai hoặc thiếu → đó là phản
hồi gửi lại `detail-fill`/BrSE, không phải việc tự sửa hay tự tìm thêm ở đây.

### Nguồn expected, theo thứ tự tin cậy (tham khảo — `detail-fill` là nơi áp dụng)

Bảng dưới đây là bảng 5 tầng mà `detail-fill` đã áp dụng khi điền `evidence.source_type`
vào `details.yaml` (mỗi tầng có 2 lựa chọn tương đương — web app / CLI-backend, dùng đúng
1 cột theo `CLAUDE.md`'s System Profile). Giữ lại làm tài liệu tham chiếu để hiểu vì sao
một `source_type` được ưu tiên hơn cái khác khi đọc case đã sinh — skill này KHÔNG tự đi
tìm hay tự so sánh lại nguồn, chỉ đọc `source_type` đã có sẵn:

1. **DB definition (DDL/ERD)** hoặc **Config definition** (CLI/backend) ← tin cậy nhất.
   Fact từ artifact sản phẩm, không qua tay dịch, không cãi được.
2. **Screen item definition** hoặc **Fixed format** (định dạng file/protocol cố định,
   CLI/backend) → max length, format, required, default
3. **Message list** hoặc **Log format** (định dạng log/mail alert, CLI/backend) →
   message ID + nội dung lỗi chính xác
4. **DD văn xuôi** — dùng chung cho cả 2 loại hệ thống
5. **Spec văn xuôi** ← ưu tiên **thấp nhất**, mơ hồ nhất, qua tay dịch nhiều nhất — dùng
   chung cho cả 2 loại hệ thống

Mâu thuẫn giữa 2 nguồn, hoặc thiếu nguồn tầng 1–3, đã được `detail-fill` xử lý thành gap
(`evidence_found: false` + `gap_id`) trước khi entry tới được bước này — gặp entry như vậy
thì bỏ qua theo Quy trình bước 2, không tự đánh giá lại xem nguồn nào đáng tin hơn.

## Quy trình

1. Đọc `work/$1/details.yaml` (KHÔNG phải `conditions.yaml` — evidence đã được
   `detail-fill` tìm sẵn, bước này không tự tìm evidence trong `docs/` nữa).
2. Với mỗi entry `evidence_found: false` → **bỏ qua, không tạo case**. Gap đã được
   `detail-fill` ghi vào `work/$1/gaps.yaml` rồi, không ghi trùng.
3. Với mỗi entry `evidence_found: true`, lấy nguyên `evidence` đã có sẵn (section/
   quote/source_type/operator) — KHÔNG tự tìm lại trong `docs/`, KHÔNG tự đổi
   `evidence.quote` đã có.
4. Viết `expected_vi` — suy ra TỪ ĐÚNG `evidence.quote` đó, KHÔNG suy diễn thêm gì
   ngoài evidence (luật này không đổi — chỉ đổi NGUỒN đọc evidence, không đổi mức độ
   nghiêm ngặt).
5. Sinh `steps[]` — hành động cụ thể (UI/CLI) hiện thực hoá `condition_vi`.
6. Gán `id` (`ST-<MODULE>-NNN` hoặc `IT-<MODULE>-NNN` theo `test_level`, số thứ tự
   tăng dần trong module), `tags`, `automatable`, `verify[]` (nếu automatable — case
   thiếu cách verify rõ ràng thì để `automatable: false`, không tự chế cách verify).
7. Validate schema (`schemas/testcase.schema.yaml`) trước khi ghi file.

### Boundary: BẮT BUỘC `evidence.operator`

Bản dịch VI của comtor **không phân biệt được toán tử biên**:

| Bản VI | Có thể là | Boundary |
|---|---|---|
| "trên 8 ký tự" | `>= 8` | 7 NG / 8 OK |
| "trên 8 ký tự" | `> 8`  | 8 NG / 9 OK |
| "tối đa 32" | `<= 32` | 32 OK / 33 NG |
| "dưới 32"   | `< 32`  | 31 OK / 32 NG |

Cùng một câu VI → boundary **lệch 1** → cả loạt DATA-01 sai, và sai **im lặng**
tới tận UAT. Đây là lý do `detail-fill` bắt buộc phải resolve `operator` tường
minh (ưu tiên `db_definition`, không suy diễn từ văn xuôi, gap nếu không ai xác
nhận) trước khi entry tới được bước này.

Với `viewpoint: DATA-01`, việc của skill này chỉ là:
- **Copy nguyên `evidence.operator`** đã có sẵn trong `details.yaml` — cấm tự suy
  diễn hoặc tự đổi operator, kể cả khi văn xuôi `condition_vi` đọc có vẻ mơ hồ.
- Entry `evidence_found: false` (nghĩa là chưa ai xác nhận operator) → bỏ qua
  theo Quy trình bước 2, không tự đoán operator để "cho đủ case".

Đây là chi phí 1 dòng YAML để chặn class bug đắt nhất.

## 大項目/中項目/小項目

Bám **business flow**, không bám mục lục DD.

❌ Sai (view của dev — copy heading DD):
```
large:  "Chức năng đăng nhập"     # = heading DD 3.
medium: "Xử lý xác thực"          # = heading DD 3.2
small:  "Kiểm tra password"       # = heading DD 3.2.1
```

✅ Đúng (view của tester — bám nghiệp vụ):
```
large:  "Nghiệp vụ đăng nhập"
medium: "Đăng nhập lần đầu sau khi cấp tài khoản"
small:  "Password đúng biên"
```

Self-check: nếu 3 cột này copy được từ mục lục DD → đang làm sai.

## Ngôn ngữ

Tiếng Việt 100%. `docs/` đã là bản comtor dịch. Tiếng Nhật ngoài scope.

## Output

Ghi vào `testcases/<module>.yaml`. **KHÔNG sinh Excel.** Excel do `tools/export_excel.py`
sinh ra từ YAML — deterministic, reproduce được.

## Ví dụ

```yaml
- id: IT-LOGIN-003
  trace: [DD-3.2.1]
  test_level: IT
  category:
    large:  "Nghiệp vụ đăng nhập"
    medium: "Xác thực password"
    small:  "Password đúng biên dưới"
  viewpoint: DATA-01
  precondition_vi:
    - "Tài khoản đã được cấp, trạng thái hoạt động"
  condition_vi: "Password 8 ký tự (min)"
  steps:
    - action_vi: "Nhập password 8 ký tự"
      data: { password: "Abcd1234" }
    - action_vi: "Bấm nút đăng nhập"
  expected_vi: "Password 8 ký tự không bị từ chối vì lý do độ dài (thoả điều kiện >= 8 theo DD-3.2.1 bảng 2)."
  evidence:
    section: "DD-3.2.1 bảng 2"
    quote: "Mật khẩu từ 8 đến 32 ký tự"
    source_type: db_definition
    operator: { min: 8, min_op: ">=", max: 32, max_op: "<=" }
    note_vi: "DDL: VARCHAR(32) + CHECK(LENGTH>=8). Boundary: 7/8 và 32/33."
  priority: P1
  tags: [smoke]
  automatable: true
  verify:
    - method: ui_visible
      target: "thông báo lỗi độ dài password (vd 'Mật khẩu quá ngắn')"
      expect: false
```

`expected_vi` chỉ khẳng định đúng phần evidence chứng minh (độ dài không bị từ chối) —
KHÔNG khẳng định "đăng nhập thành công" hay "chuyển sang màn hình chính", vì rule độ
dài không hề nói tới việc xác thực username/password có khớp tài khoản hay không (đó
là 1 claim khác, cần evidence khác — xem "Phạm vi evidence" trong
`skills/detail-fill/SKILL.md`). `verify[]` cũng đổi theo: kiểm tra thông báo lỗi độ
dài KHÔNG xuất hiện — đây là điều evidence trực tiếp chứng minh được, thay vì kiểm
tra 1 màn hình cụ thể mà evidence không hề nhắc tới.

Case sinh đôi bắt buộc: `IT-LOGIN-004` với password 7 ký tự (min-1) — tương ứng
1 entry riêng trong `details.yaml`. Nếu entry đó có `evidence_found: false` (vd
chưa có メッセージ一覧 xác nhận nội dung lỗi) → **bỏ qua theo Quy trình bước 2**,
không tự chế "hiển thị thông báo lỗi" để lấp chỗ trống — gap đã được `detail-fill`
ghi vào `work/$1/gaps.yaml` rồi.

## Self-check trước khi ghi

- [ ] Mọi case có `evidence.quote` copy NGUYÊN VĂN từ `details.yaml`, không tự
      paraphrase/viết lại khi lắp ráp?
- [ ] Case DATA-01 có `evidence.operator` tường minh, copy nguyên từ `details.yaml`
      chưa? (không có = reject, không tự suy diễn)
- [ ] Mọi entry `evidence_found: true` đã lấy `evidence` nguyên vẹn từ
      `details.yaml` chưa (không tự đọc lại `docs/` để đối chiếu/tìm thêm)?
- [ ] Case `automatable: true` có `verify[]` chưa?
- [ ] Không case nào có expected do suy đoán ngoài `evidence.quote` chưa?
- [ ] `category` bám business flow, không copy mục lục DD?
- [ ] `viewpoint` là ID có thật trong viewpoints.md?
- [ ] `trace` đúng level (IT→DD, ST→BD)?
- [ ] Boundary có đủ cặp (min/min-1, max/max+1) — với điều kiện cả 2 entry tương
      ứng đều `evidence_found: true` trong `details.yaml`?
- [ ] Mọi entry `evidence_found: false` đã bị bỏ qua chưa (không tạo case, không
      tự ghi thêm gap mới — `detail-fill` đã ghi rồi)?
