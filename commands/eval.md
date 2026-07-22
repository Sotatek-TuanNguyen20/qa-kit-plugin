---
description: Triage kết quả fail -> routing tới đúng người. KHÔNG sửa gì.
argument-hint: <module> [round]
allowed-tools: Read, Write
---

# /qa-kit:eval $1

Đọc `results/$1-r<N>.yaml`, phân loại từng fail, ghi lại. **Không sửa bất cứ thứ gì.**

QC không sửa code, không sửa script sản phẩm. Việc của bước này là trả lời:
**"gửi cái này cho ai?"**

## Luật tối cao

**CẤM sửa `expected_vi` cho khớp `actual`.**

`evidence` immutable. Muốn đổi expected -> phải đổi evidence -> evidence trích từ
`docs/` -> docs không đổi -> không đổi được. Đang muốn sửa expected = đó là **A_bug**
hoặc **E_spec**.

## Triage -> routing

| Loại | Dấu hiệu | Gửi ai |
|---|---|---|
| `A_bug` | actual != expected, script đúng, env ổn | Dev |
| `B_testcase` | expected mâu thuẫn evidence | QC lead |
| `C_script` | selector sai, thiếu wait, race | Automation engineer |
| `D_env` | data chưa seed, service down | QC/Infra |
| `E_spec` | evidence không đủ kết luận | BrSE -> khách |

**Không chắc -> `A_bug`** + `triage_confidence: low`.
Nghi ngờ nghiêng "có bug", KHÔNG nghiêng "test sai".

Chi tiết cây quyết định + bảng bẫy: `${CLAUDE_PLUGIN_ROOT}/skills/test-triage/SKILL.md`.

## Kiểm tra bắt buộc

- `blocked` tách khỏi `fail`. blocked = chưa test được, phải có `blocked_by`.
- `prev_status: pass` + `status: fail` -> **REGRESSION**. Luôn A_bug, luôn P1.
- Case `automatable: false` -> kết quả từ checklist tester, không tự suy.

## Output

Ghi ngược vào `results/$1-r<N>.yaml`: `triage`, `triage_confidence`, `reason`, `bug_id`.

Khi `triage: A_bug`, gán thêm `priority` (P1/P2/P3): regression (`prev_status: pass`
+ `status: fail`) luôn `P1`; còn lại QC gán theo mức độ ảnh hưởng nghiệp vụ.

Rồi in:
```
Round 2 / build v1.2.3
Pass 42 | Fail 6 | Blocked 2 | Not run 0

REGRESSION: 1  ← IT-LOGIN-007 (pass ở R1)

A_bug        4  -> dev        (1 confidence=low, cần soi)
B_testcase   1  -> QC lead
C_script     1  -> automation
D_env        0
E_spec       0
```

Rồi DỪNG. Không tự tạo ticket, không tự gửi ai, không chạy /qa-kit:report.

## Cấm

- Sửa `testcases/`, sửa code, sửa script
- Gộp blocked vào fail
- Gán C/D vì "nó tự sửa được" — đọc bảng bẫy trong test-triage
