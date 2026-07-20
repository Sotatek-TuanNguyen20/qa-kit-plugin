---
name: scenario-map
description: >
  Đọc docs/ (BD/DD), tách luồng nghiệp vụ theo business flow — KHÔNG theo mục lục
  DD. Sinh work/$1/scenarios.yaml (category.large + category.medium). Bước 1/6 của
  chain /qa-kit:design. KHÔNG sinh test condition cụ thể (việc của viewpoint-apply),
  KHÔNG tìm evidence (việc của detail-fill).
---

# scenario-map

## Vai trò

Đọc `docs/`, xác định "nghiệp vụ" (`category.large`) và "tình huống" (`category.medium`)
của module — tái dùng đúng khung đã có sẵn trong `context/conventions.md`, không phát
minh khái niệm mới.

## Ranh giới

- **Chỉ làm 大+中 (large+medium), KHÔNG làm 小 (small).** Điều kiện test cụ thể là việc
  của `viewpoint-apply` (bước 2).
- **KHÔNG tìm evidence.** Không trích `evidence.quote`, không xác định boundary/data cụ
  thể — đó là việc của `detail-fill` (bước 3).
- **KHÔNG đọc source code.** Chỉ đọc `docs/` (BD trước nếu có, DD sau — BD thường mô tả
  nghiệp vụ cấp cao hơn, dùng để xác định `large`; DD chi tiết hơn, dùng để tách
  `medium`).
- **Bám business flow, cấm bám mục lục DD.** Xem "Self-check" bên dưới.

## Quy trình

1. Đọc toàn bộ `docs/` liên quan tới module `$1` (BD trước nếu có, DD sau).
2. Xác định `large` — đơn vị công việc **người dùng nhận thức được**, KHÔNG phải tên
   màn hình/module/API. Câu hỏi kích hoạt (từ `conventions.md`): "người dùng nói gì khi
   kể về việc họ làm?" Ví dụ: "đăng nhập", "quên mật khẩu", "thanh toán" — dù có thể
   cùng nằm trong 1 màn hình hay 1 mục DD, vẫn là các `large` RIÊNG nếu người dùng coi
   đó là các việc khác nhau. Section chỉ mang tính tổng quan/giới thiệu, không có quy
   tắc nghiệp vụ cụ thể nào → KHÔNG tạo `large`/`medium` nào từ section đó.
3. Với mỗi `large`, liệt kê các `medium` — hoàn cảnh/tình huống khác nhau của CÙNG 1
   nghiệp vụ đó. Câu hỏi kích hoạt: "cùng nghiệp vụ này có mấy hoàn cảnh khác nhau?"
   Ví dụ: "đăng nhập lần đầu sau khi được cấp tài khoản" khác với "đăng nhập sau khi
   đổi mật khẩu" khác với "đăng nhập khi tài khoản bị khoá" — cùng nghiệp vụ "đăng
   nhập" nhưng 3 hoàn cảnh khác nhau. Một cách thực hiện cùng nghiệp vụ theo phương
   thức khác (vd đăng nhập bằng password vs đăng nhập qua SSO) thường là 2 `medium`
   của CÙNG 1 `large`, không phải 2 `large` riêng — vì người dùng vẫn mô tả cả 2 là
   "tôi đăng nhập".
4. Với mỗi `medium`, ghi `trigger_vi` (điều gì khởi động tình huống này — hành động cụ
   thể của actor) và `precondition_vi` (trạng thái hệ thống/dữ liệu cần có trước, mảng
   rỗng nếu không có).
5. Ghi `trace` ở cả 2 cấp — `large.trace` là section bao quát, mỗi `medium.trace` là
   section cụ thể hơn mô tả đúng hoàn cảnh đó.
6. Ghi `actor` cho mỗi `large` — vai trò/loại người dùng liên quan.

## `work/$1/scenarios.yaml`

```yaml
- large: "Nghiệp vụ đăng nhập"
  trace: [DD-2, DD-2.1, DD-4]
  actor: "Người dùng đã có tài khoản"
  situations:
    - medium: "Đăng nhập lần đầu sau khi được cấp tài khoản"
      trace: [DD-2.1]
      trigger_vi: "Mở màn hình đăng nhập, nhập username/password"
      precondition_vi: ["Tài khoản đã được cấp, trạng thái hoạt động"]
    - medium: "Đăng nhập qua SSO nội bộ công ty"
      trace: [DD-4]
      trigger_vi: "Chọn phương thức đăng nhập SSO trên màn hình đăng nhập"
      precondition_vi: []
```

## Self-check trước khi ghi file

- [ ] `large`/`medium` có bám business flow, KHÔNG copy được nguyên văn từ mục lục
      DD/heading numbering không? (Nếu copy được → sai, đang làm view của dev.)
- [ ] Mỗi `large` trả lời được câu hỏi "người dùng nói gì khi kể việc họ làm"?
- [ ] Mỗi `medium` là 1 hoàn cảnh THỰC SỰ khác nhau, không phải lặp lại cùng 1 tình
      huống bằng câu chữ khác?
- [ ] `trace` ở cả 2 cấp đều trỏ đúng section thật trong `docs/`?
- [ ] Section chỉ mang tính tổng quan (không có quy tắc nghiệp vụ cụ thể) đã bị loại
      khỏi file, không tạo `large`/`medium` rỗng cho nó?
- [ ] KHÔNG có `small`/điều kiện test cụ thể nào lọt vào file này?
