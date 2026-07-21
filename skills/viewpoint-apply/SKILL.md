---
name: viewpoint-apply
description: >
  Đọc work/$1/scenarios.yaml, áp quan điểm test (viewpoint) từ context/viewpoints.md
  + viewpoints-local.md, sinh test condition cụ thể (category.small) + gán priority.
  Sinh work/$1/conditions.yaml. Bước 2/6 của chain /qa-kit:design. Condition ĐƯỢC vượt
  ngoài doc — đây là chỗ tester tư duy. KHÔNG tìm evidence cho expected (việc của
  detail-fill).
---

# viewpoint-apply

## Vai trò

Với mỗi tình huống (`medium`) từ `scenarios.yaml`, chọn quan điểm test (viewpoint) phù
hợp, sinh điều kiện test cụ thể (`small`) và gán mức ưu tiên (`priority`).

## Ranh giới

- **Condition được vượt ngoài doc.** Nghĩ ra điều kiện cần test là việc CỦA tester —
  doc không nói tới cũng được, miễn có lý do (viewpoint) hợp lý.
- **KHÔNG áp cả bảng viewpoints.md cho mọi tình huống.** Chọn nhóm/viewpoint THỰC SỰ
  liên quan, bỏ qua nhóm không áp dụng.
- **Mỗi condition chỉ 1 viewpoint ID chính** — không trộn nhiều viewpoint vào 1
  condition.
- **KHÔNG tìm evidence, KHÔNG điền expected.** Đó là việc của `detail-fill`/
  `testcase-generate`. Ở bước này chỉ có `condition_vi` (mô tả điều kiện), không có
  `expected_vi`.

## Quy trình

1. Đọc `work/$1/scenarios.yaml`.
2. Với mỗi `situation` (`medium`), duyệt qua 6 nhóm trong `context/viewpoints.md`
   (BIZ/USER/DATA/TIMING/ENV/IMPACT) + `context/viewpoints-local.md` (nếu dự án có,
   file không tồn tại hoặc rỗng thì bỏ qua, không lỗi). Với mỗi nhóm, tự hỏi: câu hỏi
   kích hoạt của nhóm này có áp dụng thực sự cho tình huống này không? Nếu không, bỏ
   qua nhóm đó.
3. Với mỗi viewpoint được chọn, sinh 1 `condition` (`small`) — mô tả cụ thể điều kiện
   cần test, gắn đúng 1 `viewpoint` ID (dạng `BIZ-01`, `DATA-03`...).
4. Gán `priority` theo 3 tiêu chí (tái dùng đúng bảng `context/conventions.md`, không
   phát minh thêm):
   - **P1** — main path của nghiệp vụ chính, HOẶC boundary của nghiệp vụ chính
     (boundary KHÔNG tự động xuống P3 chỉ vì là boundary — đây là chỗ hay bị đánh giá
     thấp).
   - **P2** — nhánh phụ/ngoại lệ đã có trong spec.
   - **P3** — edge case hiếm, không nêu rõ trong spec nhưng hợp lý để kiểm tra.
5. Xác định `test_level`: `trace` trỏ về `BD-*` → `ST`; trỏ về `DD-*` → `IT`.
6. Kế thừa `trace`/`precondition_vi` từ `situation` tương ứng, bổ sung thêm nếu
   condition cụ thể cần precondition riêng.

## `work/$1/conditions.yaml`

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
    - small: "Password dưới biên (thiếu 1 ký tự)"
      trace: [DD-2.1]
      test_level: IT
      viewpoint: DATA-01
      priority: P1
      condition_vi: "Password 7 ký tự (min-1)"
      precondition_vi: ["Tài khoản đã được cấp, trạng thái hoạt động"]
```

## Self-check trước khi ghi file

- [ ] Mỗi condition có đúng 1 viewpoint ID chính, ID đó có thật trong
      `viewpoints.md`/`viewpoints-local.md` không (không tự bịa ID)?
- [ ] Có nhóm viewpoint nào bị áp lan man, không thực sự liên quan tới tình huống
      không?
- [ ] Boundary của nghiệp vụ chính có bị đánh giá nhầm xuống P3 không?
- [ ] `test_level` khớp đúng `trace` (BD→ST, DD→IT)?
- [ ] KHÔNG có `expected_vi`/evidence nào lọt vào file này?
