---
description: Sinh test case từ spec/DD/DB cho 1 module. Chạy liền mạch, dừng ở human review.
argument-hint: <module> [--step]
allowed-tools: Read, Write, Glob, Grep
---

# /qa-kit:design $1

Chạy full chain cho module **$1**. Artifact trung gian ghi ra file để review được,
nhưng KHÔNG hỏi tester giữa chừng — trừ khi machine gate bật.

## Chain

1. `scenario-map`     -> `work/$1/scenarios.yaml`   (actor, business flow, state)
2. `viewpoint-apply`  -> `work/$1/conditions.yaml`  (test condition, ĐƯỢC vượt doc)
3. `detail-fill`      -> `work/$1/details.yaml`     (boundary/data, PHẢI bám doc)
4. `testcase-generate`-> `testcases/$1.yaml`
5. `gap-report`       -> `reports/$1-gap.md`
6. `coverage-check`   -> `reports/$1-coverage.md`

## Machine gate — dừng ngay, KHÔNG generate tiếp

Không phải human gate. Máy tự chặn, không hỏi ý kiến:

- **>20% condition không tìm được evidence** -> DỪNG sau bước 3.
  Nghĩa là doc quá thiếu. Generate tiếp = sinh ra một đống case bịa.
  Xuất gap-report, báo tester: "DD chưa đủ để design, cần confirm N điểm."
- **Thiếu screen item definition HOẶC message list** -> DỪNG.
  Không có 2 cái này thì không có expected cho case normal/error. Báo BrSE.
- **viewpoint DATA-01 mà thiếu `evidence.operator`** -> DỪNG case đó, đẩy gap-report.
  Cấm đoán `>=` hay `>` từ văn xuôi VI.

Gate bật -> báo cụ thể thiếu gì ở đâu, KHÔNG đưa ra workaround, KHÔNG generate case
"tạm" để lấp chỗ.

## `--step`

Dừng sau mỗi bước, chờ tester duyệt. Dùng khi làm module đầu tiên hoặc khi
tỷ lệ merge-không-sửa của module này đang thấp.

## Kết thúc

In ra:
- Số case theo test_level / viewpoint
- Số gap (chia P1/P2/P3)
- Coverage: X/Y section đã có case trace tới
- **Danh sách section CHƯA có case nào** <- cái tester cần nhìn nhất

Rồi DỪNG. Human review `testcases/$1.yaml` trên Git diff.
KHÔNG tự chạy /qa-kit:run.

Test case merge vào main rồi mới được chạy. Test case còn trong working dir = chưa ai duyệt.
