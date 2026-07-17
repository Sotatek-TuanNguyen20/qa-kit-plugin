# Conventions

> Tài liệu Nhật ghi nhận: lý do phổ biến nhất khiến テスト観点リスト làm xong rồi
> không ai dùng là **rule chia 大/中/小項目 không được định nghĩa thành văn**,
> nên mỗi người điền một kiểu. File này tồn tại để chặn điều đó.

## Rule chia 大項目 / 中項目 / 小項目

Bám **business flow**, KHÔNG bám mục lục DD.

| Tầng | Chứa gì | Câu hỏi kiểm tra |
|---|---|---|
| 大 (large) | **Nghiệp vụ** — đơn vị công việc người dùng nhận thức được | "Người dùng nói gì khi kể về việc họ làm?" |
| 中 (medium) | **Tình huống/ngữ cảnh** của nghiệp vụ đó | "Cùng nghiệp vụ này, có mấy hoàn cảnh khác nhau?" |
| 小 (small) | **Điều kiện test** cụ thể | "Trong hoàn cảnh đó, biến số nào thay đổi?" |

Ví dụ:
```
大: Nghiệp vụ đăng nhập
中: Đăng nhập lần đầu sau khi được cấp tài khoản
小: Password đúng biên dưới (8 ký tự)
```

**Self-check:** copy được 3 dòng này từ mục lục DD → SAI, đang dùng view của dev.

## Naming ID

- `ST-<MODULE>-<3 số>` — trace về spec/BD
- `IT-<MODULE>-<3 số>` — trace về DD
- MODULE viết HOA, không dấu, khớp tên file `testcases/<module>.yaml`

## Priority

| | Nghĩa |
|---|---|
| P1 | Nghiệp vụ chính. Fail = không release được. |
| P2 | Nhánh phụ, ngoại lệ đã có trong spec. |
| P3 | Edge case, mỹ quan. |

Boundary của nghiệp vụ chính = **P1**, không phải P3. Đây là chỗ hay bị đánh giá thấp.

## Definition of Done — 1 test case

- [ ] Có `trace` đúng level (ST→spec, IT→DD)
- [ ] Có `evidence.quote` trích nguyên văn
- [ ] `viewpoint` là ID có thật trong `viewpoints.md`
- [ ] DATA-01 → có `evidence.operator`
- [ ] `automatable: true` → có `verify[]`
- [ ] `category` bám business flow, không copy heading DD

## Definition of Done — 1 module

- [ ] `/qa-kit:design` chạy không bật machine gate
- [ ] gap-report đã gửi BrSE, P1 đã có câu trả lời
- [ ] coverage-check: không còn section nào 0 case (hoặc có lý do ghi rõ)
- [ ] Human review xong, merge vào main

## Exit criteria — khi nào dừng test cycle

Đủ **TẤT CẢ**, không phải đa số:

- [ ] 消化率 100% (not_run = 0). `blocked` KHÔNG tính là đã chạy.
- [ ] Bug P1 còn mở = 0
- [ ] **Bug hội tụ**: số bug mới phát hiện giảm dần qua các round
- [ ] Regression round cuối = 0
- [ ] Mọi `E_spec` đã có câu trả lời từ khách
- [ ] Case `triage_confidence: low` đã được human soi lại

**Bug convergence quan trọng hơn pass rate.** 消化率 100% + pass 98% nhưng round cuối
vẫn ra 12 bug mới = **chưa hội tụ, chưa release được**. Nghĩa là còn cả vùng chưa ai đụng tới.

```
Hội tụ:      R1:24 → R2:11 → R3:3 → R4:1   ✅
Chưa hội tụ: R1:24 → R2:19 → R3:22 → R4:18  ❌ dù pass rate đẹp
```

## Round / build

- 1 round = 1 build. Đổi build giữa round -> **cắt round mới**.
  Trộn kết quả 2 build vào 1 file = báo cáo vô nghĩa.
- `results/<module>-r<N>.yaml` — không ghi đè, không sửa round cũ.
  Lịch sử round là bằng chứng gửi khách.
