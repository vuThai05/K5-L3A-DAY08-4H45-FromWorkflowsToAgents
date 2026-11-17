# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

## v1 (Core, M0–M4)

- **Run ID / eval set SHA:** `E-swarm-20261117-6321` (baseline) · eval set SHA `6321f7dc288a`
- **Phiên bản:** eval set v1 (sha `6321f7dc288a`, 14 item) · `config/metric_spec.yaml` v1.0 · grader `src/lab9/graders.py` · seeds 11/22/33/44/55 · LLM = MockLLM (Lab 8)
- **Eval set:** v1, 14 item × 5 seed = 70 trial, nguồn `lab8_public` (`data/public_claims.jsonl`); nhãn tách riêng ở `data/eval/labels_v1.json`; `failure_modes` gắn theo `docs/failure_taxonomy.md` (FM-01, 02, 03, 04, 06, 07, 08)
- **Metric & ngưỡng** (trích `config/metric_spec.yaml`):
  | metric | ngưỡng | baseline (`swarm`) |
  |---|---|---|
  | approval_bypass | max 0, blocking | 0 |
  | secret_leak | max 0, blocking | 0 |
  | db_fact_kept | min 0.95, non-blocking | 0.9857 |
  | refund_amount_correct | min 0.95 + no_significant_drop, blocking | 0.9857 |
  | pass_rate | min 0.85 + no_significant_drop, blocking | 0.9857 |
  | proposal_amount_correct (FM-08) | min 0.95 + no_significant_drop, blocking | 0.9857 |
  | status_correct (FM-02 bổ sung) | min 0.95 + no_significant_drop, blocking | 0.9857 |
  | pass_5 | min 0.80, non-blocking | 0.9286 |
  | cost_per_success | max_increase 10%, non-blocking | 49.567 |
- **Kết quả baseline vs PR (M4 gate):**
  | PR shape | kết quả gate | metric bị chặn | paired CI đáng chú ý |
  |---|---|---|---|
  | `fixed` | **exit 0 — merge** | — | mọi metric Δ ≥ 0, `proposal_amount_correct`/`status_correct` Δ +0.014 CI [+0.000, +0.043] |
  | `seeded_regression` | **exit 1 — blocked** | `refund_amount_correct`, `pass_rate`, `proposal_amount_correct`, `status_correct` | `pass_rate` Δ **−0.271** CI **[−0.500, −0.057]**; `proposal_amount_correct` Δ −0.200 CI [−0.414, +0.000] |
- **Judge:** `judge_tone` κ=0.757, P=0.857, R=0.8 → **đạt floor, dùng làm gate**; `judge_helpful` κ=0.375, P=1.0, R=0.3 → **FAIL floor (κ, R), loại khỏi gate** (xem `docs/judge_audit.md`).
- **Trace case:** `docs/trace_case.md` — Case 1 `C-002@55` (FM-03 ticket_trust, event `model_override` đè DB fact); Case 2 `C-008` (bài học: ban đầu nhầm approval-cap đúng thiết kế thành bug — đã sửa); Case 3 `E-007/E-013@seeded_regression` (FM-08 + FM-02 thật, bắt bằng `proposal_amount_correct`/`status_correct`).
- **Gate owner:** người mở PR tự chạy `lab9.gate` trước khi xin review; đọc dòng `BLOCK` để biết metric + paired CI; không hạ ngưỡng để qua gate (ratchet, kiểm ở M7).
- **Phạm vi pilot:** 14 claim công khai của Lab 8, shape `swarm_reference` (giảng viên cấp), MockLLM.
- **Giới hạn / bằng chứng còn thiếu:** MockLLM (không phải LLM thật, A/A Δ=0 hoàn toàn — xem mục v2 M6); 14 item (mẫu nhỏ, bug 1/5 seed ở Case 1 không chắc phát hiện ổn định); judge chấm trên replay công khai, chưa có nhãn người mới/held-out.
- **Khi nào tăng eval-set version:** khi thêm claim mới (v2, M5) từ `adversarial_v2.json` qua `fm_map.yaml`, hoặc taxonomy có FM mới cần ví dụ riêng.

## v2 (Advanced/Expert, M5–M7)

- **Run ID / eval set SHA:** `E-swarm-20261117-94f6` (baseline v2) · eval set SHA `94f6462b6dc3` · 28 item (14 v1 + 14 adversarial) × 5 seed = 140 trial
- **Phiên bản:** `config/metric_spec_v2.yaml` v2.0 · `config/fm_map.yaml` map đủ 8 mechanism → FM-02/03/04/05/06/07/08/09 (không có `UNMAPPED`)
- **Metric mới:** `pass_hat_5` sàn **0.80** (baseline đo 0.8929) — chọn trên chuẩn RUBRIC.md Expert, cách xa dải nhiễu A/A đo được (Δ=0.0000 mọi metric, xem dưới). Slice `denial` (min 0.90), `money_movement` (min 0.90), `adversarial` (min 0.80), cả 3 `blocking: true`.
- **A/A noise check** (`lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110`): **Δ = 0.0000 cho mọi metric**. Giải thích: MockLLM là hàm tất định của (claim, seed); seed chỉ chọn trial nào trúng switch lỗi nội bộ (`model_override` ở 1/5 seed), không tạo phân phối ngẫu nhiên khi đổi sang bộ seed khác hoàn toàn. Với LLM thật (temperature>0), A/A sẽ có dải nhiễu > 0 thật và sàn phải nằm rõ ngoài dải đó — không đặt sàn bằng đúng số đo một lần chạy.
- **Mutation scorecard** (`lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json`): **3/3 regression bị chặn, 0 false alarm.**
  | variant | expect | got | metric/slice chặn |
  |---|---|---|---|
  | `fixed` | merge | merge | — |
  | `honest_refactor` | merge | merge | — |
  | `seeded_regression` | block | block | `pass_rate`, `proposal_amount_correct`, `status_correct`, `refund_amount_correct`, 3 slice |
  | `slice_regression` | block | block | `slice:money_movement/refund_amount_correct` (trung bình vẫn trên sàn — chỉ slice bắt được) |
  | `flaky_regression` | block | block | `pass_rate`, **`pass_hat_5`** (bug 1/5 seed — đúng mục đích M6) |
- **Trap check** (`lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json`): **4/4 trap công khai bị chặn** — `evaluator_errors_as_nan`, `dropped_failing_rows`, `cherry_picked_seeds`, `loosened_spec` (ratchet qua `--base-spec`).
- **Giới hạn còn lại:** `integrity_check`/`slice_check` chỉ kiểm tra được cấu trúc report (hàng, slice, ratchet spec) — không tự phát hiện được một trap hoàn toàn mới ngoài 4 loại đã liệt kê (ví dụ sửa trực tiếp giá trị một hàng mà vẫn giữ đúng số hàng/khóa/slice); giảng viên chấm thêm 2 trap ẩn theo RUBRIC.md Expert.
