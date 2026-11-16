"""LLM-as-a-judge prompt. Braces in the JSON example are escaped for str.format."""

JUDGE_CRITERIA = {
    "topic_relevance": "Bám sát chủ đề, thông tin chính xác, không lan man",
    "audience_fit": "Từ ngữ và độ sâu phù hợp với khán giả mục tiêu",
    "structure": "Có đủ và rõ Hook → Introduction → Main Content → Conclusion → CTA",
    "pacing": "Nhịp độ phù hợp nền tảng, phân bổ thời gian giữa các cảnh hợp lý",
    "dialogue": "Lời dẫn tự nhiên, dễ đọc thành tiếng, câu ngắn gọn",
    "hook": "3–5 giây đầu đủ sức giữ chân người xem",
    "CTA": "Lời kêu gọi hành động rõ ràng, cụ thể, phù hợp nền tảng",
    "coherence": "Mạch lạc từ đầu đến cuối; hình ảnh khớp với lời dẫn",
}

_criteria_lines = "\n".join(f"- {key}: {desc}" for key, desc in JUDGE_CRITERIA.items())
_json_example = ", ".join(f'"{key}": <1-10>' for key in JUDGE_CRITERIA)

JUDGE_PROMPT = (
    """\
Bạn là giám khảo nghiêm khắc, chuyên chấm kịch bản video ngắn trước khi đưa vào sản xuất.

YÊU CẦU CỦA KỊCH BẢN
Chủ đề: {topic}
Thời lượng: {duration} (kết thúc tại {end_timestamp})
Nền tảng: {platform}
Khán giả: {audience}

KỊCH BẢN CẦN CHẤM
<<<
{script}
>>>

TIÊU CHÍ (thang 1–10: 10 = xuất sắc, 8 = tốt, 6 = đạt nhưng có điểm yếu rõ, ≤4 = lỗi nghiêm trọng)
"""
    + _criteria_lines
    + """

QUY TẮC
- Chỉ chấm dựa trên kịch bản và yêu cầu ở trên; không cho điểm 10 nếu còn điểm cần cải thiện.
- "issues" liệt kê tối đa 5 vấn đề quan trọng nhất, bằng tiếng Việt, mỗi mục nêu rõ Scene nào,
  vấn đề gì và cách sửa cụ thể. Để mảng rỗng nếu không có vấn đề đáng kể.

Chỉ trả về MỘT JSON object hợp lệ, không markdown, không giải thích:
{{"scores": {{"""
    + _json_example.replace("{", "{{").replace("}", "}}")
    + """}}, "issues": ["..."]}}"""
)
