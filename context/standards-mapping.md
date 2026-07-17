# qa-kit ↔ Chuẩn ngành

> Mục đích: (1) người mới hiểu kit dựa trên gì, (2) trả lời khách khi hỏi
> "quy trình test theo chuẩn nào", (3) chặn drift — biết chỗ nào cố ý lệch chuẩn.

## Quyết định: chỉ apply ISTQB

| Chuẩn | Apply? | Lý do |
|---|---|---|
| **ISTQB / JSTQB** | ✅ Có | Từ vựng + khung phase. Khách Nhật tra JSTQB ra cùng khái niệm. |
| **VSTeP / NGT** (西康晴) | ✅ Một phần | Khái niệm テスト観点. ISTQB không có tương đương tốt. |
| IVEC (IVIA) | ❌ | Đo năng lực **con người**, không phải artifact. Dùng ngoài kit. |
| SQuBOK / JCSQE | ❌ | Tầng QA toàn tổ chức. Kit ở tầng QC. |
| ISO/IEC/IEEE 29119 | ❌ (1 ngoại lệ) | Chỉ test plan gửi khách — lead viết tay, ngoài kit. |

**Nguyên tắc:** chuẩn chỉ apply khi (a) tạo ngôn ngữ chung với khách, hoặc
(b) chặn được lỗi cụ thể. Apply để "trông chuyên nghiệp" = document theater.

## Map: qa-kit ↔ ISTQB test process

| # | ISTQB | JSTQB (gửi khách) | qa-kit | Trạng thái |
|---|---|---|---|---|
| 1 | Test planning | テスト計画 | — | Lead làm tay, ngoài kit |
| 2 | Test monitoring & control | テスト監視・コントロール | `/qa-kit:report` | ✅ |
| 3 | Test analysis | テスト分析 | `/qa-kit:design` b1–2 | ✅ |
| 4 | Test design | テスト設計 | `/qa-kit:design` b3–4 | ✅ |
| 5 | Test implementation | テスト実装 | `/qa-kit:ready` `/qa-kit:data` | ⚠️ **chưa làm** |
| 6 | Test execution | テスト実行 | `/qa-kit:run` `/qa-kit:eval` | ✅ |
| 7 | Test completion | テスト完了 | `/qa-kit:complete` | ⚠️ **chưa làm** |

## Từ vựng: qa-kit ↔ ISTQB ↔ JSTQB

| qa-kit | ISTQB | JSTQB | Ghi chú |
|---|---|---|---|
| `docs/`, `db/` | test basis | テストベース | Nguồn để thiết kế test |
| `evidence.quote` | — | — | **Riêng của kit.** Trích dẫn cụ thể trong test basis. |
| `condition_vi` | test condition | テスト条件 | |
| `viewpoint` | (không có) | テスト観点 | **VSTeP**, không phải ISTQB |
| `testcases/*.yaml` | test case | テストケース | |
| `steps[]` | test procedure | テスト手順 | Kit **cố ý gộp** vào test case |
| `trace` | traceability | トレーサビリティ | |
| `test_level: IT/ST` | integration / system testing | 結合テスト / システムテスト | |
| `results/*.yaml` | test results | テスト結果 | |
| `/qa-ready` checklist | entry criteria | 開始基準 | |
| exit criteria (conventions.md) | exit criteria | 終了基準 | |
| `status` 5 giá trị | pass/fail/blocked/skipped | 合格/不合格/ブロック/スキップ | ✅ đúng chuẩn |
| `build_version` | test object version | テスト対象バージョン | ISTQB đòi ghi bắt buộc |
| `gap-report` | **static testing findings** | **静的テストの検出欠陥** | Xem dưới |
| `A_bug` … `E_spec` | anomaly analysis | 異常の分析 | |

## gap-report = static testing

Đây là điểm quan trọng khi trình bày với khách.

`gap-report` không phải "AI tìm thấy chỗ spec thiếu" — nó là **静的テスト**: phát hiện
defect **trong test basis** trước khi code chạy. Hoạt động có tên chính thức trong ISTQB,
chương "Static testing".

Nói với khách: **「静的テストで検出した設計書の欠陥」**, không nói "AI phát hiện".
Câu trước đúng và khách nghiêm túc; câu sau nghe như đánh bóng công cụ.

Giá trị: defect bắt ở phase design rẻ hơn bắt ở UAT hàng chục lần. Đây là lập luận
ROI mạnh nhất của cả kit.

## Cố ý lệch chuẩn — 3 chỗ, có lý do

### 1. `viewpoint` — dùng VSTeP, không dùng ISTQB

ISTQB có "test technique" (boundary value, equivalence partition...) nhưng đó là
**kỹ thuật**, không phải **góc nhìn**. VSTeP/テスト観点 nắm được thứ ISTQB không nắm:
*trục tư duy của tester khác trục của dev*.

Tester Nhật và khách Nhật quen 観点. Ép ISTQB vào đây = mất ngôn ngữ chung, được lý thuyết.

### 2. Gộp test procedure vào test case

ISTQB tách case (điều kiện + expected) và procedure (trình tự thực thi).
Kit gộp vào `steps[]`.

Lý do: quy mô của team không cần tách. Tách ra = 2 artifact phải đồng bộ, gấp đôi
công bảo trì, không thêm giá trị. **Cố ý, không phải thiếu sót.**

Khi nào cần tách: nhiều test case dùng chung một trình tự dài.

### 3. `evidence` immutable — ISTQB không có

ISTQB viết cho **người**. Người không có xu hướng sửa expected cho khớp actual để
"cho xong việc" — model thì có.

`evidence` immutable là guardrail **riêng cho ngữ cảnh AI**: expected bị khóa bởi trích
dẫn từ test basis; test basis không đổi → expected không đổi được. Cùng field, chặn 2 thứ:
bịa expected lúc design, gian lận lúc eval.

Không có trong chuẩn nào. Vì chuẩn nào cũng viết trước khi có vấn đề này.

## Thiếu so với ISTQB — biết mà chưa làm

1. **Traceability hai chiều.** ISTQB đòi test basis ↔ condition ↔ case ↔ procedure ↔ result
   theo cả 2 chiều. Kit mới có case→DD. Thiếu:
   - DD→case (`coverage-check`, chưa nối)
   - result→case (có `id` nhưng chưa query ngược được)
2. **Test implementation** (phase 5) — chưa có. Đây là chỗ chuẩn bị test data + env.
   Hệ quả: `D_env` sẽ là category triage lớn nhất.
3. **Test completion** (phase 7) — chưa có. ISTQB đòi: đóng defect, test summary report,
   archive testware để tái dùng, lessons learned.
   Lessons learned = vòng nuôi `viewpoints.md`. Không có command thì sẽ không xảy ra.

## Ngoài kit

- **IVEC level 1–7** → career ladder cho team QC. Việc của lead, không phải của kit.
- **ISO 29119** → template test plan gửi khách.
- **SQuBOK** → khi nào kit muốn lên tầng QA (ngăn defect, không chỉ tìm defect).
  `gap-report` đã là mầm mống tư duy QA rồi.
