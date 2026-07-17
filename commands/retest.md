---
description: Tính scope round tiếp theo. Không chạy, chỉ ra danh sách + lý do.
argument-hint: <module> <new_build_version>
allowed-tools: Read, Write
---

# /qa-kit:retest $1

Round N kết thúc, dev đã fix, có build mới. Câu hỏi: **round N+1 chạy những case nào?**

## Trả lời SAI: "chạy lại case fail"

Bỏ sót regression. **Fix của dev có thể phá case đang pass** — và vì không ai chạy lại
case đó, bug ngủ tới UAT. Đây là cách phần lớn bug lọt lưới ở dự án offshore.

## Scope đúng — 3 nhóm

| Nhóm | Case nào | scope_reason |
|---|---|---|
| 1 | fail ở round N, bug đã fix ở build mới | `retest_failed` |
| 2 | blocked ở round N, giờ hết bị chặn | `retest_failed` |
| 3 | **đang PASS nhưng nằm vùng ảnh hưởng của fix** | `regression` |

Thiếu nhóm 3 = round này vô nghĩa về mặt đảm bảo chất lượng.

## Nhóm 3 — xác định vùng ảnh hưởng thế nào

QC không đọc source, không biết dev sửa file nào. Hai nguồn:

**a. Dev khai báo 影響範囲 trong fix note** (chính xác hơn)
   - Không có khai báo -> **hỏi dev, KHÔNG tự đoán**
   - Đây là process gap, ghi vào report

**b. Suy từ trace + business flow** (an toàn hơn, scope rộng hơn)
   - Case cùng `trace` section với case đã fix
   - Case cùng `category.large` (cùng nghiệp vụ)
   - Case có viewpoint `IMPACT-01/02/03`
   - Case dùng chung data/màn hình trong flow

Có (a) -> dùng (a), giao với (b) để kiểm tra chéo.
(a) và (b) lệch nhau nhiều -> **cờ đỏ**, dev và QC đang hiểu khác nhau về phạm vi fix.
Nêu trong report, đừng im lặng chọn một bên.

## Không có thông tin -> chọn rộng

Không xác định được vùng ảnh hưởng -> retest **cả `category.large`** chứa case đã fix.
Tốn thời gian còn hơn lọt bug. Ghi rõ lý do scope rộng để lead biết đây là hệ quả
của việc thiếu 影響範囲 từ dev.

## Output

`work/$1/retest-scope-r<N+1>.md`:
```
Round: 3
Build: v1.2.4
Tổng: 27 case

[retest_failed] 8   — bug đã fix: BUG-011, BUG-014
[retest_failed] 3   — hết blocked (BUG-011 đã fix)
[regression]   16   — vùng ảnh hưởng BUG-011 (dev khai: nghiệp vụ đăng nhập)

Cảnh báo:
- BUG-014 không có khai báo 影響範囲 -> scope mở rộng cả category.large "Nghiệp vụ đăng nhập"
```

Rồi DỪNG. Human duyệt scope trước khi `/qa-kit:run`.
