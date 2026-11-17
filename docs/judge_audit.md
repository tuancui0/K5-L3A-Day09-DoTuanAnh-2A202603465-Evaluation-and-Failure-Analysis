# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (backend replay, verdict của judge nằm sẵn trong CSV). FAIL là lớp dương: việc của judge là tìm lỗi.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | **Đạt** (tp 24, fp 4, fn 6, tn 66) | **Dùng**, chỉ cho giọng điệu, không chặn merge |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt** κ và recall (tp 9, fp 0, fn 21, tn 70) | **Loại** khỏi gate |

Tỉ lệ lỗi hiệu chỉnh Rogan-Gladen: tone_ok quan sát 0.28 → 0.30; helpful quan sát 0.09 → 0.30. Judge helpful chỉ thấy 9/30 lỗi thật nên tỉ lệ lỗi báo cáo thấp hơn thực tế hơn 3 lần.

## 7 case audit thủ công (tone_ok)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha…" | PASS | FAIL | Người | Xưng "em" + "nha" quá suồng sã; judge nhầm suồng sã với thân thiện. Rubric: nêu rõ cách xưng hô bắt buộc ("anh/chị", mở đầu "Dạ"). |
| 2 | H-017 "Dạ, bạn ơi… rồi nha" | PASS | FAIL | Người | Xưng "bạn" với khách; có chữ "Dạ" nên judge cho qua. Rubric: một từ lễ phép không bù cho xưng hô sai. |
| 3 | H-029 "…không cần nhắn thêm" | PASS | FAIL | Người | Giọng ra lệnh; judge chỉ thấy "Dạ, vui lòng". Rubric: cấm câu mệnh lệnh với khách, thêm ví dụ FAIL này. |
| 4 | H-051 "LogiX đã refund 90.000đ…" | FAIL | PASS | Người | CS LogiX cho phép từ "refund". Judge phạt tiếng Anh. Rubric: ghi danh sách thuật ngữ được phép. |
| 5 | H-081 "Đơn O-107 chưa đủ điều kiện…" | FAIL | PASS | **Judge** | Ghi chú của chính bộ dữ liệu: nhãn người sai (đọc nhầm ticket). Sửa nhãn thành FAIL, không sửa judge. Đây là bằng chứng nhãn người cũng cần kiểm. |
| 6 | H-063 "…và sẽ hoàn thêm cho anh/chị ạ" | PASS | FAIL | Người | Hứa hoàn thêm ngoài kết quả hệ thống: đây không còn là lỗi giọng điệu mà là lời hứa sai sự thật → chuyển sang grader code đối chiếu ledger, rubric tone không chịu trách nhiệm. |
| 7 | H-088 "Dạ, dạ, LogiX đã hoàn…" | FAIL | PASS | Người | Lặp "Dạ" do lỗi gõ, không ảnh hưởng giọng. Rubric: lỗi chính tả/lặp từ không tính vào tone, để tiêu chí khác xử lý. |

Tổng kết bất đồng của tone_ok: judge hụt 6 lỗi (xưng hô, mệnh lệnh, emoji, hứa hẹn, mất dấu) và phạt nhầm 4 (thiếu xin lỗi, "refund", lặp "Dạ"; riêng H-081 là nhãn người sai). Lỗi lặp lại: judge bị "Dạ" đánh lạc hướng và không biết các quy ước riêng của LogiX.

## Vì sao không dùng judge helpful làm gate
- **Recall 0.30, κ 0.375**: trong 30 reply lỗi thật, judge cho qua 21. Gate dùng judge này sẽ cho merge phần lớn bản tệ.
- **Nó cho qua đúng loại lỗi nguy hiểm nhất**: 18/21 reply bị bỏ lọt có `human_failure = "sai tiền"` (reply nêu số khác ledger, ví dụ HL-015 nói 55.000đ khi ledger ghi 40.000đ) và 3 ca "sai xưng hô". Judge chỉ đọc chữ trong reply, **không thấy ledger**, nên không thể biết số tiền sai.
- **Thiên lệch độ dài**: các reply xin lỗi dài và lặp (HL-016, HL-028, HL-035…) đều được PASS dù sai tiền; văn phong lịch sự che mất lỗi.
- Precision 1.0 không cứu được: judge không bao giờ báo nhầm, nhưng cũng hiếm khi báo đúng; precision cao với recall thấp chỉ cho thấy nó rất kén.
- **Thay bằng**: FM-08 do grader code `ReplyMatchesLedger` (đối chiếu số trong reply với ledger), chạy rẻ, xác định, đo 10/70 trial lỗi trên `misreport` và 0 báo nhầm trên `fixed`. Quy tắc từ lecture: tiền và phê duyệt luôn chấm bằng code.

## Kết luận
- Tiêu chí bị loại: **helpful** (κ 0.375, recall 0.30; ma trận nhầm lẫn tp 9 / fp 0 / fn 21 / tn 70). Lý do chính: lỗi chủ yếu là sai tiền, thứ judge không quan sát được.
- tone_ok đạt cả ba ngưỡng nhưng chỉ ở mức vừa phải (R 0.80, P 0.857); dùng để theo dõi (cảnh báo), không dùng để chặn release. Đề xuất sửa rubric ở các dòng 1–4, 6–7 trước khi hiệu chuẩn lại.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai (n = 100 mỗi tiêu chí); cần nhãn người mới để có held-out thật. Nhãn người cũng sai (H-081), nên cần hai người gán nhãn độc lập và tính κ giữa người với người.
