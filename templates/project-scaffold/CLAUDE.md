# qa-kit — Test design + execution cho QC

Dự án: **<PROJECT_NAME>** — `/qa-init` điền.

**Chuẩn:** ISTQB/JSTQB (từ vựng + khung phase) + VSTeP (テスト観点).
Ba chỗ cố ý lệch chuẩn, có lý do: `${CLAUDE_PLUGIN_ROOT}/context/standards-mapping.md`.
Nói với khách bằng thuật ngữ JSTQB (開始基準/終了基準/静的テスト), không bằng từ tự chế.

## Đường dẫn

| | |
|---|---|
| Kit (read-only, đến từ plugin) | `${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md` |
| | `${CLAUDE_PLUGIN_ROOT}/context/conventions.md` |
| | `${CLAUDE_PLUGIN_ROOT}/schemas/*.yaml` |
| Dự án (đọc/ghi) | `./docs/` `./db/` `./testcases/` `./results/` |
| 観点 riêng dự án | `./context/viewpoints-local.md` |

Đọc **cả hai** file viewpoints. Local ghi đè chung khi trùng ID.
Cấm sửa file trong `${CLAUDE_PLUGIN_ROOT}` — update plugin sẽ ghi đè mất.

QC viết test case dựa trên **spec / DD / DB definition** (không phải từ source code, không phải UT).
Bộ kit: generate test case -> chạy -> đánh giá -> human review.

## Ngôn ngữ

**Tiếng Việt 100%.** Comtor dịch spec/DD sang VI TRƯỚC khi vào `docs/`.
Tiếng Nhật ngoài scope.

Ngoại lệ 1 điểm: boundary (`viewpoint: DATA-01`) BẮT BUỘC có `evidence.operator`
tường minh (`>=` / `>`), vì văn xuôi VI không phân biệt được. Không rõ -> hỏi comtor,
KHÔNG suy diễn.

## Nguyên tắc bất di bất dịch

1. **Cấu trúc test case bám business flow, KHÔNG bám mục lục DD.**
   DD là nguyên liệu điền expected/boundary, không phải khung sườn.
2. **Cấm đọc source code.** Được đọc: spec, DD, DB definition (DDL/ERD), message list.
   Không có thì hỏi, KHÔNG suy đoán từ "thường thì hệ thống sẽ...".
3. **Condition được vượt ngoài doc. Expected thì KHÔNG.**
   Không có căn cứ -> gap-report.
4. **`evidence` là IMMUTABLE.** Xem mục Loop.
5. **YAML là source of truth. Excel là build artifact.** Không ai sửa Excel.
6. **Coverage = spec coverage.** Cấm ước lượng C0/C1 (không có source).

## DB — hai vai, đừng lẫn

| | Đọc gì | Quyền |
|---|---|---|
| Design time | DB *definition*: DDL, ERD, constraint, nullable | read |
| Run time | DB *test env*: verify actual sau khi thao tác | **read-only, TEST ENV** |

Cấm tuyệt đối: ghi DB, đụng prod, đụng data khách hàng.

## Loop = TEST CYCLE, không phải auto-fix

**QC không sửa code. Kit này không sửa gì cả.** Kit chạy test, phân loại, báo cáo.
Sửa là việc của dev.

```
Round N: run -> kết quả -> triage -> báo cáo
                                        |
                             dev fix -> build mới
                                        |
Round N+1: retest_failed + REGRESSION -> ...
                                        |
                             exit criteria đạt -> dừng
```

### Kết quả gắn với (round, build_version)

Test case bất biến. Kết quả thì không. Thiếu 2 field này -> không trả lời được
"case này pass ở build nào?" = câu khách hỏi nhiều nhất.

### Triage = ROUTING, không phải fixing

| Loại | Gửi ai |
|---|---|
| A_bug | Dev |
| B_testcase | QC lead |
| C_script | Automation engineer |
| D_env | QC/Infra |
| E_spec | BrSE -> khách |

**Không chắc -> A_bug.** Báo nhầm bug tốn 30 phút của dev; giấu bug thật tốn cả release.

**CẤM sửa `expected` cho khớp `actual`.** `evidence` immutable — muốn đổi expected
phải đổi evidence, evidence trích từ docs/, docs không đổi -> không đổi được.

### Retest scope round N+1 ≠ "case fail"

Phải có nhóm `regression`: case đang PASS nhưng nằm vùng ảnh hưởng của fix.
**Fix của dev có thể phá chỗ khác.** Thiếu nhóm này = round vô nghĩa.

Vùng ảnh hưởng: dev khai 影響範囲 (ưu tiên) hoặc suy từ trace + category.large.
Không có thông tin -> chọn scope RỘNG, ghi rõ lý do.

### blocked ≠ fail

blocked = chưa test được (bug khác chặn). Nhiều blocked + pass rate cao
= **báo cáo lạc quan giả**. Luôn báo 2 số cùng nhau.

## Pipeline

/qa-kit:qa-design <module>        -> testcases/<m>.yaml + gap + coverage -> HUMAN REVIEW
/qa-kit:qa-run <module>           -> results/<m>-r<N>.yaml  (gắn build_version)
/qa-kit:qa-eval <module>          -> triage -> routing (KHÔNG sửa gì)
/qa-kit:qa-report <module>        -> reports/  (regression lên đầu)
/qa-kit:qa-retest <module> <build>-> scope round N+1 -> HUMAN REVIEW -> /qa-kit:qa-run

## Cấm

- Sửa expected cho khớp actual
- Sửa code sản phẩm (không phải việc của QC, không phải việc của kit)
- Ghi DB, đụng prod
- Sinh Excel trực tiếp (tools/export_excel.py lo)
- Bịa message lỗi khi message list không có
- Retest chỉ case fail, bỏ regression
- Báo pass rate mà giấu số blocked
- Kết luận "OK release" khi bug chưa hội tụ
