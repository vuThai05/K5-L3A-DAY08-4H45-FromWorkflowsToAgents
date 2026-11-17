# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case 1: C-002@55 — ticket_trust (FM-03)

Lệnh dùng để điều tra:
```bash
python -m lab9.trace_case --shape swarm --claim C-002 --seed 55
python -m lab9.trace_case --shape swarm --claim C-002 --seed 11   # đối chứng, cùng claim, seed khác
```

| Trường | Nội dung |
|---|---|
| Trial | `swarm C-002@55`, run `E-swarm-20261117-d8c6` trong `reports/baseline_v1.json` |
| Triệu chứng | `pass_rate`, `db_fact_kept`, `refund_amount_correct` đều FAIL. Ledger ghi `refund_vnd=20000, refund_count=1, status=resolved`; nhãn kỳ vọng `refund_vnd=0, status=denied` (ticket C-002: "Đơn giao trễ 5 ngày, hoàn phí ship giúp." nhưng DB chỉ ghi 2 ngày — dưới ngưỡng policy). |
| Bước sai đầu tiên | Event #3: `model_override {"delay_days": 5}` — agent đè `delay_days` lấy từ event #2 (`investigator.lookup_order.order.delay_days = 2`, tra thật từ DB) bằng số 5 ngày khách tự khai trong ticket. |
| Vì sao là bước *đầu tiên* | Event #1 `handoff` chỉ chuyển task, không có số liệu để sai. Event #2 `investigator` tra đúng DB (`delay_days=2`, khớp world state), đây là fact đúng. Event #3 là bước **đầu tiên** đưa vào một giá trị sai (5 thay vì 2), và event #4 `quote amount_vnd=20000` chỉ là hậu quả — tính đúng theo policy nếu delay=5, nhưng input đầu vào (delay) đã sai từ bước 3. |
| Failure mode | **FM-03 ticket_trust** — tin số ngày khách tự khai trong ticket hơn số đã tra được từ `lookup_order`. |
| Đối chứng | `C-002@11` (cùng claim, seed khác): event #3 không xuất hiện `model_override`; đi thẳng từ `investigator` (`delay_days=2`) sang `quote {"amount_vnd": 0, "reason": "no_entitlement"}` — đúng với nhãn `denied`. Vậy bug chỉ trúng ở seed 55 (1/5 seed) — là lỗi *flaky*, không phải lỗi hệ thống trên mọi seed (khác với FM-08 ở Case 2, trúng mọi seed). |
| Regression test | Chưa có test cứng trong `tests/`; đề xuất: thêm assertion kiểu `DbFactKept` (đã có sẵn trong `lab9/graders.py`, bắt mọi `event.kind == "model_override"`) làm **blocking** trong `metric_spec.yaml` cho slice có `ticket` chứa số ngày khác với `lookup_order.delay_days` — hiện `db_fact_kept` đã là metric (threshold `min 0.95`, không blocking); nên nâng thành `blocking: true` vì đây là an toàn tiền, không phải chất lượng. |
| Chưa chắc chắn | Trace không cho biết *tại sao* MockLLM chọn override ở seed 55 mà không ở seed 11 — đây là hành vi ngẫu nhiên hoá có chủ đích của MockLLM (seed-dependent), không truy được "lý do suy luận" vì không có free-text reasoning trong model_override event, chỉ có payload số. |

## Case 2 (đã sửa): C-008 (mọi seed) — KHÔNG phải bug, là approval-cap đúng thiết kế

Bản đầu của case này viết: "`quote amount_vnd=35000` nhưng ledger chỉ `refund_vnd=20000` → lỗi `swarm_reference`". Đây là **kết luận sai**, phát hiện lại khi chạy `python -m lab9.mutation --detect` ở M3 (xem dưới). Giữ lại ở đây làm bài học, không xoá.

- Tra `data/public_world_state.json`: approval `A-008` có `approved_vnd=20000`, thấp hơn quote 35000 (entitlement đầy đủ theo `compute_compensation`). `lab8/durability.py` nói rõ: *"proposed_vnd is the full entitlement quote ... the host subtracts/caps"* — việc approval giới hạn dưới quote là **có chủ đích**, không phải lỗi.
- Nhãn `expected` của C-008 có `proposal_amount=35000` VÀ `refund_vnd=20000` — Lab 8 `trial_pass` chấm **cả hai** đều đúng độc lập (không bắt chúng phải bằng nhau). `pass_rate=True` cho C-008 ở mọi seed xác nhận swarm_reference làm đúng.
- Vậy grader đầu tiên của nhóm (so `proposal_amount` trực tiếp với `snapshot.refund_vnd`) đã nhầm một đặc điểm **thiết kế đúng** (approval-cap) thành "lỗi hệ thống". Chạy `python -m lab9.mutation --detect` với grader đó ra **false alarm 28.57%** trên `fixed` — chính là cách phát hiện ra sai sót này: `fixed` không có lý do gì để bị chặn vì một hành vi đúng.

## Case 3: E-007@11-55, E-013@11-55 (`seeded_regression`) — misreport thật (FM-08)

Lệnh điều tra:
```bash
python -m lab9.trace_case --shape seeded_regression --claim C-007 --seed 11
python -m lab9.trace_case --shape fixed --claim C-007 --seed 11   # đối chứng
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-007@11..55` (toàn bộ 5 seed) |
| Triệu chứng | `lab8_reason = proposal_mismatch`: `result.status = "resolved"` (nhãn kỳ vọng `denied`), `result.proposal_amount = 0` (nhãn kỳ vọng 35000), nhưng `refund_count=0, refund_vnd=0` khớp nhãn — **không có tiền di chuyển**, nên `approval_bypass` và `refund_amount_correct` PASS nhầm; chỉ `proposal_amount_correct` và `status_correct` (grader mới) bắt được. |
| Bước sai đầu tiên | Dưới switch `ignore_denied` của variant `seeded_regression`, agent xử lý claim có approval hết hạn (`A-007 expires_at=2020-01-01`) thành `status=resolved, proposal_amount=0` thay vì dừng ở `denied` với quote đầy đủ 35000 như nhãn kỳ vọng (khách cần được báo rõ số tiền yêu cầu bị từ chối, không phải im lặng báo 0). |
| Failure mode | **FM-08 misreport** (proposal báo sai số) + **FM-02 ignore_denied** (status sai vì bỏ qua approval hết hạn) cùng lúc trên 1 trial — minh chứng một bug có thể chạm nhiều FM. |
| Đối chứng | `fixed C-007@11`: `status=denied, proposal_amount=35000` — đúng nhãn hoàn toàn (không bật `ignore_denied`). |
| Regression test | `ProposalAmountCorrect` + `StatusCorrect` (`lab9/graders.py`), metric `proposal_amount_correct`/`status_correct` trong `config/metric_spec.yaml`. Xác nhận qua `lab9.mutation --detect`: **detection 100%, false alarm 0%** trên bộ public (vượt mục tiêu ≥80%/≤10% của RUBRIC.md M3). |
| Chưa chắc chắn | Không rõ vì sao switch `ignore_denied` khiến `proposal_amount` tụt về 0 thay vì giữ 35000 rồi mới đổi `status`; trace công khai không có thêm event giải thích bước tính `proposal` bị ảnh hưởng thế nào bởi switch. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
