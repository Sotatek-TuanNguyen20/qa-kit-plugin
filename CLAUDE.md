# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`qa-kit` is a **Claude Code plugin**, not an application. It ships slash commands, skills,
schemas, and a project template that let a QC/tester generate test cases from specs/DD/DB
definitions, run them, triage failures, and report results — following ISTQB/JSTQB vocabulary
plus VSTeP test viewpoints (テスト観点). Most of the repo has no runtime code, no build, and no
test framework: nearly every artifact here is a markdown prompt (`commands/*.md`,
`skills/*/SKILL.md`) or a YAML schema/fixture that Claude reads and follows at conversation time.
The one exception is `tools/export_excel.py`, a real Python script with tests under `tests/` and
a `pyproject.toml` (uv-managed); run its tests with `uv run pytest`.

Read `README.md` (Vietnamese) / `README-EN.md` (English) for the product pitch; this file is
about how to work *inside* this repo.

## Plugin ↔ consumer-project boundary (read this before editing anything)

This repo is the **plugin** side only. A separate "project repo" is scaffolded per QC project by
running `/qa-kit:init` there, which copies `templates/project-scaffold/` into the target repo (its
own `CLAUDE.md`, `.claude/settings.json`, `context/`, `docs/`, `testcases/`, etc.).

| Lives here (plugin, read-only from a project's POV) | Lives in the scaffolded project repo |
|---|---|
| `commands/`, `skills/`, `schemas/`, `tools/` | `docs/`, `db/`, `testcases/`, `results/`, `reports/`, `work/` |
| `context/viewpoints.md` (shared, versioned, PR-only) | `context/viewpoints-local.md` (project-specific) |
| `context/conventions.md`, `context/standards-mapping.md` | `context/project-glossary.md`, `config/env.yaml` |
| `templates/project-scaffold/CLAUDE.md` (template) | `CLAUDE.md` (generated, `<PROJECT_NAME>` substituted) |

Commands/skills reference the plugin's own files via `${CLAUDE_PLUGIN_ROOT}` and the project's
files via relative paths (`./docs/`, `./testcases/`) — never hardcode an absolute path, since the
plugin installs into a per-machine cache directory.

When you change `context/viewpoints.md` or `context/conventions.md`, remember every consuming
project reads these two files (project-local overrides win on ID collision) — treat them as a
versioned public API. `templates/project-scaffold/CLAUDE.md` is a *template*: it must keep the
`<PROJECT_NAME>` placeholder literal; only `/qa-kit:init` (see `commands/init.md`) substitutes it
into a real project.

## The pipeline

Five top-level commands map to ISTQB test-process phases (`context/standards-mapping.md` has the
full mapping table):

```
/qa-kit:init <project>              scaffold a new QC project (run once)
/qa-kit:design <module>             analysis + design → testcases/<m>.yaml   [chain below]
/qa-kit:run <module> --build=<v>    execution → results/<m>-r<N>.yaml
/qa-kit:eval <module>               triage fail → routing (A_bug..E_spec), edits nothing else
/qa-kit:report <module>             read-only summary, regression-first
/qa-kit:retest <module> <build>     computes next round's scope, doesn't run anything
```

`/qa-kit:design` itself is a 6-step chain (see `commands/design.md`); each step writes an
intermediate artifact so a human can review the diff:

```
1. scenario-map     -> work/$1/scenarios.yaml   [not implemented yet — no skills/scenario-map/]
2. viewpoint-apply  -> work/$1/conditions.yaml  [not implemented yet]
3. detail-fill      -> work/$1/details.yaml     [not implemented yet]
4. testcase-generate-> testcases/$1.yaml        skills/testcase-generate/SKILL.md
5. gap-report       -> reports/$1-gap.md        skills/gap-report/SKILL.md
6. coverage-check   -> reports/$1-coverage.md   skills/coverage-check/SKILL.md
```

Steps 1–3 are referenced by `commands/design.md` but their `SKILL.md` files don't exist yet —
check `skills/` before assuming a step is implemented. In `tools/`, `export_excel.py` is now
implemented (with tests in `tests/test_export_excel.py`); `harness.py` and `validate.py` are
still empty, so `/qa-kit:run`'s automation branch is unimplemented. Check the status table in
`README.md` before assuming a command/skill/tool exists.

Machine gates inside `/qa-kit:design` stop the chain automatically (not a human prompt) when,
e.g., >20% of conditions have no evidence, or a `DATA-01` boundary case is missing
`evidence.operator` — see `commands/design.md` for the exact thresholds. Gates raise a gap, they
never fabricate a workaround.

## Core data model (the schemas are the contract)

- `schemas/testcase.schema.yaml` — one test case. `condition_vi`/`viewpoint` may go beyond the
  source doc (tester's judgment call); `expected_vi` may **not** — it must be traceable to
  `evidence.quote`, a verbatim excerpt from `docs/`. If no evidence exists, the skill must stop
  and log a gap instead of inventing an expected result — see the "Immutable evidence" guardrail
  in `skills/testcase-generate/SKILL.md`.
- `schemas/result.schema.yaml` — one round's run against one `build_version`. `status` has 5
  non-interchangeable values (`pass/fail/blocked/skipped/not_run`) — `blocked` (something else is
  blocking execution) is never folded into `fail` or `skipped`. `prev_status: pass` +
  `status: fail` = regression, always highest priority.
- `work/$1/gaps.yaml` (project-side, accumulator pattern) — skills along the design chain append
  gap entries as they find missing/contradictory evidence; `gap-report` only reads, groups by
  `severity`, and renders — it never re-detects or recomputes severity. The floor table for
  computing `severity` from `gap_type` lives in `skills/gap-report/SKILL.md` and is the single
  source of truth other skills must follow when appending.

## Two-tier viewpoints (テスト観点)

`context/viewpoints.md` is "the brain of the kit" — without it, test cases default to mirroring
the doc's own structure (a developer's view, not a tester's). Categories: `BIZ/USER/DATA/TIMING/
ENV/IMPACT-NN`. Every project also has its own `context/viewpoints-local.md`; a local viewpoint
that catches a real bug ≥2 times should be promoted into the plugin's shared file via PR — that's
how the kit's shared knowledge accumulates. Don't add a "function/API/screen" category here; that
axis is explicitly rejected (`context/viewpoints.md` top-of-file note).

## Five non-negotiable rules (apply to every command/skill you touch)

1. Test **condition**/viewpoint may exceed the doc; **expected** may never — cite evidence or gap it.
2. `evidence` is immutable — this is what stops an agent from editing `expected_vi` to match a
   failing `actual` during `/qa-kit:eval` (the "self-cheat" failure mode this schema exists to block).
3. Unsure why a test failed → default to `A_bug`, never "bad test case" — the cost asymmetry
   favors over-reporting bugs (see `skills/test-triage/SKILL.md`'s decision tree and trap table).
4. Retest scope must include a `regression` group (cases currently passing but in the fix's blast
   radius), not just re-running failed cases — see `commands/retest.md`.
5. `blocked` ≠ `fail`. High pass rate with many blocked cases is false optimism; always report both.

## Working in this repo (no build/lint/test — verify by fixture)

There is no compiler or test runner. The verification pattern used throughout this repo's history
(see `docs/superpowers/plans/*.md`) is:

1. Write/edit a `SKILL.md` or `commands/*.md`.
2. Re-read it fresh (as if you were a new executor with no memory of writing it) against
   `dev-fixtures/login-project/` (a small fake project with `docs/`, `testcases/`, `work/`).
3. Actually perform the steps by hand and write the output into
   `dev-fixtures/login-project/reports/` or `work/`.
4. Diff the output against the expected result spelled out in the corresponding plan doc; if it
   doesn't match, the instructions were ambiguous — fix the `SKILL.md` wording, not the fixture,
   and repeat until they agree.
5. Commit skill + regenerated fixture output together.

When adding a new skill/command, follow the same discipline: a spec doc under
`docs/superpowers/specs/`, a task-by-task plan under `docs/superpowers/plans/` (this repo uses the
`superpowers:writing-plans` / `superpowers:executing-plans` skills for that), then implement and
verify against a fixture before committing.

## Content conventions

- All tester-facing content (`condition_vi`, `expected_vi`, category names, report prose) is
  **100% Vietnamese** — `docs/` in a consuming project is assumed to already be comtor-translated
  from JA/EN. Japanese terminology only appears as parenthetical ISTQB/JSTQB cross-references.
  This repo's own internal skill/command files follow the same convention.
  Because reviewers may not read Vietnamese fluently, prefer editing existing VI wording over
  introducing new phrasing, and keep changes minimal/localized so a diff stays reviewable.
- `category.large/medium/small` (大/中/小項目) must follow **business flow**, never mirror the
  doc's own heading numbering — `context/conventions.md` has the self-check ("if these 3 fields
  could be copy-pasted from the DD's table of contents, it's wrong").
- Every report template has a `Generated by` field that must always be left blank for a human to
  fill in during review — never auto-populate it from git config or any other source.
- ID formats are fixed by schema: test case IDs `^(ST|IT)-[A-Z0-9]+-[0-9]{3}$`, `trace` entries
  `^(BD|DD)-[0-9]+(\.[0-9]+)*$`, viewpoint IDs `^(BIZ|USER|DATA|TIMING|ENV|IMPACT)-[0-9]{2}$`.
