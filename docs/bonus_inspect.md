# Bonus: port 3 grader sang Inspect AI, so khớp kết quả

Chạy `python -m lab9.bonus_inspect` trên shape `swarm`, 70 trial (14 claim x 5 seed, cùng dữ liệu baseline_v1). Mỗi trial được chấm HAI LẦN trên CÙNG một Trial object: một lần bằng Evaluator pydantic-evals gốc (`lab9/graders.py`), một lần bằng Scorer Inspect AI mới viết (`secret_leak_ported`, `approval_bypass_ported`, `refund_amount_correct_ported`).

**Kết quả: 70/70 trial khớp 100% trên cả 3 grader.**

| Grader | Khớp / tổng |
|---|---|
| `secret_leak_ported` | 70/70 |
| `approval_bypass_ported` | 70/70 |
| `refund_amount_correct_ported` | 70/70 |

## Vì sao Inspect AI không cần model/API key ở đây
`no_model_solver` không gọi `generate()` -- Trial đã được `lab9.eval.make_task` tính sẵn (MockLLM, giống hệt cách `lab9/graders.py` chấm). `model="mockllm/model"` chỉ là provider built-in của Inspect AI để `eval()` có model id hợp lệ, không hề được gọi tới.

## Khác biệt khi port (và một lỗi thật đã gặp)
- Trong chính `lab9/graders.py`, quy ước **không đồng nhất**: `SecretLeak`/`ApprovalBypass` (an toàn) có `value=True` nghĩa là "phát hiện vấn đề", nhưng `RefundAmountCorrect` (năng lực) có `value=True` nghĩa là "đúng" (good) — NGƯỢC LẠI. Lần chạy đầu tiên của script này quên đảo chiều cho `RefundAmountCorrect`, ra **0/70 khớp** dù logic port đúng — tưởng port sai, hoá ra do quy ước lẫn lộn giữa các grader cùng file. Sửa xong (map đúng `invert=True` cho metric có quy ước "True=good") mới ra 70/70.
- Inspect AI: `Scorer` trả `Score(value=CORRECT/INCORRECT)` — một quy ước duy nhất, không lẫn lộn như trên. Đây là điểm cộng thực tế của Inspect AI so với viết Evaluator tay: ép người port phải tường minh "đúng" nghĩa là gì cho mỗi scorer, không ngầm định theo tên class.

## Giới hạn
Chỉ port 3/6 grader code (an toàn + 1 capability); chưa port grader step-level (`DbFactKept`) hay 2 grader FM-08 mới (`ProposalAmountCorrect`, `StatusCorrect`). Không port sang DeepEval (chọn 1 trong 2 theo đề bài).
