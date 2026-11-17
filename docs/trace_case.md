# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

## Case của nhóm

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, trong report `E-seeded_regression-20261117-b22c` (item E-002) |
| Triệu chứng | Grader Lab 8: `FAIL (status resolved != denied)`. Ledger ghi 20.000đ (1 dòng) trong khi nhãn là 0đ, `denied`. Reply nói "đã hoàn 20.000đ cho đơn O-202" nên **khớp ledger**: reply trôi chảy và nhất quán nhưng quyết định sai. `db_fact_kept`, `refund_amount_correct`, `pass_rate` cùng fail ở cả 5 seed. |
| Bước sai đầu tiên | Event 3 `model_override {"delay_days": 5}`: agent ghi đè số ngày trễ của DB bằng số trong ticket. |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` đúng allowlist; event 2 `investigator` trả `lookup_order` visible, đơn O-202 `delivered` với `delay_days` = 2 (DB đúng). Ticket nói "trễ 5 ngày" khác DB, và event 3 là chỗ đầu tiên agent chọn ticket. Các event sau (4 `quote` 20.000đ theo clause SHIP-LATE-03, 5 `refund_history`, 6 `reply`) chỉ hệ quả của con số 5 này. |
| Failure mode | FM-03 `ticket_trust` (`docs/failure_taxonomy.md`) |
| Đối chứng | `fixed C-002@11`: không có event `model_override`; trace chỉ có `handoff → investigator → quote → …`, `delay_days` giữ 2, status `denied`, ledger 0, khớp nhãn. |
| Regression test | `src/tests/test_lab9_trace_case.py` (2 test). Đã fail theo đúng ý trên `seeded_regression`: `DbFactKept` và `RefundAmountCorrect` đều `False`, `model_override` ở vị trí thứ 3. Pass trên `fixed`: cả hai grader `True`, không có event override, `ReplyMatchesLedger` `True`. Chạy: `python -m pytest -q -m student -o addopts= -k trace_case`. |
| Chưa chắc chắn | (1) Trace chỉ cho biết agent *đã* dùng số của ticket, không cho biết vì sao (MockLLM, không có suy luận để đọc). (2) Biến thể `quiet_override` cùng lỗi nhưng không ghi event `model_override`: đã chạy thử trên C-002@11, `DbFactKept` vẫn `True` (không thấy lỗi) còn `RefundAmountCorrect` `False`. Test trên bắt được lỗi này nhờ grader ledger, chứ không nhờ event. (3) Chỉ một claim@seed; chưa chứng minh mọi ca FM-03 có cùng dạng. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
