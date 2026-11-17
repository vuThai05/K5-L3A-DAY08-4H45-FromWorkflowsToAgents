# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: 4H45
- Thành viên: xem [TEAM.md](../../TEAM.md)
- Commit chốt (trùng `report/team/decision_adr.md`): `6609395` (xem `decision_adr.md` để cập nhật hash cuối cùng trước khi nộp)

## 2. Mục tiêu và cách tiếp cận

Nhóm xử lý claim hoàn phí vận chuyển của LogiX-VN bằng bốn kiến trúc — workflow (shape A), single agent ReAct (shape B), orchestrator + investigator (shape C), và swarm (shape D, có sẵn để đối chứng) — rồi dùng số đo thật để chọn kiến trúc **ít tự chủ nhất mà vẫn làm được việc**, thay vì mặc định "multi-agent tốt hơn".

Chia việc theo đúng 3 shape cần viết, mỗi người một shape:

1. **Vũ Quang Thái** — shape `single` (CP2): vòng ReAct tối đa 8 bước, model chỉ được chọn tool đọc.
2. **Nguyễn Thị Thùy Dung** — shape `orchestrator` (CP2–CP3): tách orchestrator và investigator chỉ đọc, dùng handoff đã sanitize.
3. **Lưu Thanh Mỹ** — shape `workflow` (CP2): các bước Python cố định, không có bước nào model tự quyết.

Thứ tự PR: base (setup) trước, 3 PR shape chạy song song (không đụng file của nhau), rồi đến các PR vá must-pass (CP3–CP4), cuối cùng là benchmark/ADR/báo cáo (CP5).

## 3. Giải pháp

Cả ba shape giữ đúng chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult` và cùng luồng nghiệp vụ: đọc claim qua `get_claim_view` → thiếu `order_id` thì `needs_info` → `lookup_order` (không thấy thì `escalated`) → tính quote bằng `compute_compensation` (code tính, không phải model) → quote = 0 thì `denied`, quote > 0 thì gọi `durability.issue_refund` với **quote đầy đủ** (host tự trừ phần đã hoàn trước đó theo đơn).

- **`workflow`**: không có model nào tham gia quyết định; chỉ các bước Python tuần tự.
- **`single`**: dùng `lab8.runtime.run_react` với `worker=True`, `decide()` xây args hoàn toàn từ dữ liệu đã có (không có chỗ nào model tự chọn `principal_id`/order), nên không có đường để giả mạo tham số tool.
- **`orchestrator`**: dùng `lab8.handoff.make_handoff` với `allowed_tools` chỉ gồm tool đọc, `facts={}` (không nhét dữ liệu claim thô); investigator chạy qua `run_readonly_investigators`, không có write registry.

**Ranh giới bảo mật:** trace chỉ ghi field đã qua allowlist (`get_claim_view`, `lookup_order`, handoff đã sanitize), không bao giờ ghi `parent_secret`, `raw_headers`, hay toàn bộ dòng claim/order thô. Một lỗi thật đã tìm thấy và vá: `single.py` từng ghi nguyên `last_result` (có thể chứa `ticket` thô) vào trace khi thoát sớm ở nhánh `needs_info` — đã sửa để chỉ ghi `last_tool`.

## 4. Kết quả

So trên cùng 14 claim public × 5 seed (`11,22,33,44,55`), cùng bảng giá, cùng evaluator — số liệu từ `src/reports/benchmark.json`:

| Shape | pass | pass^5 | variance | cost/success (VNĐ mô phỏng) | mean steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| **workflow** | 1.000 | 1.000 | 0.000000 | 34.29 | 1.86 |
| single | 1.000 | 1.000 | 0.000000 | 32.39 | 2.64 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 47.23 | 3.71 |
| swarm | 0.986 | 0.929 | 0.000816 | 49.57 | 2.80 |

Crash safety (`src/reports/crash.json`): **20/20**. Ba shape nhóm viết đều pass 100% trên cả 5 seed, không dao động. `swarm` (đối chứng, có sẵn) fail đúng 1/70 trial ở seed chia hết cho 5 vì tin vào con số delay khách tự ghi trong ticket thay vì đọc order row (`REFERENCE_WEAKNESS`).

Quyết định kiến trúc và lý do chi tiết: xem [`decision_adr.md`](decision_adr.md) — nhóm chọn `workflow` vì rẻ nhất, ít bước nhất, vẫn đạt pass rate tuyệt đối. Phiếu nghiên cứu và ablation: xem [`research_card.md`](research_card.md).

## 5. Khó khăn và cách xử lý

- **Rò dữ liệu nhạy cảm vào trace (`single.py`):** phát hiện khi viết test đối kháng — khi `order_id` thiếu, `trace.add("observation", outcome.get("observation", {}))` vẫn còn giữ `last_result` của bước `get_claim_view` trước đó, có thể chứa `ticket` thô. Xử lý: chỉ ghi `last_tool` vào trace, thêm test `test_shape_trace_privacy.py` để chặn tái diễn.
- **Một nhánh làm việc bị lệch ("thai"):** một PR dựa trên nhánh cũ đã vô tình revert `orchestrator.py` về stub và sửa `src/lab8/runtime.py` — file nằm ngoài phạm vi grader hidden đọc được, khiến `single.py` phụ thuộc vào nó sẽ fail khi chấm thật. Xử lý: không merge PR đó, viết lại đúng phần ý tưởng tốt (chặn giả mạo tham số tool) ngay trong `single.py`, không đụng `runtime.py`.
- **Conflict giữa các PR sửa cùng file báo cáo:** `TEAM.md` và `decision_adr.md`/`research_card.md` bị nhiều người sửa gần như cùng lúc, có lúc một merge lấy nhầm bản cũ (rỗng) đè lên bản đã điền. Xử lý: kiểm tra lại bằng `python -m lab8.check_submission` sau mỗi lần merge, phát hiện ngay khi số FAIL tăng trở lại.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong bảng đóng góp ở [TEAM.md](../../TEAM.md) và báo cáo cá nhân từng người (`report/team/2A202603545_VuQuangThai.md`, `report/team/2A202603552_NguyenThiThuyDung.md`, `report/team/2A202603532_LuuThanhMy.md`).

Tóm tắt:
- **Thái**: viết shape `single` (CP2).
- **Dung**: viết shape `orchestrator` (CP2–CP3), kiểm tra handoff và xử lý crash và report decision_adr.md.
- **Mỹ**: viết shape `workflow` (CP2), vá lỗi rò ticket vào trace và thêm test chống giả mạo tham số, chạy benchmark và quyết định kiến trúc (CP5), làm bonus B3.

## 7. Hạn chế và hướng cải thiện

- MockLLM không phải model sản xuất thật; một model ngôn ngữ thật có thể bị dẫn dắt theo những cách mà bộ test hiện tại chưa bao phủ (ví dụ chèn hướng dẫn giả thay vì chỉ một con số).
- Benchmark chỉ chạy trên 14 claim public; bộ hidden của giảng viên (40 claim × 5 seed) nhóm không tự chạy được bằng grader riêng, chỉ ước lượng qua pass rate public.
- Cost là VNĐ mô phỏng (`config/pricing.yaml`), không phải hóa đơn API thật; latency không đo được (`unavailable`).
- Nếu claim thực tế phức tạp hơn (cần điều tra nhiều nguồn song song, chính sách thay đổi thường xuyên), kết luận chọn `workflow` có thể đảo ngược — cần đo lại trên corpus đó trước khi kết luận.

## 8. Tài liệu tham khảo

- [docs/business_rules.md](../../docs/business_rules.md), [docs/contracts.md](../../docs/contracts.md), [docs/architecture.md](../../docs/architecture.md), [docs/metrics.md](../../docs/metrics.md) — tài liệu đề bài.
- Google Research 2026, *error amplification* (slide 17, 22, 42) — nguồn cho bonus B3, xem [bonus_report.md](bonus_report.md).
- EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* — nguồn cho research card, xem [research_card.md](research_card.md).
