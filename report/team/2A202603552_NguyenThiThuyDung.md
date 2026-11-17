# Báo cáo cá nhân — 2A202603552_NguyenThiThuyDung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thị Thùy Dung
- MSSV: 2A202603552
- Email: nttdungk5@gmail.com
- GitHub: Dunnguyn

## 2. Phần việc phụ trách

- CP2: viết shape C `orchestrator` (`src/lab8/shapes/orchestrator.py`) — tách orchestrator và investigator chỉ đọc.
- CP3: kiểm tra handoff, cách host dùng ledger và xử lý crash cho shape của mình.
- CP5: Điền decision_adr.md
- Tham gia đánh giá, nhận xét các PR trong nhóm.

## 3. Đóng góp cụ thể

- Commit `85bc805`: viết đầy đủ `orchestrator.py` — dùng `make_handoff` với `allowed_tools` chỉ gồm tool đọc, `facts={}` (không nhét dữ liệu claim thô), investigator chạy qua `run_readonly_investigators`.
- Commit `c0ae98e` ("cp3"): xử lý `TODO CP3` — truyền `crash_at` vào `durability.issue_refund`, không bắt `InjectedCrash` một cách sai cách.
- Commit `036b684`: cập nhật decision ADR dựa trên kết quả benchmark public.
- Bổ sung test `src/tests/test_orchestrator_handoff_boundary.py` để kiểm tra handoff chỉ cấp công cụ đọc và trace không chứa dữ liệu nhạy cảm.

## 4. Bằng chứng

- Commit `85bc805` (orchestrator) và `c0ae98e` (CP3).
- Ma trận student đã chạy: 248 bài pass, bao gồm các kịch bản T11 chạy lại và T12 crash rồi chạy lại trên các shape.
- Test handoff mới: `src/tests/test_orchestrator_handoff_boundary.py`

## 5. Công cụ AI đã dùng

Đã dùng Codex để giải thích luồng CP2, CP3 và hỗ trợ xây dựng test handoff. Kết quả được đối chiếu với contract và mã dự án, sau đó kiểm tra bằng ma trận student (`python -m pytest -q -m student -o addopts=`) và bộ test mặc định (`python -m pytest -q`).

## 6. Tự đánh giá

Qua phần việc Orchestrator, đã hiểu rõ hơn cách phân chia trách nhiệm giữa agent điều phối, Investigator chỉ đọc và host thực hiện giao dịch. Cũng đã hiểu vì sao cần giới hạn dữ liệu trong handoff, truyền quote đầy đủ cho host và kiểm tra khả năng chạy lại sau crash. Trong quá trình làm, khó khăn gặp phải khi phân biệt vai trò của ledger và checkpoint, nên cần đọc lại contract và xem kết quả kiểm thử để hiểu rõ hơn.
