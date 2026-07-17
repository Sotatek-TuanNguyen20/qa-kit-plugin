# DD — Đăng nhập (fixture nội bộ, dùng để tự kiểm chứng gap-report/coverage-check)

## DD-1. Tổng quan
Mô tả tổng quan luồng đăng nhập. Không có rule cụ thể, không cần test case.

## DD-2. Xác thực password

### DD-2.1. Độ dài password
Password từ 8 đến 32 ký tự. DDL: `VARCHAR(32) NOT NULL CHECK (LENGTH(password) >= 8)`.

## DD-3. Quên mật khẩu
Người dùng bấm "Quên mật khẩu" trên màn hình đăng nhập, hệ thống gửi email chứa
link reset. Chưa có thêm chi tiết trong tài liệu này.

## DD-4. Đăng nhập SSO
Đăng nhập qua SSO nội bộ công ty. Tài liệu này chưa mô tả field/màn hình cụ thể.
