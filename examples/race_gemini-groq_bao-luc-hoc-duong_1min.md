# Bạo lực học đường

| Framework | Generator | Judge | Score | Status | Best iteration | Time |
|---|---|---|---|---|---|---|
| RACE | gemini/gemini-3.6-flash | groq/openai/gpt-oss-120b | 90.9/100 (90.9%) | best_effort | 3/4 | 375.21s |

## Script

```text
Scene 1 — 00:00–00:04
Visual/Action:
Cận cảnh chiếc cặp sách bị hất văng xuống sàn hành lang với tiếng va chạm mạnh. Máy quay chuyển nhanh sang ánh mắt sợ hãi, rấn nước mắt của một học sinh. Chữ xuất hiện: BẠO LỰC HỌC ĐƯỜNG - Đừng im lặng!
Dialogue/Narration:
Bạn có chắc con mình, hoặc chính bạn, đang an toàn ở trường?

Scene 2 — 00:04–00:10
Visual/Action:
Khung hình chia đôi: Bên trái học sinh THCS ngồi thu mình nhìn điện thoại im lặng, bên phải người mẹ đứng ngoài cửa thở dài đầy âu lo. Chữ trên màn hình: Dấu hiệu âm thầm.
Dialogue/Narration:
Dấu hiệu bạo lực thường ẩn sau sự im lặng của con và nỗi lo của cha mẹ.

Scene 3 — 00:10–00:20
Visual/Action:
Đoạn 1: Học sinh bị giật mạnh balo và xô ngã. Đoạn 2: Một nhóm bạn chỉ tay thì thầm xúc phạm, nạn nhân cúi gục mặt né tránh. Chữ nổi bật: Thể xác & Lời nói.
Dialogue/Narration:
Đó là bạo lực thể xác như đánh đập, trấn tiền. Hay bạo lực lời nói như lăng mạ, miệt thị.

Scene 4 — 00:20–00:32
Visual/Action:
Màn hình điện thoại liên tục nổ tin nhắn miệt thị trong nhóm chat, chuyển cảnh học sinh ngồi một mình ở góc sân trường vắng lặng. Chữ xuất hiện: Bạo lực mạng & Cô lập.
Dialogue/Narration:
Bạo lực mạng với tin đồn lan truyền 24/7, cùng hành vi cô lập, tẩy chay khiến nạn nhân hoàn toàn đơn độc.

Scene 5 — 00:32–00:44
Visual/Action:
Chuỗi hình ảnh nhanh: Học sinh kéo chăn trùm đầu sợ hãi khi chuông báo thức reo, đẩy bỏ bát cơm đầy, ngồi thu mình ở góc phòng từ chối nói chuyện. Người mẹ nhẹ nhàng đến bên nắm lấy tay con. Chữ: Nhận diện thay đổi.
Dialogue/Narration:
Khi trẻ sợ đi học, bỏ ăn hay thu mình lại, đó là lúc con đang rất cần được bảo vệ.

Scene 6 — 00:44–01:00
Visual/Action:
Học sinh mỉm cười tự tin khi trải lòng với cô giáo tư vấn. Đồ họa số điện thoại 111 xuất hiện to, rõ cùng biểu tượng Thích và Chia sẻ nhấp nháy trên giao diện YouTube Shorts. Chữ: Tổng đài 111 — Chung tay bảo vệ con trẻ!
Dialogue/Narration:
Đừng chịu đựng một mình. Hãy chia sẻ với thầy cô, cha mẹ hoặc gọi ngay Tổng đài 111. Nhấn Thích và Chia sẻ video này vì một môi trường học đường an toàn!
```

## Rule-based evaluation

| Check | Points |
|---|---|
| duration | 15.0 |
| timeline | 5.0 |
| completeness | 10.0 |
| format | 5.0 |
| speech_rate | 9.8 |
| **total** | **44.8/45** |

Duration: 60s / 60s · Scenes: 6 · Narration: 131 words (2.18 words/s)

## LLM judge

| Criterion | Score |
|---|---|
| topic_relevance | 9/10 |
| audience_fit | 8/10 |
| structure | 9/10 |
| pacing | 7/10 |
| dialogue | 7/10 |
| hook | 9/10 |
| CTA | 9/10 |
| coherence | 9/10 |
| **total** | **46.1/55** |

Judge notes:

- Scene 2: Hình ảnh mẹ đứng ngoài cửa chưa truyền tải đủ lo lắng; nên thay bằng cảnh mẹ nhìn điện thoại hoặc trò chuyện với giáo viên để nhấn mạnh mối quan hệ cha mẹ-học sinh.
- Dialogue/Narration: Một số câu quá dài cho video 1 phút (ví dụ Scene 3 và Scene 4); cần rút ngắn thành câu ngắn, dễ đọc để tránh vội vã.
- Scene 5: Chuỗi hình ảnh nhanh có thể gây rối cho người xem; nên giảm số cảnh hoặc dùng chuyển cảnh mượt mà hơn để làm nổi bật hành động mẹ an ủi.
- CTA: Thêm hashtag hoặc lời kêu gọi cụ thể cho nền tảng Shorts (ví dụ #BảoVệTrẻ) để tăng khả năng lan truyền.
- Scene 6: Số điện thoại 111 xuất hiện quá nhanh; nên để trên màn hình ít nhất 3‑4 giây để người xem có thời gian ghi nhớ.

## Iteration history

| Iteration | Score | Duration | Issues |
|---|---|---|---|
| 1 | 89.7% | 60s/60s | 7 |
| 2 | 90.4% | 60s/60s | 7 |
| 3 | 90.9% | 60s/60s | 8 |
| 4 | 87.2% | 60s/60s | 8 |
