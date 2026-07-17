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

Việc tester phải làm TRƯỚC khi /qa-kit:design:
1. config/env.yaml     -> điền base_url, db host TEST env
2. docs/               -> comtor bỏ spec/DD (bản VI) vào
3. db/                 -> xin dev DDL + ERD  ← nguồn boundary tin cậy nhất
4. context/project-glossary.md -> điền thuật ngữ domain

Kiểm tra: git init && git add . && git commit -m "chore: init qa"
```

Rồi DỪNG. Không tự chạy `/qa-kit:design`.

## Cấm

- Ghi đè file đã tồn tại (dự án đã init rồi -> báo, đừng phá)
- Tự điền `config/env.yaml` bằng giá trị đoán
- Tự `git init`
