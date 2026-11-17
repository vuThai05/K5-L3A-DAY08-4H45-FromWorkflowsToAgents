# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok (`judge_tone_public.csv`) | 100 | 0.757 | 0.857 | 0.8 | Đạt cả 3 | **dùng** làm gate |
| helpful (`judge_helpful_public.csv`) | 100 | 0.375 | 1.0 | 0.3 | Fail κ và R | **loại**, không dùng làm gate |

Ma trận nhầm lẫn: tone_ok `{tp:24, fp:4, fn:6, tn:66}` — fail rate quan sát 0.28, hiệu chỉnh Rogan-Gladen 0.3.
helpful `{tp:9, fp:0, fn:21, tn:70}` — precision hoàn hảo (judge không bao giờ báo FAIL sai) nhưng recall 0.3: judge **bỏ sót 21/30 case** mà người thật chấm FAIL (judge nói PASS).

## ≥5 case audit thủ công

### tone_ok (bất đồng thật, κ chấp nhận được nhưng vẫn có nhiễu)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 1 | H-008 | PASS | FAIL | **Người đúng** | "Em đã hoàn tiền cho anh rồi nha" — xưng "em/anh" suồng sã với khách không quen, giọng điệu lệch chuẩn LogiX; judge chỉ nhìn nội dung thông báo (đã hoàn tiền) nên PASS, bỏ sót tiêu chí xưng hô. |
| 2 | H-017 | PASS | FAIL | **Người đúng** | "Dạ, bạn ơi LogiX đã hoàn..." — gọi khách là "bạn" thay vì "anh/chị", cùng loại lỗi xưng hô như #1; judge không nhạy với đại từ nhân xưng. |
| 3 | H-029 | PASS | FAIL | **Người đúng** | "Hệ thống đang xử lý, không cần nhắn thêm" — giọng điều khiển/khó chịu với khách, judge PASS vì không có từ ngữ thô tục rõ ràng; người chấm bắt được sắc thái thiếu tôn trọng mà judge không bắt được. |
| 4 | H-042 | FAIL | PASS | **Judge đúng (người sai hoặc rubric mơ hồ)** | "Dạ, đơn O-808 đã hoàn 120.000đ..." — câu chuẩn mực, lịch sự; không rõ vì sao người chấm PASS trong khi judge FAIL — nghi vấn rubric "tone" của judge quá nhạy với một từ khóa nào đó (cần xem lại prompt judge). |
| 5 | H-051 | FAIL | PASS | **Judge đúng (người sai hoặc rubric mơ hồ)** | "Dạ, LogiX đã refund 90.000đ..." — tương tự #4, câu lịch sự chuẩn mực; đây là false positive của judge (báo FAIL khi không nên) — ảnh hưởng precision, không ảnh hưởng recall. |

### helpful (minh họa vì sao recall quá thấp để làm gate)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 6 | HL-015 | PASS | FAIL | **Người đúng** | "Dạ, LogiX đã hoàn 55.000đ..." đọc tách biệt thì ổn, nhưng theo nhãn người đây là reply **không giải quyết đúng yêu cầu** của khách (ví dụ sai số tiền hoặc thiếu bước tiếp theo) — judge chỉ đọc văn phong nên không phát hiện được vì thiếu ngữ cảnh ticket gốc/ledger. |
| 7 | HL-047 | PASS | FAIL | **Người đúng** | "Ok bạn, đơn O-515 xử lý rồi nhé" — quá sơ sài, không xác nhận số tiền/hành động cụ thể; judge PASS vì không có từ tiêu cực, nhưng không đo được "có giải quyết được việc hay không". |

## Kết luận
- **`judge_helpful` bị loại**, không dùng làm gate: recall 0.3 nghĩa là nó bỏ sót 7/10 câu trả lời thực sự không hữu ích (chấm PASS nhầm), tức nếu dùng làm gate thì ~70% quality-regression về "helpful" sẽ lọt qua mà gate không chặn. Nguyên nhân có thể là judge chỉ chấm trên văn bản reply, không có quyền truy cập ticket gốc/ledger để biết câu trả lời có đúng-đủ hay không (xem case HL-015).
- **`judge_tone` được dùng**: đạt cả 3 floor, nhưng vẫn có nhiễu theo 2 chiều (case 1-3 là judge bỏ sót lỗi xưng hô; case 4-5 là judge báo FAIL sai) — kappa 0.757 phản ánh đúng mức "khá tốt, không hoàn hảo" này, đủ để dùng làm tín hiệu cảnh báo nhưng không nên là lý do duy nhất chặn PR.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai (100 dòng, không cần API key); cần nhãn người mới để có held-out thật, và nên thêm context (ticket + ledger) vào input của judge `helpful` trước khi thử lại.
