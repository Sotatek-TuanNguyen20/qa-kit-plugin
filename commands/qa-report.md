---
description: Sinh báo cáo kết quả test cho 1 round. Không sửa gì, chỉ tổng hợp.
argument-hint: <module> [round]
allowed-tools: Read, Write
---

# /qa-report $1

Đọc `results/$1-r*.yaml` -> `reports/$1-r<N>-report.md`. **Read-only.**

## Số liệu bắt buộc

| Chỉ số | Công thức | Ghi chú |
|---|---|---|
| 消化率 (execution rate) | (đã chạy)/(tổng) | blocked KHÔNG tính là đã chạy |
| Pass rate | pass/(đã chạy) | |
| 未消化 | not_run + blocked | tách riêng 2 con số |
| Bug còn mở | A_bug chưa đóng | chia P1/P2/P3 |
| **Regression** | prev_status=pass & status=fail | **để LÊN ĐẦU báo cáo** |

## Regression lên đầu, không phải pass rate

Case `pass -> fail` nghĩa là **fix của dev đã phá chỗ khác**. Đây là tín hiệu đắt nhất
trong cả báo cáo, và là thứ dễ bị chôn dưới đống số liệu đẹp.

Có regression -> ghi ngay dòng đầu, kể cả pass rate 95%.

## blocked ≠ fail

Trộn 2 cái này là bóp méo báo cáo:
- `fail` = đã test, kết quả sai -> có bug
- `blocked` = **chưa test được**, bị bug khác chặn đường

Nhiều `blocked` mà pass rate cao = **báo cáo lạc quan giả**. Phải nêu rõ:
"Pass 95% nhưng 30 case blocked, chưa biết chất lượng vùng đó."

## Bug convergence

Vẽ số bug mới phát hiện theo round:
```
R1: 24 | R2: 11 | R3: 3 | R4: 1
```
Còn tăng hoặc đi ngang -> **chưa hội tụ, chưa được release**, dù 消化率 100%.
Con số này quan trọng hơn pass rate.

## Cấu trúc report

1. Kết luận 1 dòng: đạt exit criteria chưa? (Có/Không + lý do)
2. **Regression** (nếu có) ← lên trước mọi thứ
3. 消化率 + 未消化 (tách not_run / blocked)
4. Bug còn mở theo severity
5. Bug convergence qua các round
6. Case triage_confidence=low -> cần human soi
7. E_spec -> nối vào gap-report

## Cấm

- Sửa `testcases/` hay `results/`
- Gộp blocked vào not_run
- Báo pass rate mà không báo số blocked
- Kết luận "OK để release" khi bug chưa hội tụ
