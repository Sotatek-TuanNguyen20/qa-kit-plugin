# System Profile + `/qa-kit:ready` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize `qa-kit-plugin` beyond its web-app+DB assumption — `/qa-kit:init` asks
5 questions (system type, DB, config-file, seed-data ownership, environment isolation),
records them as a "System Profile" in the project's `CLAUDE.md`, extends 2 schema enums for
CLI/daemon systems, routes `commands/run.md`'s AUTO branch by verify-method family, and adds
a new `/qa-kit:ready` command that reads the System Profile + a module's generated test cases
to produce a pre-run readiness checklist.

**Architecture:** Pure markdown-prompt-file changes (no runtime code) — this repo's own
convention: verify by re-reading each file fresh as a new executor and running it against a
`dev-fixtures/` project by hand, not by unit tests. One exception: schema enum values are
checked with a small throwaway PyYAML script (parseable, no external test framework needed).

**Tech Stack:** Markdown (`commands/*.md`, `skills/*/SKILL.md`), YAML (`schemas/*.yaml`,
fixture files), Python + PyYAML (verification scripts only, not shipped).

## Global Constraints

- Spec of record: `docs/superpowers/specs/2026-07-21-system-profile-and-ready-design.md`.
  Every task's requirements implicitly include this spec's rules.
- 100% Vietnamese in all VI-facing prose (this repo's own convention, see its `CLAUDE.md`).
- `/qa-kit:ready` is a checklist, not automation — it never SSHes, never creates files,
  never checks a real server's state. It only reads `CLAUDE.md`'s System Profile +
  `testcases/$1.yaml` and renders a report.
- `steps[].data` is the ONLY source `/qa-kit:ready` uses to determine what resources are
  needed — `precondition_vi`/`action_vi` prose is context-only, never a suggestion source.
- Câu 4/5 answers of "chưa xác định" / "dùng chung, không có cơ chế cô lập" are never a
  block on `/qa-kit:init` completing — they're recorded as an explicit, visible risk.
- `forbidden_patterns` in `config/env.yaml` must survive in EVERY system-type variant,
  unchanged in content (`[prod, production, live, honban, 本番]`) — this is the hard safety
  gate `commands/run.md` depends on to refuse running against production.
- `/qa-kit:data` as a separate command was explicitly rejected during brainstorming — do not
  reintroduce it. Its concerns are folded into `/qa-kit:ready`.
- Evidence priority table lives in `skills/detail-fill/SKILL.md` (not `testcase-generate`) —
  this is a correction versus the original 2026-07-17 spec, which predates the
  `design-chain-skills` plan that moved all evidence-finding to `detail-fill`.
- No new Python tool/dependency — `tools/` stays limited to `export_excel.py`. Verification
  scripts for this plan are throwaway (write, run, discard — not committed).

---

## Task 1: Extend `schemas/testcase.schema.yaml` — 2 new enums

**Files:**
- Modify: `schemas/testcase.schema.yaml`

**Interfaces:**
- Produces: `evidence.source_type` enum gains `config_definition`, `fixed_format`,
  `log_format` (alongside existing `spec, dd, db_definition, message_list, screen_item`).
  `verify.method` enum gains `cli_exit_code`, `cli_output`, `file_exists`, `file_content`,
  `log_grep` (alongside existing `ui_text, ui_visible, http_status, http_body, db_query`).
  Tasks 2, 4, 5, 6 all reference these exact new enum value names — do not rename.

- [ ] **Step 1: Read the current file fresh**

Read `schemas/testcase.schema.yaml` in full before editing (don't guess at current
formatting).

- [ ] **Step 2: Extend `evidence.source_type` enum**

Find:
```yaml
      source_type:
        type: string
        enum: [spec, dd, db_definition, message_list, screen_item]
        description: "db_definition = từ DDL/ERD. Nguồn tin cậy cao cho boundary."
```

Replace with:
```yaml
      source_type:
        type: string
        enum: [spec, dd, db_definition, message_list, screen_item, config_definition, fixed_format, log_format]
        description: >
          db_definition = từ DDL/ERD (web/DB). config_definition/fixed_format/log_format =
          tương đương cho hệ CLI/backend không DB — xem CLAUDE.md dự án, mục "System
          Profile", để biết cột nào (web hay CLI/backend) áp dụng.
```

- [ ] **Step 3: Extend `verify.method` enum**

Find:
```yaml
        method:
          type: string
          enum: [ui_text, ui_visible, http_status, http_body, db_query]
```

Replace with:
```yaml
        method:
          type: string
          enum: [ui_text, ui_visible, http_status, http_body, db_query, cli_exit_code, cli_output, file_exists, file_content, log_grep]
```

- [ ] **Step 4: Verify with a throwaway script**

Run this inline (don't save the script file):

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
python3 -c "
import yaml
schema = yaml.safe_load(open('schemas/testcase.schema.yaml'))
source_type_enum = schema['properties']['evidence']['properties']['source_type']['enum']
verify_method_enum = schema['properties']['verify']['items']['properties']['method']['enum']
expected_source = ['spec','dd','db_definition','message_list','screen_item','config_definition','fixed_format','log_format']
expected_verify = ['ui_text','ui_visible','http_status','http_body','db_query','cli_exit_code','cli_output','file_exists','file_content','log_grep']
assert source_type_enum == expected_source, source_type_enum
assert verify_method_enum == expected_verify, verify_method_enum
assert len(source_type_enum) == len(set(source_type_enum)), 'duplicate in source_type enum'
assert len(verify_method_enum) == len(set(verify_method_enum)), 'duplicate in verify.method enum'
print('OK: both enums extended correctly, no duplicates')
"
```

Expected output: `OK: both enums extended correctly, no duplicates`

- [ ] **Step 5: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add schemas/testcase.schema.yaml
git commit -m "Extend evidence.source_type and verify.method enums for CLI/daemon systems"
```

---

## Task 2: Update evidence-priority table for CLI/daemon (`detail-fill` + `testcase-generate` reference copy)

**Files:**
- Modify: `skills/detail-fill/SKILL.md`
- Modify: `skills/testcase-generate/SKILL.md`

**Interfaces:**
- Consumes: the 3 new `evidence.source_type` values from Task 1 (`config_definition`,
  `fixed_format`, `log_format`).
- Consumes: `CLAUDE.md`'s "System Profile" section, specifically the "Loại hệ thống" line
  (produced by Task 3) — this task only writes the RULE that reads it; Task 3 is what
  actually produces that line in a real project.

- [ ] **Step 1: Read both files fresh**

Read `skills/detail-fill/SKILL.md` and `skills/testcase-generate/SKILL.md` in full before
editing.

- [ ] **Step 2: Replace `detail-fill/SKILL.md`'s "Bảng ưu tiên nguồn evidence" section**

Find:
```markdown
## Bảng ưu tiên nguồn evidence

Tái dùng đúng bảng gốc (web-app) đã có trong `context/standards-mapping.md` +
`skills/testcase-generate/SKILL.md` — KHÔNG dùng bảng tổng quát hoá CLI/daemon (spec
`docs/superpowers/specs/2026-07-17-non-web-system-support-design.md` chưa triển khai,
phạm vi rộng hơn riêng skill này, để dành nâng cấp sau):

```
db_definition > screen_item > message_list > dd > spec
```

Mâu thuẫn giữa 2 nguồn (vd DDL nói khác văn xuôi) → KHÔNG tự chọn bên nào, đó là gap
(`gap_type: contradiction`).
```

Replace with:
```markdown
## Bảng ưu tiên nguồn evidence

Tổ chức theo 5 tầng tin cậy, mỗi tầng có 2 lựa chọn tương đương (web app / CLI-backend).
Đọc `CLAUDE.md`'s mục "System Profile" (dòng "Loại hệ thống") để biết CỘT nào áp dụng cho
dự án đang làm — chỉ dùng ĐÚNG 1 cột cho cả module, không trộn 2 cột trong cùng 1 case:

| Tầng | Web app | CLI/backend |
|---|---|---|
| 1 — cao nhất | `db_definition` (DDL/ERD) | `config_definition` (config file sản phẩm) |
| 2 | `screen_item` (màn hình) | `fixed_format` (định dạng file/protocol cố định) |
| 3 | `message_list` (catalog lỗi) | `log_format` (định dạng log/mail alert) |
| 4 | `dd` (văn xuôi DD) | dùng chung |
| 5 — thấp nhất | `spec` (văn xuôi spec) | dùng chung |

`Loại hệ thống` = `web`/`api-only` → dùng cột Web app. `cli-daemon` → dùng cột CLI/backend.
`mobile app`/`khác` → chưa có cột riêng, dùng cột Web app tạm, ghi rõ trong `evidence.note_vi`
là tạm dùng do chưa có tầng riêng cho loại hệ thống này.

Mâu thuẫn giữa 2 nguồn (vd DDL nói khác văn xuôi) → KHÔNG tự chọn bên nào, đó là gap
(`gap_type: contradiction`).
```

- [ ] **Step 3: Update `testcase-generate/SKILL.md`'s reference copy of the same table**

Find:
```markdown
### Nguồn expected, theo thứ tự tin cậy (tham khảo — `detail-fill` là nơi áp dụng)

Bảng dưới đây là thứ tự ưu tiên nguồn evidence mà `detail-fill` đã áp dụng khi
điền `evidence.source_type` vào `details.yaml`. Giữ lại làm tài liệu tham chiếu để
hiểu vì sao một `source_type` được ưu tiên hơn cái khác khi đọc case đã sinh —
skill này KHÔNG tự đi tìm hay tự so sánh lại nguồn, chỉ đọc `source_type` đã có
sẵn:

1. **DB definition (DDL/ERD)** ← tin cậy nhất. `VARCHAR(32) NOT NULL` là fact,
   không qua tay dịch, không cãi được.
2. **Screen item definition** → max length, format, required, default
3. **Message list** → message ID + nội dung lỗi chính xác
4. **API spec** → param range, response code
5. **Văn xuôi DD/spec** ← ưu tiên **thấp nhất**, mơ hồ nhất, qua tay dịch nhiều nhất

Mâu thuẫn giữa DDL và văn xuôi, hoặc thiếu nguồn 1–3, đã được `detail-fill` xử lý
thành gap (`evidence_found: false` + `gap_id`) trước khi entry tới được bước này —
gặp entry như vậy thì bỏ qua theo Quy trình bước 2, không tự đánh giá lại xem
nguồn nào đáng tin hơn.
```

Replace with:
```markdown
### Nguồn expected, theo thứ tự tin cậy (tham khảo — `detail-fill` là nơi áp dụng)

Bảng dưới đây là bảng 5 tầng mà `detail-fill` đã áp dụng khi điền `evidence.source_type`
vào `details.yaml` (mỗi tầng có 2 lựa chọn tương đương — web app / CLI-backend, dùng đúng
1 cột theo `CLAUDE.md`'s System Profile). Giữ lại làm tài liệu tham chiếu để hiểu vì sao
một `source_type` được ưu tiên hơn cái khác khi đọc case đã sinh — skill này KHÔNG tự đi
tìm hay tự so sánh lại nguồn, chỉ đọc `source_type` đã có sẵn:

1. **DB definition (DDL/ERD)** hoặc **Config definition** (CLI/backend) ← tin cậy nhất.
   Fact từ artifact sản phẩm, không qua tay dịch, không cãi được.
2. **Screen item definition** hoặc **Fixed format** (định dạng file/protocol cố định,
   CLI/backend) → max length, format, required, default
3. **Message list** hoặc **Log format** (định dạng log/mail alert, CLI/backend) →
   message ID + nội dung lỗi chính xác
4. **DD văn xuôi** — dùng chung cho cả 2 loại hệ thống
5. **Spec văn xuôi** ← ưu tiên **thấp nhất**, mơ hồ nhất, qua tay dịch nhiều nhất — dùng
   chung cho cả 2 loại hệ thống

Mâu thuẫn giữa 2 nguồn, hoặc thiếu nguồn tầng 1–3, đã được `detail-fill` xử lý thành gap
(`evidence_found: false` + `gap_id`) trước khi entry tới được bước này — gặp entry như vậy
thì bỏ qua theo Quy trình bước 2, không tự đánh giá lại xem nguồn nào đáng tin hơn.
```

- [ ] **Step 4: Grep for other stale references to the old 1-tier priority string**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
grep -rn "db_definition > screen_item > message_list > dd > spec" --include="*.md" .
```

Expected: no output (both known occurrences were just replaced). If there IS output in a
file other than the 2 just edited, read that file's surrounding context and apply the same
5-tier replacement there too, matching the exact table format used in Step 2.

- [ ] **Step 5: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add skills/detail-fill/SKILL.md skills/testcase-generate/SKILL.md
git commit -m "Extend evidence-priority table to 5-tier web/CLI-backend structure"
```

---

## Task 3: Rewrite `commands/init.md` — 5-question System Profile flow

**Files:**
- Modify: `commands/init.md`

**Interfaces:**
- Consumes: `evidence.source_type`/`verify.method` enum values from Task 1 (referenced in
  the verify-method suggestion table this task writes).
- Produces: the exact "System Profile" block shape in a project's `CLAUDE.md` (6 lines:
  `Loại hệ thống`, `Database`, `Nguồn boundary ưu tiên #1`, `Bộ verify.method gợi ý`,
  `Nguồn seed/test data`, `Môi trường`) — Task 5 (`/qa-kit:ready`) parses these exact 6
  labels, so keep them byte-identical to what's written here. Produces 3 `config/env.yaml`
  variants (web/api-only, cli-daemon, mobile/khác) — Task 4 (`run.md`) and Task 6 (fixture)
  both depend on `forbidden_patterns` surviving unchanged in all 3.

- [ ] **Step 1: Read the current file fresh**

Read `commands/init.md` in full before editing.

- [ ] **Step 2: Insert the 5-question step before the copy step**

Find:
```markdown
## Việc

Copy từ `${CLAUDE_PLUGIN_ROOT}/templates/project-scaffold/` vào thư mục hiện tại:
```

Replace with:
```markdown
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

- [ ] **Step 3: Renumber the placeholder-substitution paragraph and insert Bước 3/4**

Find:
```markdown
Sau khi copy, thay TOÀN BỘ placeholder `<PROJECT_NAME>` trong `CLAUDE.md` và
`context/project-glossary.md` bằng tên dự án thật (`$1`). Copy nguyên văn mà
không thay là bug — 2 file đó sẽ còn nguyên literal `<PROJECT_NAME>`, vô nghĩa
với người đọc sau này.

## Hai tầng viewpoints
```

Replace with:
```markdown
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
```

- [ ] **Step 4: Update the "Sau khi chạy — báo tester" checklist**

Find:
```markdown
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
```

Replace with:
```markdown
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
```

- [ ] **Step 5: Update the "Cấm" section**

Find:
```markdown
## Cấm

- Ghi đè file đã tồn tại (dự án đã init rồi -> báo, đừng phá)
- Tự điền `config/env.yaml` bằng giá trị đoán
- Tự `git init`
```

Replace with:
```markdown
## Cấm

- Ghi đè file đã tồn tại (dự án đã init rồi -> báo, đừng phá)
- Tự điền `config/env.yaml` bằng giá trị đoán (IP/host/service THẬT phải hỏi tester,
  không tự bịa — chỉ khung field theo loại hệ thống là được viết sẵn)
- Tự `git init`
- Bỏ qua 5 câu hỏi vì "tên project có vẻ đoán được loại hệ thống" — luôn hỏi đủ 5 câu
```

- [ ] **Step 6: Verify by dry-running the flow for 2 answer sets**

Read the fully-edited `commands/init.md` fresh (as a new executor). Trace through it by
hand twice:

1. Answers: `web`, có DB, (câu 3 skip), `QC tự tạo theo schema/format đã tài liệu hoá`,
   `Riêng — không ai khác dùng chung`. Confirm you'd produce: System Profile block with
   `Loại hệ thống: web`, `Database: có`, `Nguồn boundary ưu tiên #1: db_definition`,
   verify.method suggestion = the web row, `config/env.yaml` = the web/api-only variant
   (with the `db:` block kept since câu 2 = có).
2. Answers: `cli-daemon`, không DB, có config file riêng, `dev/BrSE cấp mẫu thật`,
   `Dùng chung, không có cơ chế cô lập`. Confirm you'd produce: System Profile block with
   `Nguồn boundary ưu tiên #1: config_definition`, verify.method suggestion = the
   cli-daemon row, `config/env.yaml` = the cli-daemon variant, and the "Môi trường" line
   reads `Dùng chung, không có cơ chế cô lập` verbatim (this exact string is what Task 5
   greps for to decide whether to print the risk warning).

Both traces must produce internally consistent output (no leftover web-only wording in the
cli-daemon trace, `forbidden_patterns` present unchanged in both).

- [ ] **Step 7: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add commands/init.md
git commit -m "Add 5-question System Profile flow to /qa-kit:init"
```

---

## Task 4: `commands/run.md` — AUTO routing by verify-method family + generalized prod guard

**Files:**
- Modify: `commands/run.md`

**Interfaces:**
- Consumes: `cli_exit_code`/`cli_output`/`file_exists`/`file_content`/`log_grep` enum
  values from Task 1. Consumes `config/env.yaml`'s `environments.test.*` field shape from
  Task 3 (both the web/api-only and cli-daemon variants).

- [ ] **Step 1: Read the current file fresh**

Read `commands/run.md` in full before editing.

- [ ] **Step 2: Generalize the prod-safety guard**

Find:
```markdown
## Tiền điều kiện — không đủ thì DỪNG

- `testcases/$1.yaml` đã qua human review (có commit, không phải working dir bẩn)
- Env target là **test env**. Đọc `config/env.yaml`.
  Host chứa `prod`/`production` -> **DỪNG NGAY**, không hỏi lại.
```

Replace with:
```markdown
## Tiền điều kiện — không đủ thì DỪNG

- `testcases/$1.yaml` đã qua human review (có commit, không phải working dir bẩn)
- Env target là **test env**. Đọc `config/env.yaml`.
  Quét TẤT CẢ giá trị string trong `environments.<target>` (không chỉ `base_url`/`db.host`
  — hệ CLI/daemon dùng field khác như `ssh_host`/`spool_root`/`external_mock_url`, xem
  `CLAUDE.md`'s System Profile để biết field nào project này dùng) đối chiếu
  `forbidden_patterns`. Khớp bất kỳ pattern nào -> **DỪNG NGAY**, không hỏi lại.
```

- [ ] **Step 3: Replace the AUTO branch with routing logic**

Find:
```markdown
## Nhánh AUTO (`automatable: true`)

1. Sinh script từ `steps[]` + `verify[]` -> `e2e/$1.spec.ts`
2. Chạy: `npx playwright test e2e/$1.spec.ts`
3. Ghi kết quả -> `results/$1-<run_id>.yaml`

Case thiếu `verify[]` -> KHÔNG tự chế cách verify. Chuyển sang nhánh manual, ghi lý do.
```

Replace with:
```markdown
## Nhánh AUTO (`automatable: true`)

Xem `verify[]` của case dùng họ `method` nào:

- **Toàn bộ `ui_*`/`http_*`/`db_query`** (web/API):
  1. Sinh script từ `steps[]` + `verify[]` -> `e2e/$1.spec.ts`
  2. Chạy: `npx playwright test e2e/$1.spec.ts`
  3. Ghi kết quả -> `results/$1-<run_id>.yaml`

- **Toàn bộ `cli_exit_code`/`cli_output`/`file_exists`/`file_content`/`log_grep`**
  (CLI-daemon):
  1. Sinh script từ `steps[]` + `verify[]` -> `e2e/$1.sh` (bash)
  2. Dùng field tương ứng trong `config/env.yaml` (`ssh_host`, `spool_root`, hoặc field
     khác đã khai báo ở đó) để SSH vào server test, chạy lệnh CLI, kiểm tra exit
     code/file/log đúng theo từng `verify[]` entry
  3. Script tự `exit 0` (pass toàn bộ) / `exit 1` (có ít nhất 1 verify fail)
  4. Chạy: `bash e2e/$1.sh`
  5. Ghi kết quả -> `results/$1-<run_id>.yaml`

- **Case trộn cả 2 họ trong cùng 1 `verify[]`** (vd 1 entry `ui_visible` + 1 entry
  `cli_exit_code` trong cùng 1 case): KHÔNG tự động hoá — chuyển nhánh MANUAL, ghi lý do
  "verify method trộn họ, chưa có cách auto-route an toàn".

Case thiếu `verify[]` -> KHÔNG tự chế cách verify. Chuyển sang nhánh manual, ghi lý do.
```

- [ ] **Step 4: Verify by hand-tracing 3 case shapes**

Read the fully-edited file fresh. Confirm your own routing decision for 3 hypothetical
cases:
1. `verify: [{method: ui_visible, ...}, {method: http_status, ...}]` → routes to Playwright
   branch (both `ui_*`/`http_*` family).
2. `verify: [{method: cli_exit_code, ...}, {method: log_grep, ...}]` → routes to bash/SSH
   branch.
3. `verify: [{method: ui_visible, ...}, {method: cli_exit_code, ...}]` → routes to MANUAL,
   reason "verify method trộn họ".

- [ ] **Step 5: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add commands/run.md
git commit -m "Route /qa-kit:run's AUTO branch by verify-method family, generalize prod guard"
```

---

## Task 5: New `/qa-kit:ready` command

**Files:**
- Create: `commands/ready.md`

**Interfaces:**
- Consumes: `CLAUDE.md`'s "System Profile" block (exact 6-label shape from Task 3) and
  `testcases/$1.yaml` (existing schema, unchanged by this plan).
- Produces: `reports/$1-ready.md`.

- [ ] **Step 1: Write `commands/ready.md`**

```markdown
---
description: Check môi trường + resource sẵn sàng trước khi /qa-kit:run. Đọc System Profile + testcases đã sinh. KHÔNG tự SSH, KHÔNG tự tạo file.
argument-hint: <module>
allowed-tools: Read, Write
---

# /qa-kit:ready $1

## Vì sao command này tồn tại

`testcase-generate` đã điền `steps[].data` cụ thể cho từng case, và thiếu evidence cho
data đã được `detail-fill` bắt thành gap ngay lúc design (`/qa-kit:design`). Còn 1 việc
chưa ai làm: **trước khi thực sự chạy `/qa-kit:run`, resource vật lý (file mẫu, service
mock, server) cần cho module này đã có sẵn tại chỗ chưa, và môi trường có rủi ro đụng
tester khác không.**

Đây KHÔNG phải command tự động hoá hạ tầng. `/qa-kit:ready` không tự SSH, không tự tạo
file, không tự kiểm tra trạng thái server thật — QC không tự động hoá infra (ranh giới đã
có sẵn của cả kit). Đây là 1 checklist tĩnh giúp tester tự soát trước khi chạy thật.

## Nguồn được đọc

- `CLAUDE.md` — mục "System Profile" (dòng "Nguồn seed/test data" và "Môi trường").
- `testcases/$1.yaml` — toàn bộ case của module.

**Cấm tuyệt đối:** tự SSH vào server, tự đọc file thật trên máy/server để kiểm tra tồn tại.

## Quy trình

1. Đọc `CLAUDE.md`'s mục "System Profile" — lấy đúng 2 dòng "Nguồn seed/test data" và
   "Môi trường". Không có mục "System Profile" (project init từ trước khi có cơ chế này)
   -> báo rõ, coi như cả 2 dòng đều "chưa xác định"/"chưa rõ cơ chế cô lập", không tự đoán.
2. Đọc `testcases/$1.yaml`, với mỗi case trích `steps[].data` (giá trị cụ thể cần
   nhập/dùng) — đây là NGUỒN DUY NHẤT xác định resource cần chuẩn bị. `precondition_vi`/
   `condition_vi`/`steps[].action_vi` chỉ đọc để lấy ngữ cảnh hiển thị trong report (vd
   tên service nhắc tới trong câu mô tả), KHÔNG dùng để tự suy luận resource cần chuẩn bị
   nếu `steps[].data` không có giá trị nào gợi ý — tránh đoán mò từ văn xuôi tự do.
3. Gom tất cả `steps[].data` values thành 1 danh sách "resource cần chuẩn bị" cho cả
   module — dedupe theo giá trị (nhiều case cùng cần 1 resource thì chỉ liệt kê 1 lần,
   kèm danh sách id case phụ thuộc).
4. Đối chiếu danh sách với dòng "Nguồn seed/test data":
   - = "chưa xác định" -> TOÀN BỘ danh sách đánh dấu "⚠️ CHƯA THỂ XÁC NHẬN — chưa rõ ai
     cấp data cho dự án này".
   - Khác "chưa xác định" -> liệt kê từng resource dưới dạng checklist tay
     (`- [ ] <giá trị> (cần cho N case: <id case>)`), tester tự tick sau khi xác nhận có
     sẵn.
5. Đối chiếu dòng "Môi trường":
   - Chứa "không có cơ chế cô lập" -> LUÔN in cảnh báo rủi ro ở đầu report, bất kể module
     nào, nhắc tester phối hợp lịch chạy với người khác đang dùng chung server/resource.
   - Chứa "có cơ chế cô lập" -> in 1 dòng nhắc lại đúng mô tả cơ chế đã khai báo trong
     System Profile.
   - = "Riêng — không ai khác dùng chung" -> không in gì thêm ở mục này.
6. Nếu có bất kỳ resource nào "⚠️ CHƯA THỂ XÁC NHẬN" -> dòng "Trạng thái" ở đầu report ghi
   "❌ CHƯA SẴN SÀNG — cần xác nhận nguồn data trước khi /qa-kit:run". Ngược lại ghi
   "✅ Sẵn sàng (đã đối chiếu System Profile)".
7. Ghi `reports/$1-ready.md`.

## `reports/$1-ready.md`

```markdown
# Ready Check — <module>

| Module | <module> |
|---|---|
| Generated at | <ISO 8601> |
| Generated by | |
| Trạng thái | <✅ Sẵn sàng | ❌ CHƯA SẴN SÀNG — cần xác nhận nguồn data trước khi /qa-kit:run> |

## ⚠️ Rủi ro môi trường
<chỉ xuất hiện nếu "Môi trường" chứa "không có cơ chế cô lập" hoặc "có cơ chế cô lập">

## Resource cần chuẩn bị
- [ ] <giá trị 1> (cần cho N case: <id1>, <id2>...)
- [ ] <giá trị 2> (cần cho N case: <id3>...)
<hoặc, nếu Nguồn seed/test data = "chưa xác định":>
⚠️ CHƯA THỂ XÁC NHẬN — chưa rõ ai cấp data cho dự án này (System Profile: "chưa xác định")
```

`Generated by` luôn để trống — con người tự điền tay lúc review, đúng convention đã có của
`gap-report`/`coverage-check`. Không có case nào trong `testcases/$1.yaml` -> báo "0 case,
không có gì để check", vẫn ghi report (không báo lỗi).

## Cấm

- Tự SSH vào server để kiểm tra file/resource có thật không.
- Tự tạo file/resource còn thiếu.
- Tự đoán resource cần chuẩn bị từ văn xuôi tự do (`precondition_vi`/`action_vi`) khi
  `steps[].data` không có gợi ý.
- Tự chặn `/qa-kit:run` chạy tiếp — chỉ in cảnh báo, tester tự quyết định có chạy hay không
  (khác `/qa-kit:design`'s machine gate, vốn tự động chặn được vì nằm trong cùng 1 chain).
- `Generated by` tự điền.

## Self-check trước khi ghi report

- [ ] Đã đọc đúng 2 dòng "Nguồn seed/test data"/"Môi trường" từ System Profile, không tự
      đoán khi thiếu mục này chưa?
- [ ] Resource cần chuẩn bị chỉ lấy từ `steps[].data`, không lẫn suy luận từ văn xuôi tự
      do chưa?
- [ ] Dedupe đúng — 1 resource dùng ở nhiều case chỉ xuất hiện 1 dòng, kèm đủ id case
      chưa?
- [ ] Trạng thái đầu report khớp đúng có resource "CHƯA THỂ XÁC NHẬN" nào không?
- [ ] Cảnh báo môi trường có in đúng khi "không có cơ chế cô lập" chưa?
- [ ] `Generated by` để trống chưa?
```

- [ ] **Step 2: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add commands/ready.md
git commit -m "Add /qa-kit:ready command"
```

---

## Task 6: New CLI-daemon dev-fixture + end-to-end sanity check

**Files:**
- Create: `dev-fixtures/roc-fixture/CLAUDE.md`
- Create: `dev-fixtures/roc-fixture/config/env.yaml`
- Create: `dev-fixtures/roc-fixture/testcases/send.yaml`
- Create: `dev-fixtures/roc-fixture/reports/send-ready.md`

**Interfaces:**
- Consumes: Task 1's enum values, Task 3's System Profile block shape + `config/env.yaml`
  cli-daemon variant, Task 5's `/qa-kit:ready` Quy trình.
- This task produces no interface other tasks depend on — it's the integration check that
  everything from Tasks 1–5 actually fits together on a realistic CLI-daemon example.

- [ ] **Step 1: Write `dev-fixtures/roc-fixture/CLAUDE.md`**

Simulate `/qa-kit:init`'s Task-3 output for a real CLI-daemon answer set (grounded in the
real ROC-PD-Gateway facts already known from `ROC-Test/test-case/*.html`: no DB, has its
own `config.yaml`, seed data = sample `.eml` files supplied by dev/BrSE, environment =
1 shared EC2 dev server with no isolation mechanism):

```markdown
# qa-kit — Test design + execution cho QC

Dự án: **roc-fixture** — `/qa-kit:init` điền.

## System Profile
- Loại hệ thống: cli-daemon
- Database: không
- Nguồn boundary ưu tiên #1: config_definition
- Bộ verify.method gợi ý: cli_exit_code, cli_output, file_exists, file_content, log_grep
- Nguồn seed/test data: dev/BrSE cấp mẫu thật
- Môi trường: Dùng chung, không có cơ chế cô lập

## Ngôn ngữ

Tiếng Việt 100%.
```

(Trimmed vs. a real project's `CLAUDE.md` — this fixture only needs the System Profile
block for `/qa-kit:ready` to read; it doesn't need the full 6-rule/loop content that a real
scaffolded project would have.)

- [ ] **Step 2: Write `dev-fixtures/roc-fixture/config/env.yaml`**

Exactly Task 3's cli-daemon variant, filled with plausible values:

```yaml
# harness đọc file này TRƯỚC KHI chạy bất cứ gì. Guard chống chạy nhầm prod.
target: test

environments:
  test:
    ssh_host: "ec2-user@dev-rocgw.internal"
    spool_root: "/var/spool/roc-pd"
    external_mock_url: "http://localhost:3000/v2/enqueue"
    systemd_services: [rocgw.service, rocgw-retry.timer, rocgw-stale.timer]

forbidden_patterns: [prod, production, live, honban, 本番]
```

- [ ] **Step 3: Write `dev-fixtures/roc-fixture/testcases/send.yaml`**

3 cases exercising CLI-daemon verify methods, one referencing a sample `.eml` file via
`steps[].data` (matching the real `Sample Data.html`/`Send.html` shape seen in
`ROC-Test/test-case/`):

```yaml
- id: IT-SEND-001
  trace: [DD-1]
  test_level: IT
  category:
    large: "Nghiệp vụ nhận và chuyển tiếp alert"
    medium: "Nhận mail Nagios và forward PagerDuty"
    small: "Body JSON chỉ chứa 4 field top-level"
  viewpoint: DATA-05
  precondition_vi:
    - "Gateway đã cài, daemon đang chạy"
    - "PagerDuty mock chạy, log request body"
  condition_vi: "Thả 1 mail Nagios hợp lệ vào maildir, kiểm tra body JSON gửi PagerDuty"
  steps:
    - action_vi: "Copy file mail mẫu vào maildir"
      data: { mail_file: "samples/nagios-trigger.eml" }
    - action_vi: "Chờ 3 giây cho daemon xử lý"
    - action_vi: "Xem log PagerDuty mock nhận request"
  expected_vi: "Body JSON chỉ có 4 field top-level: routing_key, event_action, dedup_key, payload."
  evidence:
    section: "config.yaml pd.payload_template"
    quote: "payload: { summary, severity, source, timestamp } — 4 field top-level cố định, không có field nội bộ Gateway"
    source_type: config_definition
  priority: P1
  automatable: true
  verify:
    - method: log_grep
      target: "pd-mock container log"
      expect: "POST /v2/enqueue với đúng 4 field top-level"

- id: IT-SEND-002
  trace: [DD-1]
  test_level: IT
  category:
    large: "Nghiệp vụ nhận và chuyển tiếp alert"
    medium: "Nhận mail Nagios và forward PagerDuty"
    small: "Mail parse fail — thiếu item_id"
  viewpoint: DATA-04
  precondition_vi:
    - "Gateway đã cài, daemon đang chạy"
  condition_vi: "Thả mail thiếu field bắt buộc, kiểm tra Gateway không crash và ghi log lỗi rõ ràng"
  steps:
    - action_vi: "Copy file mail mẫu (cố ý thiếu item_id) vào maildir"
      data: { mail_file: "samples/bad-no-itemid.eml" }
    - action_vi: "Kiểm tra exit code của lần xử lý qua log"
  expected_vi: "Daemon không crash (service vẫn active), log ghi rõ lý do parse fail (thiếu item_id)."
  evidence:
    section: "config.yaml parser.required_fields"
    quote: "required_fields: [tbl_kanshi_koumoku_id, detection_datetime, mst_alarm_rearm_id] — thiếu field nào trong danh sách này thì reject, không crash"
    source_type: config_definition
  priority: P1
  automatable: true
  verify:
    - method: cli_exit_code
      target: "systemctl is-active rocgw"
      expect: "active"
    - method: log_grep
      target: "journalctl -u rocgw"
      expect: "parse fail: missing tbl_kanshi_koumoku_id"

- id: IT-SEND-003
  trace: [DD-1]
  test_level: IT
  category:
    large: "Nghiệp vụ nhận và chuyển tiếp alert"
    medium: "Nhận mail Nagios và forward PagerDuty"
    small: "File mail đã xử lý được archive đúng thư mục"
  viewpoint: DATA-06
  precondition_vi:
    - "Gateway đã cài, daemon đang chạy"
  condition_vi: "Sau khi xử lý xong 1 mail hợp lệ, kiểm tra file gốc được di chuyển sang thư mục completed"
  steps:
    - action_vi: "Copy file mail mẫu vào maildir"
      data: { mail_file: "samples/nagios-trigger.eml" }
    - action_vi: "Chờ xử lý xong, kiểm tra thư mục completed"
  expected_vi: "File mail gốc không còn trong maildir/new, xuất hiện trong spool_root/completed/."
  evidence:
    section: "config.yaml spool.completed_dir"
    quote: "completed_dir: {spool_root}/completed — mail xử lý xong (thành công hoặc thất bại đều) được move vào đây, không xoá"
    source_type: config_definition
  priority: P2
  automatable: true
  verify:
    - method: file_exists
      target: "{spool_root}/completed/nagios-trigger.eml"
      expect: true
```

- [ ] **Step 4: Run `/qa-kit:ready` fresh against this fixture**

Read your just-written `commands/ready.md` (Task 5) fresh, as a new executor. Follow its
Quy trình by hand against `dev-fixtures/roc-fixture/`:

1. Read `dev-fixtures/roc-fixture/CLAUDE.md`'s System Profile — confirm you extract
   `Nguồn seed/test data: dev/BrSE cấp mẫu thật` and `Môi trường: Dùng chung, không có cơ
   chế cô lập`.
2. Read `dev-fixtures/roc-fixture/testcases/send.yaml` — extract `steps[].data` from all
   3 cases: `mail_file: samples/nagios-trigger.eml` (used by `IT-SEND-001` and
   `IT-SEND-003`), `mail_file: samples/bad-no-itemid.eml` (used by `IT-SEND-002`).
3. Dedupe: 2 distinct resources (`samples/nagios-trigger.eml` used by 2 cases,
   `samples/bad-no-itemid.eml` used by 1 case).
4. "Nguồn seed/test data" is NOT "chưa xác định" (it's "dev/BrSE cấp mẫu thật") -> both
   resources get a real checklist line, NOT the "⚠️ CHƯA THỂ XÁC NHẬN" marker.
5. "Môi trường" contains "không có cơ chế cô lập" -> the risk warning section MUST appear.
6. No unresolved resource -> "Trạng thái" = "✅ Sẵn sàng".
7. Write the resulting report to `dev-fixtures/roc-fixture/reports/send-ready.md`.

- [ ] **Step 5: Verify the report's properties programmatically**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
python3 -c "
report = open('dev-fixtures/roc-fixture/reports/send-ready.md').read()
assert '✅ Sẵn sàng' in report, 'expected ready status, no unresolved resources'
assert 'samples/nagios-trigger.eml' in report
assert 'samples/bad-no-itemid.eml' in report
assert 'IT-SEND-001' in report and 'IT-SEND-003' in report, 'nagios-trigger.eml checklist line must list both dependent cases'
assert 'CHƯA THỂ XÁC NHẬN' not in report, 'seed data source is defined, should not show this marker'
assert 'không có cơ chế cô lập' in report or 'Rủi ro' in report, 'shared-unisolated environment warning must appear'
assert report.count('samples/nagios-trigger.eml') <= 2, 'resource should be deduped to one checklist line (title + maybe one more mention), not one per case'
print('OK: all report properties verified')
"
```

Expected output: `OK: all report properties verified`. If any assertion fails, the mismatch
is between `commands/ready.md`'s wording (Task 5) and this trace — fix `commands/ready.md`'s
wording (not the fixture) until they agree, matching this repo's own established
verify-by-fixture discipline.

- [ ] **Step 6: Hand-trace `commands/run.md`'s AUTO routing for this fixture (no real execution)**

Read `commands/run.md` (Task 4) fresh. For each of the 3 cases in
`dev-fixtures/roc-fixture/testcases/send.yaml`, confirm the routing decision:
- `IT-SEND-001`: `verify: [log_grep]` → all CLI/daemon family → bash/SSH branch.
- `IT-SEND-002`: `verify: [cli_exit_code, log_grep]` → all CLI/daemon family → bash/SSH
  branch.
- `IT-SEND-003`: `verify: [file_exists]` → all CLI/daemon family → bash/SSH branch.

None of the 3 cases should route to Playwright or MANUAL (no `ui_*`/`http_*` methods
present, no mixed-family case). Do NOT actually SSH or run any script — this fixture has no
real server behind it; this step only confirms the ROUTING DECISION documented in
`commands/run.md` is unambiguous and correct for these 3 cases, matching how the rest of
this repo's `dev-fixtures/` verify skill logic by hand-tracing rather than executing
infrastructure.

- [ ] **Step 7: Commit**

```bash
cd /Users/TuanNA/Projects/Sotatek/ROC-PD-Gateway/ROC-Test/qa-kit-plugin
git add dev-fixtures/roc-fixture/
git commit -m "Add CLI-daemon dev-fixture, verify /qa-kit:ready + run.md routing end-to-end"
```

---

## Self-Review (đã chạy khi viết plan này)

**1. Spec coverage:** Spec's Phần 1 (5 câu hỏi + System Profile + `config/env.yaml` theo
loại) → Task 3. Phần 2 (2 enum) → Task 1, cộng Task 2 cho evidence-priority table áp dụng
đúng nơi (`detail-fill`, sửa từ chỗ spec cũ ghi nhầm là `testcase-generate`). Phần 3
(`run.md` routing) → Task 4. Phần 4 (`/qa-kit:ready`) → Task 5. Mục "Kiểm chứng khi
implement" (fixture CLI-daemon mới) → Task 6. Mục "Ảnh hưởng lên ROC-QC" trong spec là ghi
chú cho 1 project TIÊU DÙNG plugin này, nằm ngoài repo `qa-kit-plugin` — không có task
tương ứng trong plan này (đúng với nguyên tắc đã thống nhất trong phiên: sửa ở plugin dùng
chung, không sửa ở project riêng; migrate `ROC-QC` là việc riêng của người vận hành project
đó khi họ chọn làm, không phải phần của plan implement-cho-plugin này).

**2. Placeholder scan:** Không có "TBD"/"TODO" — mọi step có nội dung/code cụ thể, không
step nào chỉ mô tả suông "thêm xử lý phù hợp".

**3. Type/field consistency:** `evidence.source_type` enum values (`config_definition`,
`fixed_format`, `log_format`) dùng nhất quán giữa Task 1 (schema), Task 2 (bảng ưu tiên
trong `detail-fill`), Task 6 (fixture case dùng đúng `source_type: config_definition`).
`verify.method` values (`cli_exit_code`, `cli_output`, `file_exists`, `file_content`,
`log_grep`) dùng nhất quán giữa Task 1 (schema), Task 3 (bảng gợi ý theo System Profile),
Task 4 (routing logic), Task 6 (fixture cases dùng `log_grep`/`cli_exit_code`/
`file_exists`). System Profile's 6 label chính xác (`Loại hệ thống`/`Database`/`Nguồn
boundary ưu tiên #1`/`Bộ verify.method gợi ý`/`Nguồn seed/test data`/`Môi trường`) dùng
byte-giống nhau giữa Task 3 (nơi ghi) và Task 5 (nơi đọc lại) — Task 5's Quy trình bước 1
grep đúng 2 label "Nguồn seed/test data" và "Môi trường" Task 3 tạo ra, không lệch tên.
`forbidden_patterns` giữ nguyên giá trị `[prod, production, live, honban, 本番]` xuyên suốt
Task 3 (cả 3 variant) và Task 4 (nơi đọc lại để chặn prod).
