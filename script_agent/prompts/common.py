"""Prompt building blocks shared by every framework.

Keeping hard constraints (language, format, timing) identical across
frameworks makes the benchmark a fair comparison of *prompt structure*.
"""

from __future__ import annotations

from script_agent import config
from script_agent.schemas import ScriptRequest

LANGUAGE_RULE = """\
NGÔN NGỮ ĐẦU RA
Toàn bộ nội dung kịch bản (Visual/Action và Dialogue/Narration) phải viết bằng tiếng Việt,
kể cả khi chủ đề hoặc dữ liệu đầu vào là tiếng Anh. Chỉ giữ nguyên tiếng Anh cho tên riêng,
thương hiệu hoặc thuật ngữ kỹ thuật không có bản dịch tự nhiên."""

OUTPUT_FORMAT = """\
ĐỊNH DẠNG BẮT BUỘC
Giữ nguyên các nhãn tiếng Anh "Scene", "Visual/Action:", "Dialogue/Narration:" để hệ thống đọc tự động.

Scene N — MM:SS–MM:SS
Visual/Action:
<hình ảnh, góc quay, chuyển động, chữ trên màn hình>
Dialogue/Narration:
<lời sẽ được đọc thành tiếng — không ghi chú đạo diễn trong phần này>

- Không dùng markdown (không **, #, bảng, gạch đầu dòng cho nhãn).
- Không thêm tiêu đề, lời chào, giải thích hay ghi chú bên ngoài các cảnh."""

DURATION_RULES = """\
QUY TẮC THỜI LƯỢNG
- Cảnh đầu tiên bắt đầu tại 00:00; cảnh cuối cùng kết thúc CHÍNH XÁC tại {end_timestamp} ({duration_seconds} giây).
- Mỗi cảnh bắt đầu đúng tại thời điểm cảnh trước kết thúc: không hở, không chồng lấn.
- Tổng lời dẫn khoảng {words_min}–{words_max} tiếng (âm tiết), tương đương tốc độ đọc tự nhiên ~{wps_target} tiếng/giây.
- Lượng lời dẫn của từng cảnh phải tương xứng với độ dài cảnh đó."""

EXAMPLE = """\
VÍ DỤ ĐỊNH DẠNG (chủ đề khác — chỉ để tham khảo cấu trúc và mức độ chi tiết, KHÔNG sao chép nội dung)

Scene 1 — 00:00–00:04
Visual/Action:
Cận cảnh cốc nước đổ tràn trên bàn làm việc. Chữ lớn hiện giữa màn hình: "Bạn đang uống nước SAI cách?"
Dialogue/Narration:
Ngày nào bạn cũng uống nước, nhưng có chắc là đúng cách không?

Scene 2 — 00:04–00:12
Visual/Action:
Hoạt hình cơ thể người, vạch mực nước tụt dần. Biểu tượng mệt mỏi và đau đầu bật lên theo nhịp lời dẫn.
Dialogue/Narration:
Cơ thể mất nước chỉ hai phần trăm thôi là bạn đã thấy mệt mỏi, khó tập trung và hay đau đầu."""

SYSTEM_PROMPT = f"""\
Bạn là biên kịch chính của một hệ thống sản xuất video ngắn chuyên nghiệp.

QUY TẮC CHUNG
- Tuân thủ chính xác mọi yêu cầu rõ ràng của người dùng; chỉ tập trung vào chủ đề được yêu cầu.
- Điều chỉnh giọng văn, từ vựng và nhịp độ theo nền tảng và khán giả mục tiêu.
- Dùng kiến thức sản xuất được cung cấp làm định hướng, nhưng không để nó ghi đè yêu cầu của người dùng.
- Không bịa số liệu, nghiên cứu hay trích dẫn cụ thể nếu không chắc chắn; ưu tiên thông tin phổ biến, chính xác.
- Với chủ đề nhạy cảm (bạo lực, sức khỏe, tâm lý...), trình bày có trách nhiệm và hướng người xem tới sự hỗ trợ phù hợp.
- Không nhắc đến prompt, framework, hướng dẫn nội bộ hay quá trình tạo nội dung.
- Chỉ trả về kịch bản hoàn chỉnh, sẵn sàng sản xuất.

{LANGUAGE_RULE}"""


def format_timestamp(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def human_duration(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    if minutes and secs:
        return f"{minutes} phút {secs} giây"
    if minutes:
        return f"{minutes} phút"
    return f"{secs} giây"


def _extra_context(request: ScriptRequest) -> str:
    lines = []
    if request.screenplay.strip():
        lines.append(f"Định hướng nội dung: {request.screenplay.strip()}")
    if request.characters:
        lines.append(f"Nhân vật: {', '.join(request.characters)}")
    if request.scenes:
        lines.append("Ý tưởng cảnh gợi ý: " + "; ".join(request.scenes))
    if not lines:
        return ""
    return "GHI CHÚ TỪ NGƯỜI DÙNG\n" + "\n".join(lines)


def build_context(request: ScriptRequest, knowledge: dict | None = None) -> dict:
    """Flatten a validated request into the placeholders used by all templates."""
    knowledge = {**config.DEFAULT_KNOWLEDGE, **(knowledge or {})}
    seconds = request.metadata.duration_seconds
    return {
        "topic": request.topic,
        "platform": request.metadata.platform,
        "audience": request.metadata.audience,
        "duration": human_duration(seconds),
        "duration_seconds": seconds,
        "end_timestamp": format_timestamp(seconds),
        "words_min": round(seconds * config.WORDS_PER_SECOND_MIN),
        "words_max": round(seconds * config.WORDS_PER_SECOND_MAX),
        "wps_target": str(config.WORDS_PER_SECOND_TARGET).replace(".", ","),
        "structure": knowledge["structure"],
        "pacing": knowledge["pacing"],
        "dialogue": knowledge["dialogue"],
        "extra_context": _extra_context(request),
    }
