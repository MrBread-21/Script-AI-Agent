"""Prompt-engineering frameworks under comparison.

Each framework keeps its own *structure* (the thing being benchmarked) while
sharing the same hard constraints from :mod:`script_agent.prompts.common`.

| Framework | Sections                                                    |
|-----------|-------------------------------------------------------------|
| RICE      | Role · Input · Context · Example                            |
| TAG       | Task · Action · Goal                                        |
| CARE      | Context · Action · Result · Example                         |
| RACE      | Role · Action · Context · Execute                           |
| RISE      | Role · Input · Steps · Expectation                          |
| HYBRID    | Role · Context · Input · Steps · Constraints · Example      |
"""

from __future__ import annotations

import re

from script_agent.prompts.common import DURATION_RULES, EXAMPLE, LANGUAGE_RULE, OUTPUT_FORMAT

REQUEST_BLOCK = """\
Chủ đề: {topic}
Thời lượng: {duration} ({duration_seconds} giây)
Nền tảng: {platform}
Đối tượng khán giả: {audience}
{extra_context}"""

KNOWLEDGE_BLOCK = """\
Cấu trúc: {structure}
Nhịp độ: {pacing}
Lời thoại: {dialogue}"""

ROLE_BLOCK = """\
Bạn là biên kịch video ngắn và chiến lược gia nội dung chuyên nghiệp, chuyên về:
- Video giáo dục dạng ngắn cho TikTok, YouTube Shorts, Reels
- Kể chuyện bằng hình ảnh và nhịp dựng nhanh
- Viết lời dẫn (voice-over) tự nhiên, phù hợp từng nhóm khán giả"""


RICE_PROMPT = f"""\
[ROLE]
{ROLE_BLOCK}

[INPUT]
YÊU CẦU CỦA NGƯỜI DÙNG
{REQUEST_BLOCK}

KIẾN THỨC SẢN XUẤT
{KNOWLEDGE_BLOCK}

[CONTEXT]
Kịch bản sẽ được dùng trực tiếp làm đầu vào sản xuất (quay/dựng và thu voice-over)
cho một video trên {{platform}}, hướng tới {{audience}}.

{DURATION_RULES}

{LANGUAGE_RULE}

[EXAMPLE]
{EXAMPLE}

{OUTPUT_FORMAT}"""


TAG_PROMPT = f"""\
[TASK]
Viết kịch bản video ngắn cho hệ thống sản xuất nội dung chuyên nghiệp.

{REQUEST_BLOCK}

Kiến thức sản xuất tham khảo:
{KNOWLEDGE_BLOCK}

[ACTION]
Tạo kịch bản hoàn chỉnh, trong đó:
- Hook gây tò mò ngay trong 3–5 giây đầu
- Phát triển chủ đề rõ ràng theo mạch Hook → Introduction → Main Content → Conclusion → CTA
- Mỗi cảnh có chỉ dẫn hình ảnh cụ thể và lời dẫn tương ứng
- Kết thúc bằng CTA rõ ràng, phù hợp với {{platform}}

{DURATION_RULES}

{LANGUAGE_RULE}

[GOAL]
Một kịch bản dài {{duration}}, sẵn sàng sản xuất, bám sát chủ đề và phù hợp với {{audience}}.

{OUTPUT_FORMAT}"""


CARE_PROMPT = f"""\
[CONTEXT]
Bạn là một phần của hệ thống sản xuất video ngắn tự động. Hệ thống nhận một chủ đề và
tạo kịch bản dùng cho quá trình sản xuất video thực tế.

YÊU CẦU CỦA NGƯỜI DÙNG
{REQUEST_BLOCK}

KIẾN THỨC SẢN XUẤT ĐƯỢC TRUY XUẤT
{KNOWLEDGE_BLOCK}

[ACTION]
Viết một kịch bản video ngắn hoàn chỉnh từ yêu cầu và kiến thức sản xuất ở trên.
Dùng kiến thức làm định hướng cho cấu trúc, nhịp độ và lời thoại, nhưng không mâu thuẫn
với yêu cầu rõ ràng của người dùng.

[RESULT]
Kết quả là kịch bản sẵn sàng sản xuất:
- Có đủ Hook, Introduction, Main Content, Conclusion, CTA
- Mỗi cảnh có số thứ tự, mốc thời gian, Visual/Action và Dialogue/Narration
- Ngôn ngữ phù hợp với {{audience}}, phong cách phù hợp với {{platform}}

{DURATION_RULES}

{LANGUAGE_RULE}

[EXAMPLE]
{EXAMPLE}

{OUTPUT_FORMAT}"""


RACE_PROMPT = f"""\
[ROLE]
{ROLE_BLOCK}

[ACTION]
Chuyển chủ đề và yêu cầu sản xuất dưới đây thành một kịch bản mạch lạc, hấp dẫn và
sẵn sàng sản xuất.

[CONTEXT]
YÊU CẦU CỦA NGƯỜI DÙNG
{REQUEST_BLOCK}

KIẾN THỨC ĐƯỢC TRUY XUẤT (định hướng, không ghi đè yêu cầu của người dùng)
{KNOWLEDGE_BLOCK}

{LANGUAGE_RULE}

[EXECUTE]
1. Xây dựng kịch bản thành chuỗi cảnh theo mạch Hook → Introduction → Main Content → Conclusion → CTA.
2. Mỗi cảnh gồm: số thứ tự, thời gian bắt đầu–kết thúc (MM:SS), Visual/Action, Dialogue/Narration.
3. Điều chỉnh từ vựng và độ sâu giải thích theo {{audience}}.
4. Điều chỉnh nhịp độ và cách trình bày theo {{platform}}.
5. Giữ mạch lạc từ đầu đến cuối; hình ảnh phải khớp với lời dẫn.

{DURATION_RULES}

{OUTPUT_FORMAT}"""


RISE_PROMPT = f"""\
[ROLE]
Bạn là biên kịch video ngắn, biên tập viên nội dung và chiến lược gia video chuyên nghiệp.
Chuyên môn: kể chuyện dạng ngắn, nhịp độ video, điều chỉnh nội dung theo khán giả,
lập kế hoạch hình ảnh và lời dẫn.

[INPUT]
YÊU CẦU CỦA NGƯỜI DÙNG
{REQUEST_BLOCK}

KIẾN THỨC SẢN XUẤT
{KNOWLEDGE_BLOCK}

{LANGUAGE_RULE}

[STEPS]
Thực hiện nội bộ (không viết ra) quy trình sau:
1. Phân tích yêu cầu: chủ đề, khán giả, nền tảng, thời lượng.
2. Thiết kế mạch kể: Hook → Introduction → Main Content → Conclusion → CTA.
3. Phân bổ {{duration_seconds}} giây cho các cảnh sao cho cảnh cuối kết thúc tại {{end_timestamp}}.
4. Viết lời dẫn với lượng chữ tương xứng độ dài từng cảnh.
5. Thêm chỉ dẫn hình ảnh cụ thể cho từng cảnh.
6. Tự kiểm tra: thời lượng, mốc thời gian liên tục, độ bám chủ đề, độ phù hợp khán giả và nền tảng, CTA.

{DURATION_RULES}

[EXPECTATION]
Chỉ xuất kịch bản cuối cùng — không kèm phân tích hay ghi chú lập kế hoạch.

{OUTPUT_FORMAT}"""


HYBRID_PROMPT = f"""\
[ROLE]
{ROLE_BLOCK}

[CONTEXT]
Kịch bản dùng trực tiếp cho sản xuất video ngắn trên {{platform}}, hướng tới {{audience}}.

[INPUT]
{REQUEST_BLOCK}

KIẾN THỨC SẢN XUẤT
{KNOWLEDGE_BLOCK}

[STEPS] (thực hiện nội bộ, không viết ra)
1. Xác định thông điệp cốt lõi và nhu cầu của khán giả.
2. Thiết kế mạch kể Hook → Introduction → Main Content → Conclusion → CTA.
3. Phân bổ chính xác {{duration_seconds}} giây cho các cảnh.
4. Viết lời dẫn và chỉ dẫn hình ảnh khớp nhau.
5. Kiểm tra thời lượng và mức độ tuân thủ trước khi xuất.

[CONSTRAINTS]
{DURATION_RULES}

{LANGUAGE_RULE}

[EXAMPLE]
{EXAMPLE}

[EXPECTATION]
Một kịch bản mạch lạc, hấp dẫn, sẵn sàng sản xuất với thời lượng chính xác.

{OUTPUT_FORMAT}"""


FRAMEWORK_PROMPTS: dict[str, str] = {
    "RICE": RICE_PROMPT,
    "TAG": TAG_PROMPT,
    "CARE": CARE_PROMPT,
    "RACE": RACE_PROMPT,
    "RISE": RISE_PROMPT,
    "HYBRID": HYBRID_PROMPT,
}
AVAILABLE_FRAMEWORKS = list(FRAMEWORK_PROMPTS)


REVISION_PROMPT = f"""\
Bạn đang chỉnh sửa một kịch bản video ngắn dựa trên kết quả đánh giá tự động.

=== YÊU CẦU GỐC ===
{{original_prompt}}

=== KỊCH BẢN HIỆN TẠI (phiên bản {{iteration}}, đạt {{score}}%) ===
{{current_script}}

=== CÁC VẤN ĐỀ CẦN SỬA (ưu tiên từ trên xuống) ===
{{issues}}

=== NHIỆM VỤ ===
Viết lại TOÀN BỘ kịch bản thành phiên bản mới:
- Sửa trực tiếp từng vấn đề ở trên.
- Giữ lại những phần đang tốt (ý tưởng, hình ảnh, câu chữ hay).
- Không giải thích những gì đã sửa.

{DURATION_RULES}

{OUTPUT_FORMAT}"""


def _render(template: str, context: dict) -> str:
    text = template.format(**context)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_prompt(framework: str, context: dict) -> str:
    if framework not in FRAMEWORK_PROMPTS:
        raise ValueError(f"Unknown framework: {framework}. Available: {AVAILABLE_FRAMEWORKS}")
    return _render(FRAMEWORK_PROMPTS[framework], context)


def build_revision_prompt(framework: str, context: dict, current_script: str,
                          issues: list[str], iteration: int, score: float) -> str:
    issues_text = "\n".join(f"{i}. {issue}" for i, issue in enumerate(issues, 1)) \
        or "Không có lỗi nghiêm trọng — hãy nâng chất lượng hook, lời dẫn và CTA."
    return _render(REVISION_PROMPT, {
        **context,
        "original_prompt": build_prompt(framework, context),
        "current_script": current_script,
        "issues": issues_text,
        "iteration": iteration,
        "score": score,
    })
