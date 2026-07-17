---
name: testcase-generate
description: >
  Sinh test case YAML từ test condition đã map viewpoint. Dùng khi đã chạy xong
  scenario-map và viewpoint-apply, cần ra artifact test case cuối cùng theo
  schemas/testcase.schema.yaml. KHÔNG dùng để đọc source code. KHÔNG dùng để
  sinh Excel trực tiếp.
---

# testcase-generate

## Vai trò

Biến test condition → test case YAML hợp lệ schema. Đây là bước **điền expected**,
là bước duy nhất trong pipeline **bị cấm sáng tạo**.

## Ranh giới bất di bất dịch

| Việc | Được phép sáng tạo? |
|---|---|
| Nghĩ ra condition cần test | ✅ Có (đã làm ở viewpoint-apply) |
| Điền expected result | ❌ **KHÔNG.** Phải trích từ doc. |

> "Case này cần test" — tester tự nghĩ ra được.
> "Kết quả đúng là X" — phải có người xác nhận.

**Không tìm được căn cứ trong doc cho expected → KHÔNG tạo case. Ghi vào gap-report.**

Đây là failure mode nguy hiểm nhất: model sẽ bịa expected result rất trôi chảy,
nghe hợp lý, và reviewer sẽ không bắt được. Thà thiếu case còn hơn có case sai
mà không ai biết.

## Nguồn được đọc

Chỉ đọc:
- `docs/` — BD, DD và **phụ lục** (ưu tiên cao nhất, xem dưới)
- `${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md`, `${CLAUDE_PLUGIN_ROOT}/context/conventions.md`,
  `./context/project-glossary.md`, `./context/viewpoints-local.md`
- output của `scenario-map`, `viewpoint-apply`

**Cấm tuyệt đối:** source code, DB thật, staging. Không có thì hỏi, không suy đoán
từ "thường thì hệ thống sẽ...".

### Nguồn expected, theo thứ tự tin cậy

Không có source code thì boundary/expected chỉ đến từ đây:

1. **DB definition (DDL/ERD)** ← tin cậy nhất. `VARCHAR(32) NOT NULL` là fact,
   không qua tay dịch, không cãi được. Luôn kiểm tra đây TRƯỚC.
2. **Screen item definition** → max length, format, required, default
3. **Message list** → message ID + nội dung lỗi chính xác
4. **API spec** → param range, response code
5. **Văn xuôi DD/spec** ← ưu tiên **thấp nhất**, mơ hồ nhất, qua tay dịch nhiều nhất

Mâu thuẫn giữa DDL và văn xuôi → **không tự chọn bên nào**. Đó là gap, hỏi BrSE.
Thiếu 1–3 → finding lớn, gap-report ngay.

## Quy trình

1. Đọc test condition + viewpoint ID.
2. Với mỗi condition, tìm căn cứ expected trong `docs/`.
3. **Trích nguyên văn** từ `docs/` vào `evidence.quote`. KHÔNG paraphrase, KHÔNG tóm tắt.
4. Ghi `source_type`. Ưu tiên `db_definition` > `screen_item` > `message_list` > `dd` > `spec`.
5. Không tìm được căn cứ → **dừng, ghi gap-report**, không tạo case.
6. Validate schema trước khi ghi file.

### Boundary: BẮT BUỘC `evidence.operator`

Bản dịch VI của comtor **không phân biệt được toán tử biên**:

| Bản VI | Có thể là | Boundary |
|---|---|---|
| "trên 8 ký tự" | `>= 8` | 7 NG / 8 OK |
| "trên 8 ký tự" | `> 8`  | 8 NG / 9 OK |
| "tối đa 32" | `<= 32` | 32 OK / 33 NG |
| "dưới 32"   | `< 32`  | 31 OK / 32 NG |

Cùng một câu VI → boundary **lệch 1** → cả loạt DATA-01 sai, và sai **im lặng**
tới tận UAT.

Với `viewpoint: DATA-01`:
- **Cấm suy diễn toán tử từ văn xuôi.**
- Ưu tiên tuyệt đối `db_definition` (DDL nói `VARCHAR(32)` là hết cãi).
- DDL không có → hỏi comtor/BrSE điền `operator` tường minh.
- Không ai xác nhận → **gap-report, KHÔNG tạo case**.

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
  expected_vi: "Đăng nhập thành công, chuyển sang màn hình chính"
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
      target: "màn hình chính"
      expect: true
```

Case sinh đôi bắt buộc: `IT-LOGIN-004` với password 7 ký tự (min-1) → expected lấy
từ メッセージ一覧. Nếu メッセージ一覧 không có message cho case này → **gap-report**,
không tự chế "hiển thị thông báo lỗi".

## Self-check trước khi ghi

- [ ] Mọi case có `evidence.quote` trích nguyên văn, không paraphrase?
- [ ] Case DATA-01 có `evidence.operator` tường minh chưa? (không có = reject)
- [ ] Đã kiểm tra DDL/ERD TRƯỚC khi lấy boundary từ văn xuôi chưa?
- [ ] Case `automatable: true` có `verify[]` chưa?
- [ ] Không case nào có expected do suy đoán?
- [ ] `category` bám business flow, không copy mục lục DD?
- [ ] `viewpoint` là ID có thật trong viewpoints.md?
- [ ] `trace` đúng level (IT→DD, ST→BD)?
- [ ] Boundary có đủ cặp (min/min-1, max/max+1)?
- [ ] Case không có căn cứ đã chuyển sang gap-report chưa?
