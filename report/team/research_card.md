# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột “Nhóm điền” bằng máy.

Phần này nối tiếp mini research ở buổi lý thuyết (slide 62–63). Nhóm chọn R3 và chuyển câu hỏi thành một ablation có thể chạy trong lab: giữ nguyên model, tool, seed, corpus, giá và evaluator; chỉ đổi shape.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL-IJCNLP 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R3 · Architecture choices |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Bogavelli, Subramani & Sharma (2026), [AgentArch: A Benchmark for Evaluating Agent Architectures in Enterprise Workflows](https://aclanthology.org/2026.aacl-long.44/), AACL-IJCNLP 2026; benchmark nghiên cứu. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Nghiên cứu đánh giá 18 cấu hình agent theo bốn chiều (chiến lược orchestration, ReAct/function calling, bộ nhớ và thinking tool), và báo cáo sở thích kiến trúc phụ thuộc vào model; không có một cấu hình tốt nhất cho mọi model. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết quả nguồn dựa trên benchmark workflow doanh nghiệp và các LLM được nghiên cứu trong paper. Ablation ở đây chỉ dùng fixture public của lab, MockLLM, 14 claim × 5 seed; không xác nhận kết luận cho model production hay workload khác. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Đổi `single` → `orchestrator`: pass rate dự kiến giữ gần 1.00 trên public claims; cost/success dự kiến tăng ít nhất 20% và mean steps tăng do thêm điều phối. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định MockLLM, tool manifest, public corpus (14 claim), seed `11,22,33,44,55`, bảng giá, evaluator và SQLite mới cho từng trial. Chỉ đổi shape `single` ↔ `orchestrator`. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Rủi ro là chi phí điều phối tăng mà độ đúng không tăng. Đo pass rate, pass^5, variance theo seed, cost/success mô phỏng và mean steps từ cùng benchmark; latency không khả dụng. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes single,orchestrator --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_ablation.json`
- Run id / file report: `R-single-C-001-s11`, `R-orchestrator-C-001-s11`; benchmark output was generated at `reports/research_ablation.json` during this run. The card records the result summary.
- Kết quả so với hypothesis: được ủng hộ trên fixture public này. Cả hai đạt 70/70, pass rate = 1.000, pass^5 = 1.000, seed min–max = 1.000–1.000, variance = 0. `single`: 32.39 VND/success, mean 2.64 steps. `orchestrator`: 47.23 VND/success (+45.8%), mean 3.71 steps (+1.07). Không thấy lợi ích pass rate để bù chi phí điều phối trong phép đo này.
- Giới hạn: 14 claim public và MockLLM; kết quả không chứng minh shape nào tốt hơn trên hidden set hay model production. Cost là VND mô phỏng, latency `unavailable`. Không có `student_drop/hidden_claims.jsonl` trong workspace nên chưa chạy hidden self-check.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
