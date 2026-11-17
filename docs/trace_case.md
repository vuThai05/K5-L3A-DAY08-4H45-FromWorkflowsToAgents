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

## Case 2: C-008 (mọi seed) — misreport (FM-08)

| Trường | Nội dung |
|---|---|
| Trial | `swarm C-008@11..55` (toàn bộ 5 seed), cùng run `E-swarm-20261117-d8c6` |
| Triệu chứng | `reply_amount_matches_ledger` FAIL cả 5 seed (grader mới M3); `refund_amount_correct` và `pass_rate` vẫn PASS vì cả hai chỉ so ledger với nhãn, không so với số agent "chốt" với khách. |
| Bước sai đầu tiên | Event `quote {"amount_vnd": 35000, ...}` — agent chốt 35.000đ (đúng bằng phí ship gốc) với khách, nhưng ledger cuối cùng chỉ commit `refund_vnd=20000` (nhãn xác nhận 20.000đ là số đúng sau áp policy/giảm trừ). |
| Vì sao là bước *đầu tiên* | `investigator` tra đúng `shipping_fee_vnd=35000` — đúng. Bước `quote` là nơi đầu tiên số 35000 được "chốt" làm số cuối cùng gửi khách, trong khi phần tính lại/áp policy ra 20000 xảy ra sau đó, không được đồng bộ ngược lại câu trả lời khách. |
| Failure mode | **FM-08 misreport** — số tiền trong reply khác số tiền ledger thực ghi. |
| Đối chứng | Không áp dụng theo seed (lỗi trúng cả 5/5 seed của C-008, C-007, C-013, C-014 — là lỗi **hệ thống** của `swarm_reference`, không phải nhiễu). |
| Regression test | `reply_amount_matches_ledger` (grader `ReplyAmountMatchesLedger`, `lab9/graders.py`) + metric cùng tên trong `config/metric_spec.yaml` (`threshold: {min: 0.95, no_significant_drop: true}, blocking: true`). Baseline hiện đo `reply_amount_matches_ledger = 0.7143` — dưới ngưỡng 0.95, nên về nguyên tắc **đã phải BLOCK** nếu đây là PR thay vì baseline; nhóm ghi nhận làm nợ kỹ thuật cần sửa ở `swarm_reference`/pipeline tính quote trước khi hạ ngưỡng. |
| Chưa chắc chắn | Chưa rõ 20.000đ (số ledger) hay 35.000đ (số quote) là số "đúng theo policy" — nhãn `expected.refund_vnd=20000` được giảng viên cung cấp nên coi là đúng, nhưng lý do giảm từ 35000→20000 (deductible nào, clause nào) không xuất hiện trong trace công khai. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
