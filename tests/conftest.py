import json

import pytest

GOOD_SCRIPT = """\
Scene 1 — 00:00–00:05
Visual/Action:
Cận cảnh một học sinh ngồi một mình ở góc lớp, điện thoại rung liên tục.
Dialogue/Narration:
Bạo lực học đường không chỉ là những trận đánh nhau mà bạn vẫn nghĩ.

Scene 2 — 00:05–00:20
Visual/Action:
Chuyển cảnh nhanh: nhóm bạn thì thầm chỉ trỏ, màn hình chat tràn ngập tin nhắn chế giễu.
Dialogue/Narration:
Nó còn là những lời chế giễu, sự cô lập và cả những tin nhắn ác ý trên mạng xã hội. Những vết thương này không
nhìn thấy được nhưng có thể theo một người rất lâu, khiến họ sợ đến trường mỗi ngày.

Scene 3 — 00:20–00:45
Visual/Action:
Đồ họa ba biểu tượng: thể chất, tinh thần, trực tuyến. Mỗi biểu tượng sáng lên theo lời dẫn.
Dialogue/Narration:
Hãy nhớ ba dấu hiệu quan trọng. Một là bạn bị đánh hoặc bị lấy đồ. Hai là bạn bị bêu riếu hay bị cô lập.
Ba là bạn bị đe dọa trên mạng. Nếu gặp một trong ba điều đó, đó không phải lỗi của bạn, và bạn xứng đáng được
giúp đỡ ngay lập tức từ những người lớn mà bạn tin tưởng.

Scene 4 — 00:45–01:00
Visual/Action:
Học sinh mỉm cười nói chuyện với giáo viên chủ nhiệm. Chữ trên màn hình: "Lên tiếng là dũng cảm".
Dialogue/Narration:
Hãy nói với thầy cô, bố mẹ hoặc gọi đường dây hỗ trợ trẻ em. Chia sẻ video này để bạn bè cùng biết nhé,
và theo dõi kênh để xem thêm những mẹo bảo vệ bản thân.
"""

JUDGE_JSON = json.dumps({
    "scores": {"topic_relevance": 9, "audience_fit": 9, "structure": 9, "pacing": 9,
               "dialogue": 9, "hook": 9, "CTA": 9, "coherence": 9},
    "issues": [],
})


class FakeProvider:
    """Offline stand-in for an LLM. Replies are popped from a queue; the
    judge prompt (detected by its header) always gets ``judge_reply``."""

    name = "fake"

    def __init__(self, replies, judge_reply=JUDGE_JSON, model="fake-model"):
        self.replies = list(replies)
        self.judge_reply = judge_reply
        self.model = model
        self.prompts = []

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_output_tokens=4096):
        self.prompts.append(prompt)
        if prompt.startswith("Bạn là giám khảo"):
            text = self.judge_reply
        else:
            text = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        return {"text": text, "latency": 0.01, "model": self.model, "provider": self.name,
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}}


@pytest.fixture
def good_script():
    return GOOD_SCRIPT


@pytest.fixture
def payload():
    return {
        "topic": "Bạo lực học đường",
        "metadata": {"platform": "YouTube Shorts", "audience": "học sinh THCS", "duration": 1},
    }


@pytest.fixture
def fake_provider_cls():
    return FakeProvider
