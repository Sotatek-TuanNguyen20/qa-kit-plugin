# テスト観点 riêng dự án

> Bổ sung cho `${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md` (dùng chung mọi dự án).
> File này chỉ chứa 観点 **đặc thù dự án này**. Trùng ID -> file này thắng.

## Cách nuôi

Mỗi bug lọt qua design (khách chỉ ra, hoặc lọt tới UAT/production):
1. Hỏi: **観点 nào đáng lẽ bắt được nó?**
2. Có trong viewpoints chung rồi -> không phải lỗi 観点, là lỗi apply. Xem lại /qa-design.
3. Chưa có -> thêm vào đây.

## Promote lên plugin

観点 ở đây bắt được bug thật **≥ 2 lần** -> mở PR đưa lên
`${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md`. Mọi dự án khác hưởng.

**Không promote = kinh nghiệm chết trong 1 dự án.** Đây là điểm khác biệt giữa
"team dùng AI" và "team tích lũy được tài sản".

---

## Danh sách

<!-- Format y hệt viewpoints.md của plugin.
     ID phải có prefix dự án để không đụng: <PROJ>-BIZ-01

| ID | 観点 | Câu hỏi kích hoạt | Nguồn |
|---|---|---|---|
| ABC-BIZ-01 | Chốt sổ cuối tháng | Thao tác vắt qua 23:59 ngày cuối tháng? | BUG-0231, BUG-0455 |
-->

| ID | 観点 | Câu hỏi kích hoạt | Nguồn (bug nào đẻ ra 観点 này) |
|---|---|---|---|
| | | | |
