---
description: Scaffold repo dự án QC. Chạy 1 lần khi bắt đầu dự án mới.
argument-hint: <project-name>
allowed-tools: Read, Write, Bash
---

# /qa-kit:init $1

## Vì sao command này tồn tại

Plugin đóng gói được `commands/`, `skills/`, `tools/` — **nhưng KHÔNG đóng gói được
`CLAUDE.md` và `.claude/settings.json`**.

Nghĩa là: cài plugin xong, tester có đủ command nhưng **thiếu sạch guardrail**
(6 nguyên tắc, deny rule chặn source code, guard chống prod).

Command này lấp chỗ đó. Chạy 1 lần/dự án.

## Việc

### Bước 1: Hỏi 5 câu về hệ thống (System Profile)

TRƯỚC khi copy file, hỏi tester 5 câu sau — dùng `AskUserQuestion` nếu tool đó có sẵn
trong phiên hiện tại, không thì hỏi trực tiếp trong hội thoại. Hỏi từng câu một, không dồn
cả 5 câu vào 1 tin nhắn:

1. **Hệ thống test là gì?** — lựa chọn: `web` / `mobile app` / `cli-daemon` / `api-only` / `khác`
2. **Hệ thống có database không?** — có / không
3. **Hệ thống có config file riêng làm nguồn tham số không?** — CHỈ hỏi nếu câu 2 = không.
   có / không
4. **Ai cung cấp seed/test data cho dự án này?** — lựa chọn:
   - `dev/BrSE cấp mẫu thật` (vd file mẫu, tài khoản test thật do dev tạo)
   - `QC tự tạo theo schema/format đã tài liệu hoá`
   - `chưa xác định`
5. **Môi trường test này được dùng như thế nào?** — lựa chọn:
   - `Riêng — không ai khác dùng chung`
   - `Dùng chung, có cơ chế cô lập` — nếu chọn, hỏi thêm 1 dòng mô tả cơ chế (tự do, vd
     "mỗi tester 1 schema DB riêng")
   - `Dùng chung, không có cơ chế cô lập`

Câu 4 = "chưa xác định" hoặc câu 5 = "dùng chung, không có cơ chế cô lập" **không phải lỗi
chặn** — vẫn tiếp tục scaffold bình thường. Đây là rủi ro cần ghi nhận tường minh, không
phải điều kiện dừng.

Ghi lại cả 5 câu trả lời (+ mô tả cơ chế cô lập nếu câu 5 chọn nhánh đó) để dùng ở Bước 3
và Bước 4.

### Bước 2: Copy scaffold

Copy từ `${CLAUDE_PLUGIN_ROOT}/templates/project-scaffold/` vào thư mục hiện tại:

```
CLAUDE.md                    <- 6 nguyên tắc + luật loop
.claude/settings.json        <- deny src/**, deny prod
context/
  project-glossary.md        <- domain dự án. TESTER ĐIỀN.
  viewpoints-local.md        <- 観点 riêng dự án. Rỗng lúc đầu.
config/env.yaml              <- TESTER SỬA: base_url, db host
docs/                        <- test basis (bản VI của comtor)
db/                          <- DDL, ERD
testcases/                   <- source of truth
testdata/
results/
reports/
e2e/
.gitignore
```

Sau khi copy, thay TOÀN BỘ placeholder `<PROJECT_NAME>` trong `CLAUDE.md` và
`context/project-glossary.md` bằng tên dự án thật (`$1`). Copy nguyên văn mà
không thay là bug — 2 file đó sẽ còn nguyên literal `<PROJECT_NAME>`, vô nghĩa
với người đọc sau này.

### Bước 3: Ghi mục "System Profile" vào `CLAUDE.md`

Chèn block sau vào `CLAUDE.md` của project, ngay sau mục "## Đường dẫn", trước mục
"## Ngôn ngữ":

```markdown
## System Profile
- Loại hệ thống: <câu 1>
- Database: <câu 2>
- Nguồn boundary ưu tiên #1: <câu 2 = có -> "db_definition"; câu 2 = không VÀ câu 3 = có ->
  "config_definition"; câu 2 = không VÀ câu 3 = không -> "(không có, chỉ còn văn xuôi)">
- Bộ verify.method gợi ý: <tra bảng dưới theo câu 1>
- Nguồn seed/test data: <câu 4>
- Môi trường: <câu 5, kèm mô tả cơ chế nếu câu 5 chọn nhánh "có cơ chế cô lập">
```

Bảng verify.method gợi ý theo câu 1 (giá trị enum đầy đủ ở `${CLAUDE_PLUGIN_ROOT}/schemas/testcase.schema.yaml`):

| Câu 1 | verify.method gợi ý |
|---|---|
| `web` | `ui_text`, `ui_visible`, `http_status`, `http_body`, `db_query` (nếu câu 2 = có) |
| `api-only` | `http_status`, `http_body`, `db_query` (nếu câu 2 = có) |
| `cli-daemon` | `cli_exit_code`, `cli_output`, `file_exists`, `file_content`, `log_grep` |
| `mobile app` | `ui_text`, `ui_visible` (TẠM — chưa có method riêng cho mobile, ghi chú "tạm" trong CLAUDE.md) |
| `khác` | Không gợi ý sẵn — tester tự chọn từ enum đầy đủ, ghi lý do trong `evidence.note_vi` mỗi case |

### Bước 4: Ghi `config/env.yaml` theo câu 1

`config/env.yaml` đã copy từ template ở Bước 2 (nội dung web-app mặc định) — GHI ĐÈ bằng
đúng 1 trong 3 nội dung dưới đây theo câu 1. Trong MỌI trường hợp, dòng `forbidden_patterns`
ở cuối file phải giữ NGUYÊN VẸN, không đổi — đây là guard an toàn `commands/run.md` phụ
thuộc vào để chặn chạy nhầm prod, không phụ thuộc loại hệ thống.

**Câu 1 = `web` hoặc `api-only`:**
```yaml
# harness đọc file này TRƯỚC KHI chạy bất cứ gì. Guard chống chạy nhầm prod.
target: test

environments:
  test:
    base_url: "https://test.example.local"
    db:                           # xoá cả mục "db" này nếu câu 2 = không
      host: "test-db.local"
      readonly_user: "qa_ro"     # BẮT BUỘC user chỉ có quyền SELECT
      # Cấm để credential ở đây. Dùng biến môi trường.

forbidden_patterns: [prod, production, live, honban, 本番]
```

**Câu 1 = `cli-daemon`:**
```yaml
# harness đọc file này TRƯỚC KHI chạy bất cứ gì. Guard chống chạy nhầm prod.
target: test

environments:
  test:
    ssh_host: "ec2-user@<PUBLIC_IP_OR_HOSTNAME>"   # tester điền IP/hostname thật
    spool_root: "/var/spool/<ten-app>"             # tester điền đường dẫn thật
    external_mock_url: "http://localhost:3000/v2/enqueue"  # đổi tên field theo domain thật
    systemd_services: []                            # tester điền tên service thật

forbidden_patterns: [prod, production, live, honban, 本番]
```

**Câu 1 = `mobile app` hoặc `khác`:**
```yaml
# harness đọc file này TRƯỚC KHI chạy bất cứ gì. Guard chống chạy nhầm prod.
target: test

environments:
  test:
    # Chưa có field mẫu cho loại hệ thống này — tester tự thêm field phù hợp (vd
    # device_farm_url cho mobile), PHẢI có ít nhất 1 field kiểu host/url để
    # forbidden_patterns bên dưới có cái để đối chiếu.

forbidden_patterns: [prod, production, live, honban, 本番]
```

## Hai tầng viewpoints

| | Ở đâu | Ai sửa | Vòng đời |
|---|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md` | **Plugin** | QA lead, qua PR | Version hóa, dùng chung mọi dự án |
| `./context/viewpoints-local.md` | **Project** | Tester | 観点 riêng dự án này |

Đọc **cả hai**, local ghi đè chung khi trùng ID.

観点 local chứng minh được giá trị (bắt bug thật ≥2 lần) -> **promote lên plugin qua PR**.
Đây là cách kit khá lên. Không promote = kinh nghiệm chết trong 1 dự án.

## Đường dẫn — chỗ dễ sai nhất

| Loại | Đường dẫn |
|---|---|
| Của **plugin** (read-only) | `${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md` |
| | `${CLAUDE_PLUGIN_ROOT}/schemas/testcase.schema.yaml` |
| Của **dự án** (tương đối) | `./docs/`, `./testcases/`, `./results/` |

**KHÔNG hardcode đường dẫn tuyệt đối.** Plugin cài vào cache của từng máy, path khác nhau.

## Sau khi chạy — báo tester

```
✅ Scaffold xong: <project-name>

System Profile đã ghi vào CLAUDE.md — kiểm tra lại có đúng ý không.

Việc tester phải làm TRƯỚC khi /qa-kit:design:
1. config/env.yaml     -> điền giá trị thật (host/IP/service...) theo loại hệ thống đã chọn
2. docs/               -> comtor bỏ spec/DD (bản VI) vào
3. db/                 -> xin dev DDL + ERD (nếu có DB) ← nguồn boundary tin cậy nhất
4. context/project-glossary.md -> điền thuật ngữ domain
5. Nếu "Môi trường" = dùng chung, không cô lập -> phối hợp lịch chạy test với người khác;
   /qa-kit:ready sẽ nhắc lại rủi ro này mỗi lần chạy

Kiểm tra: git init && git add . && git commit -m "chore: init qa"
```

Rồi DỪNG. Không tự chạy `/qa-kit:design`.

## Cấm

- Ghi đè file đã tồn tại (dự án đã init rồi -> báo, đừng phá)
- Tự điền `config/env.yaml` bằng giá trị đoán (IP/host/service THẬT phải hỏi tester,
  không tự bịa — chỉ khung field theo loại hệ thống là được viết sẵn)
- Tự `git init`
- Bỏ qua 5 câu hỏi vì "tên project có vẻ đoán được loại hệ thống" — luôn hỏi đủ 5 câu
