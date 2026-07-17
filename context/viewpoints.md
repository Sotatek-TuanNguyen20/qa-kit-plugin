# Thư viện Test観点 (View của Tester)

> Đây là bộ não của cả qa-kit. Không có file này thì Claude generate test case theo
> cấu trúc doc = view của dev.
>
> **File này thuộc PLUGIN** — dùng chung mọi dự án, version hóa, sửa qua PR.
> 観点 riêng dự án -> `./context/viewpoints-local.md` trong repo dự án.
> Claude đọc CẢ HAI; local thắng khi trùng ID.
>
> **Cách nuôi file này:** mỗi bug lọt ra production / mỗi case khách hàng chỉ ra thiếu
> → hỏi "観点 nào đáng lẽ bắt được nó?" → nếu chưa có, thêm vào đây. Đây là tài sản
> tích lũy, không phải file viết một lần.
>
> **Cố ý không có mục nào tên "function" / "API" / "screen".** Đó là trục của dev.

---

## BIZ — 業務観点 (nghiệp vụ)

Dev nhìn 1 màn hình. Tester nhìn 1 luồng nghiệp vụ xuyên nhiều màn hình, nhiều ngày,
nhiều người.

| ID | 観点 | Câu hỏi kích hoạt |
|---|---|---|
| BIZ-01 | Luồng nghiệp vụ end-to-end | Nghiệp vụ này bắt đầu từ đâu, kết thúc ở đâu? Ai bàn giao cho ai? |
| BIZ-02 | Role / permission matrix | Cùng màn hình này, role khác vào thì thấy gì, làm được gì? |
| BIZ-03 | Nghiệp vụ ngoại lệ | Hủy giữa chừng, trả lại, sửa sau khi duyệt, làm lại tháng trước |
| BIZ-04 | Luồng phê duyệt nhiều cấp | Người duyệt nghỉ việc? Duyệt xong mới phát hiện sai? |
| BIZ-05 | Ranh giới kỳ / chốt sổ | Thao tác vắt qua cuối tháng, cuối năm tài chính |
| BIZ-06 | Quy tắc nghiệp vụ ngầm | Doc không viết nhưng nghiệp vụ thực tế bắt buộc |

## USER — 利用者観点 (người dùng thật)

Dev test cái đã code. Tester test cái người dùng thật sự làm.

| ID | 観点 | Câu hỏi kích hoạt |
|---|---|---|
| USER-01 | Thao tác sai / nhầm | Bấm nhầm, nhập nhầm ô, paste cả đoạn |
| USER-02 | Gián đoạn giữa chừng | Đóng tab, F5, back, đóng máy, hết pin |
| USER-03 | Nút back / forward trình duyệt | Back sau khi submit? Back rồi submit lại? |
| USER-04 | Double click / spam click | Tạo 2 record trùng? |
| USER-05 | Nhiều tab song song | Mở 2 tab sửa cùng 1 record |
| USER-06 | Session hết hạn | Hết hạn ngay lúc đang nhập form dài |
| USER-07 | Người dùng thiếu kiên nhẫn | Bấm khi màn hình chưa load xong |

## DATA — データ観点

Dev coi data là param. Tester coi data có vòng đời.

| ID | 観点 | Câu hỏi kích hoạt |
|---|---|---|
| DATA-01 | Boundary value | Min, min-1, min+1, max, max-1, max+1 |
| DATA-02 | Equivalence partition | Chia lớp tương đương, lấy đại diện |
| DATA-03 | Rỗng / null / khoảng trắng | "" vs null vs " " có khác nhau không? |
| DATA-04 | Ký tự đặc biệt | Emoji, 半角/全角, 機種依存文字, ký tự VN có dấu |
| DATA-05 | Độ dài cực đại | Nhập đủ max length → vỡ layout? tràn DB? |
| DATA-06 | Data lifecycle | Data từ đâu ra, ai đã đụng, sống bao lâu, xóa rồi còn tham chiếu? |
| DATA-07 | Data cũ / migration | Record tạo từ version trước có chạy được với logic mới? |
| DATA-08 | Data lượng lớn | 10,000 dòng thì list/export/search ra sao? |
| DATA-09 | Quan hệ tham chiếu | Xóa cha khi còn con? |

## TIMING — タイミング・状態観点

Trục mà dev hay mù nhất.

| ID | 観点 | Câu hỏi kích hoạt |
|---|---|---|
| TIMING-01 | Trạng thái khi thao tác | Cùng nút này, ở state khác thì sao? |
| TIMING-02 | State transition | Vẽ sơ đồ chuyển trạng thái — nhánh nào chưa test? |
| TIMING-03 | Đồng thời (concurrency) | 2 người sửa cùng lúc → ai thắng? mất data ai? |
| TIMING-04 | Thứ tự thao tác | Làm B trước A thì sao? |
| TIMING-05 | Timeout | Timeout giữa lúc xử lý → data dở dang? |
| TIMING-06 | Xử lý bất đồng bộ / batch | Batch chạy lúc user đang thao tác? |
| TIMING-07 | Ngày giờ | Đổi ngày lúc 23:59, năm nhuận, timezone |

## ENV — 環境観点

| ID | 観点 | Câu hỏi kích hoạt |
|---|---|---|
| ENV-01 | Trình duyệt / OS | Chrome/Edge/Safari, bản khách hàng thật sự dùng |
| ENV-02 | Độ phân giải | Màn hình nhỏ → layout vỡ? |
| ENV-03 | Mạng chậm / đứt | Đứt mạng giữa lúc submit |
| ENV-04 | In ấn / xuất file | Excel/PDF xuất ra có đúng như hiển thị? |

## IMPACT — 影響範囲観点

| ID | 観点 | Câu hỏi kích hoạt |
|---|---|---|
| IMPACT-01 | Ảnh hưởng chức năng khác | Sửa chỗ này, chỗ nào dùng chung? |
| IMPACT-02 | Ảnh hưởng data đã có | Logic mới có làm sai data cũ? |
| IMPACT-03 | Ảnh hưởng hệ thống ngoài | API bên ngoài, hệ thống liên kết |
| IMPACT-04 | Regression | Bug cũ từng xảy ra ở vùng này? |

---

## Quy tắc khi apply

1. **Không apply cả bảng cho mọi requirement.** Chọn 観点 phù hợp, ghi lý do loại trừ.
2. **Mỗi case chỉ 1 viewpoint ID chính.** Nhiều 観点 trộn vào 1 case = case không rõ mục đích.
3. **観点 được vượt ngoài doc — expected thì không.** Nghĩ ra được case mà doc im lặng
   → tạo entry trong `gap-report`, không tự chế expected result.
