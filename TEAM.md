# Team

## Thông tin nhóm

- Tên nhóm: 4H45
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-4H45-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo: https://github.com/vuThai05/K5-L3A-DAY08-4H45-FromWorkflowsToAgents.git

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1  |    Vũ Quang Thái    |   2A202603545    |   qtvu2k5@gmail.com    |    vuThai05    |    Tạo fork repo; CP2: shape single; CP4: xử lý approval hợp lệ; đánh giá và nhận xét các phần còn lại   |
|   2  |    Nguyễn Thị Thùy Dung   |   2A202603552   |   nttdungk5@gmail.com| Dunnguyn| CP2: shape orchestrator; CP3: Handoff, ledger, crash; CP4: xử lý crash & secret; đánh giá và nhận xét các phần còn lại  |
|   3  |    Lưu Thanh Mỹ    |   2A202603532    |    data97688@gmail.com|    aialphaproduct    | CP2: shape workflow; CP5: benchmark, hidden, quyết định kiến trúc; đánh giá và nhận xét các phần còn lại          |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Vũ Quang Thái | Shape single; approval | `16496be` (single); `c53ea1e` (test) | `src/tests/test_single_react_flow.py` (`c53ea1e`) |
| Nguyễn Thị Thùy Dung | Orchestrator; CP3; crash và secret; decision ADR | `85bc805` (orchestrator); `c0ae98e` (CP3); `e629726` (CP4); `036b684` (ADR) | `src/tests/test_orchestrator_handoff_boundary.py` (commit `999d196`); `src/tests/test_shape_trace_privacy.py` (commit `e629726`)  |
| Lưu Thanh Mỹ | Shape workflow; benchmark, hidden, quyết định kiến trúc; vá rò ticket và khóa tham số tool trong single.py | `76aab20` (workflow); `76709c4` (trace privacy + arg integrity); `2ddce84` (benchmark) | `src/tests/test_shape_trace_privacy.py`, `src/tests/test_single_arg_integrity.py` (commit `76709c4`) |
