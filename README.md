# qa-kit — Claude Code plugin cho QC

Sinh test case từ **spec / DD / DB definition** → chạy → triage → báo cáo.
Theo **ISTQB/JSTQB** (từ vựng, khung phase) + **VSTeP** (テスト観点).

Không đọc source code. Không phải UT. Không phải view của dev.

## Cài

```bash
/plugin marketplace add Sotatek-TuanNguyen20/qa-kit-plugin
/plugin install qa-kit@qa-internal
```

## Dùng

```bash
mkdir qa-project-a && cd qa-project-a
claude
> /qa-kit:init project-a          # scaffold 1 lần
# comtor bỏ doc vào docs/, xin dev DDL vào db/
> /qa-kit:design login            # → testcases/login.yaml + gap + coverage
# HUMAN REVIEW → merge
> /qa-kit:run login --build=v1.2.3
> /qa-kit:eval login              # triage → routing
> /qa-kit:report login
# dev fix
> /qa-kit:retest login v1.2.4     # scope = retest_failed + REGRESSION
```

## Ranh giới plugin ↔ dự án

|                                  | Plugin (read-only) | Repo dự án          |
| -------------------------------- | ------------------ | ------------------- |
| commands, skills, tools, schemas | ✅                 |                     |
| `context/viewpoints.md` (chung)  | ✅                 |                     |
| `context/conventions.md`         | ✅                 |                     |
| CLAUDE.md, .claude/settings.json | template           | ✅ `/qa-kit:init` sinh  |
| `context/viewpoints-local.md`    |                    | ✅ 観点 riêng dự án |
| docs/ db/ testcases/ results/    |                    | ✅                  |

**Plugin KHÔNG đóng gói được CLAUDE.md và settings.json** — đó là lý do `/qa-kit:init` tồn tại.
Bỏ qua `/qa-kit:init` = có command nhưng không có guardrail.

## Hai tầng viewpoints

```
${CLAUDE_PLUGIN_ROOT}/context/viewpoints.md   ← chung, mọi dự án, sửa qua PR
./context/viewpoints-local.md                 ← riêng dự án
```

観点 local bắt bug thật ≥2 lần → **PR promote lên plugin**. Mọi dự án hưởng.
Không promote = kinh nghiệm chết trong 1 dự án.

## 5 luật sống còn

1. **Condition được vượt ngoài doc. Expected thì không.**
2. **`evidence` immutable** — chặn sửa expected cho khớp actual.
3. **Không chắc nguyên nhân fail → mặc định BUG**, không phải "test sai".
4. **Retest ≠ case fail.** Phải có nhóm regression.
5. **blocked ≠ fail.** Pass rate cao + nhiều blocked = lạc quan giả.

## Metric

Tỷ lệ test case merge không sửa, theo module. <60% → bơm `viewpoints.md`,
**đừng** sửa prompt hay thêm skill.

## Trạng thái

| Phase (ISTQB)         | Command                   |     |
| --------------------- | ------------------------- | --- |
| —                     | `/qa-kit:init`                | ✅  |
| 3-4 Analysis + Design | `/qa-kit:design`              | ✅  |
| 5 Implementation      | `/qa-kit:ready` `/qa-kit:data`    | ⬜  |
| 6 Execution           | `/qa-kit:run` `/qa-kit:eval`      | ✅  |
| 2 Monitoring          | `/qa-kit:report` `/qa-kit:retest` | ✅  |
| 7 Completion          | `/qa-kit:complete`            | ⬜  |

Skills: `testcase-generate` ✅ `test-triage` ✅ `gap-report` ✅ `coverage-check` ✅ | `scenario-map` `viewpoint-apply` `detail-fill` ⬜

Tools: `export_excel.py` ✅ | `harness.py` `validate.py` ⬜

## Version

- Đổi schema → **major** (breaking, mọi dự án phải migrate)
- Thêm 観点 / skill → **minor**
- Sửa chữ → **patch**
