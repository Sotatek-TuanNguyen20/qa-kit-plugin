---
name: test-triage
description: >
  Phân loại nguyên nhân test fail để ROUTING tới đúng người. Dùng trong /qa-eval.
  KHÔNG sửa gì cả — QC không sửa code, không sửa script sản phẩm.
---

# test-triage

## Vai trò: routing, không phải fixing

QC chạy test, thấy fail, phải trả lời: **"gửi cái này cho ai?"**

Sai địa chỉ = tốn thời gian cả hai bên và bug quay lại sau 2 ngày.

| Loại | Nghĩa | Gửi ai |
|---|---|---|
| `A_bug` | App sai so với spec | **Dev** — bug report |
| `B_testcase` | Test case sai logic | **QC lead** — sửa testcases/ |
| `C_script` | Script automation lỗi | **Automation engineer** |
| `D_env` | Env/data chưa sẵn sàng | **QC/Infra** — chuẩn bị lại, chạy lại |
| `E_spec` | Spec mơ hồ, không kết luận nổi | **BrSE** — hỏi khách |

**Skill này KHÔNG sửa gì.** Không sửa code, không sửa script, không sửa test case.
Chỉ phân loại + ghi lý do.

## Luật tối cao

**CẤM sửa `expected_vi` cho khớp `actual`.**

`evidence` immutable. Muốn đổi expected -> phải đổi evidence -> evidence trích từ
`docs/` -> docs không đổi -> **không đổi được**.

Đang muốn sửa expected? Đó là **A** hoặc **E**. Không bao giờ là B, trừ khi chứng minh
được expected mâu thuẫn chính evidence của nó.

## Cây quyết định

```
Test fail
│
├─ Chạy tới bước verify chưa?
│   └─ CHƯA -> element không thấy / timeout / crash
│       ├─ Selector đổi, thiếu wait, race     -> C_script
│       ├─ Service down, data chưa seed       -> D_env
│       └─ App crash / lỗi 500                -> A_bug  ← đừng nhầm thành C
│
└─ RỒI, actual != expected
    ├─ expected có đúng theo evidence.quote không?
    │   ├─ KHÔNG, mâu thuẫn evidence   -> B_testcase  (hiếm, phải chứng minh)
    │   └─ CÓ
    │       ├─ evidence đủ rõ để kết luận app sai -> A_bug
    │       └─ evidence mơ hồ, không kết luận nổi -> E_spec
    └─ Precondition không thỏa -> D_env
```

## Mặc định khi không chắc: A_bug

Nghi ngờ -> nghiêng **"có bug"**, KHÔNG nghiêng "test sai".

Chi phí bất đối xứng: báo nhầm bug tốn 30 phút của dev. Giấu bug thật tốn cả release.
Bias phải lệch theo chi phí.

Ghi `triage_confidence: low` để human soi lại.

## Bẫy hay gặp

| Hiện tượng | Hay gán nhầm | Thật ra |
|---|---|---|
| Lỗi 500 khi nhập ký tự đặc biệt | C_script | **A_bug** — đó chính là bug |
| Timeout khi data lớn | D_env | **A_bug** — nếu spec có ràng buộc hiệu năng |
| Element không thấy sau submit | C_script | **A_bug** — nếu spec bảo phải hiển thị |
| Message lệch chút ít | B_testcase | **A_bug** — trừ khi evidence chỉ nêu ý nghĩa |
| Fail khi chạy song song, pass khi riêng | C_script (flaky) | **A_bug** — nếu là bug đồng thời (TIMING-03) |

Điểm chung: **C/D nghe như "không phải lỗi ai", nên dễ gán.** Đó là bias phải chống.

## blocked ≠ fail

Case không chạy được vì bug khác chặn đường -> `status: blocked` + `blocked_by: BUG-xxx`.
**KHÔNG phải fail, KHÔNG triage.** Gán fail = thổi phồng số bug; gán skip = giấu rủi ro.

## Regression = ưu tiên cao nhất

`prev_status: pass` + `status: fail` -> fix của dev đã phá chỗ khác.
Luôn `A_bug`, luôn P1, ghi rõ "REGRESSION từ round N".

## Output

```yaml
- id: IT-LOGIN-003
  status: fail
  actual: "Báo lỗi độ dài password"
  triage: A_bug
  triage_confidence: high
  reason: "Nhập 8 ký tự. evidence.operator min_op '>=' -> 8 phải hợp lệ. App sai."
  bug_id: BUG-0112
  evidence_ref: [screenshots/login-003.png]
```

## Self-check

- [ ] Đã phân loại HẾT fail chưa?
- [ ] Có case nào định sửa `expected` không? -> dừng, đó là A hoặc E
- [ ] Case gán C/D: đã đọc bảng bẫy chưa?
- [ ] Không chắc -> đã gán A + confidence low chưa?
- [ ] blocked có tách khỏi fail chưa?
- [ ] Regression có đánh dấu chưa?
- [ ] `testcases/*.yaml` còn nguyên vẹn chứ?
