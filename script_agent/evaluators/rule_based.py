"""Deterministic checks (45 points) — the "hard" production constraints.

| Check            | Points | What it measures                                         |
|------------------|-------:|----------------------------------------------------------|
| duration         |   15   | Last scene ends exactly at the requested duration        |
| timeline         |    5   | Starts at 00:00, no gaps / overlaps, valid MM:SS          |
| completeness     |   10   | Every scene has both Visual/Action and Dialogue/Narration |
| format           |    5   | Parseable "Scene N — MM:SS–MM:SS" headers, >= 3 scenes    |
| speech_rate      |   10   | Narration length fits the duration (words per second)    |
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from itertools import pairwise

from script_agent import config
from script_agent.prompts.common import format_timestamp

HARD_MAX = 45
POINTS = {"duration": 15, "timeline": 5, "completeness": 10, "format": 5, "speech_rate": 10}

_PREFIX = r"^[ \t>*_#-]*"
SCENE_HEADER_RE = re.compile(
    _PREFIX + r"(?:Scene|Cảnh)\s*(\d+)\b[^\n]*?(\d{1,2}):(\d{2})\s*[–—-]+\s*(\d{1,2}):(\d{2})",
    re.IGNORECASE | re.MULTILINE,
)
# Untimed headers: "Scene N" anywhere, but Vietnamese "Cảnh N" only when it stands
# alone on its line — "Cảnh 1: học sinh..." inside Visual/Action is a shot, not a scene.
SCENE_ANY_RE = re.compile(_PREFIX + r"(?:Scene\s*\d+|Cảnh\s*\d+[ \t*_#:.]*$)",
                          re.IGNORECASE | re.MULTILINE)
VISUAL_RE = re.compile(_PREFIX + r"Visual\s*/\s*Action[ \t*_]*:[ \t*_]*", re.IGNORECASE | re.MULTILINE)
DIALOGUE_RE = re.compile(_PREFIX + r"Dialogue\s*/\s*Narration[ \t*_]*:[ \t*_]*",
                         re.IGNORECASE | re.MULTILINE)
_DIRECTION_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass
class Scene:
    number: int
    start: int
    end: int
    visual: str
    dialogue: str
    words: int
    valid_clock: bool = True

    @property
    def length(self) -> int:
        return self.end - self.start


def _section(block: str, label_re: re.Pattern, stop_res: list[re.Pattern]) -> str:
    match = label_re.search(block)
    if not match:
        return ""
    rest = block[match.end():]
    stops = [m.start() for r in stop_res if (m := r.search(rest))]
    return rest[: min(stops)] if stops else rest


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(_DIRECTION_RE.sub(" ", text)))


def parse_scenes(script: str) -> list[Scene]:
    headers = list(SCENE_HEADER_RE.finditer(script))
    scenes = []
    for i, h in enumerate(headers):
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(script)
        block = script[h.end():block_end]
        visual = _section(block, VISUAL_RE, [DIALOGUE_RE]).strip(" \n*_\"“”")
        dialogue = _section(block, DIALOGUE_RE, [VISUAL_RE]).strip(" \n*_\"“”")
        scenes.append(Scene(
            number=int(h.group(1)),
            start=int(h.group(2)) * 60 + int(h.group(3)),
            end=int(h.group(4)) * 60 + int(h.group(5)),
            visual=visual,
            dialogue=dialogue,
            words=count_words(dialogue),
            valid_clock=int(h.group(3)) < 60 and int(h.group(5)) < 60,
        ))
    return scenes


def _ts(seconds: int) -> str:
    return format_timestamp(seconds)


def _timeline_issues(scenes: list[Scene]) -> list[str]:
    issues = []
    if scenes and scenes[0].start != 0:
        issues.append(f"Scene {scenes[0].number} phải bắt đầu tại 00:00 (đang là {_ts(scenes[0].start)}).")
    for prev, cur in pairwise(scenes):
        if cur.start != prev.end:
            kind = "khoảng hở" if cur.start > prev.end else "chồng lấn"
            issues.append(f"Có {kind} giữa Scene {prev.number} (kết thúc {_ts(prev.end)}) và "
                          f"Scene {cur.number} (bắt đầu {_ts(cur.start)}).")
    for s in scenes:
        if s.end <= s.start:
            issues.append(f"Scene {s.number} có thời gian kết thúc không sau thời gian bắt đầu.")
        if not s.valid_clock:
            issues.append(f"Scene {s.number} có mốc thời gian không hợp lệ (giây phải < 60).")
    return issues


def _speech_rate_score(wps: float) -> float:
    lo, hi = config.WORDS_PER_SECOND_MIN, config.WORDS_PER_SECOND_MAX
    if lo <= wps <= hi:
        return 1.0
    deviation = (lo - wps) / lo if wps < lo else (wps - hi) / hi
    return max(0.0, 1.0 - 2 * deviation)


def evaluate_rule_based(context: dict, script: str) -> dict:
    expected = context["duration_seconds"]
    scenes = parse_scenes(script)
    any_headers = len(SCENE_ANY_RE.findall(script))
    issues: list[str] = []

    # --- duration -------------------------------------------------------------
    actual = scenes[-1].end if scenes else 0
    exact = actual == expected and actual > 0
    compliance = 1.0 if exact else (max(0.0, 1 - abs(actual - expected) / expected) if actual else 0.0)
    if not scenes:
        issues.append("Không đọc được cảnh nào. Dùng đúng định dạng 'Scene N — MM:SS–MM:SS'.")
    elif not exact:
        issues.append(f"Cảnh cuối kết thúc tại {_ts(actual)} nhưng phải kết thúc CHÍNH XÁC tại "
                      f"{_ts(expected)}. Phân bổ lại mốc thời gian các cảnh.")

    # --- timeline -------------------------------------------------------------
    t_issues = _timeline_issues(scenes)
    issues += t_issues
    timeline_ratio = 0.0 if not scenes else max(0.0, 1 - len(t_issues) / max(len(scenes), 1))

    # --- completeness ----------------------------------------------------------
    complete = [s for s in scenes if s.visual and s.dialogue]
    for s in scenes:
        missing = [name for name, val in (("Visual/Action", s.visual), ("Dialogue/Narration", s.dialogue))
                   if not val]
        if missing:
            issues.append(f"Scene {s.number} thiếu phần {' và '.join(missing)}.")
    completeness_ratio = len(complete) / len(scenes) if scenes else 0.0

    # --- format ----------------------------------------------------------------
    if len(scenes) >= 3 and len(scenes) == any_headers:
        format_ratio = 1.0
    elif scenes:
        format_ratio = 0.5
        if len(scenes) < 3:
            issues.append("Kịch bản cần ít nhất 3 cảnh để có Hook, nội dung chính và CTA.")
        if any_headers > len(scenes):
            issues.append("Một số cảnh thiếu mốc thời gian dạng 'MM:SS–MM:SS' trong tiêu đề.")
    else:
        format_ratio = 0.0

    # --- speech rate -----------------------------------------------------------
    total_words = sum(s.words for s in scenes)
    timed = sum(max(s.length, 0) for s in scenes)
    wps = total_words / timed if timed else 0.0
    speech_ratio = _speech_rate_score(wps) if timed else 0.0
    if timed and speech_ratio < 1.0:
        lo = round(expected * config.WORDS_PER_SECOND_MIN)
        hi = round(expected * config.WORDS_PER_SECOND_MAX)
        verb = "Thêm" if wps < config.WORDS_PER_SECOND_MIN else "Rút gọn"
        issues.append(f"Lời dẫn có {total_words} tiếng cho {timed} giây ({wps:.1f} tiếng/giây). "
                      f"{verb} lời dẫn để đạt khoảng {lo}–{hi} tiếng.")
    for s in scenes:
        if s.length > 0 and s.dialogue:
            rate = s.words / s.length
            if rate > config.WORDS_PER_SECOND_MAX * 1.3:
                issues.append(f"Scene {s.number} quá nhiều lời ({s.words} tiếng trong {s.length}s) — "
                              "rút gọn lời hoặc kéo dài cảnh.")
            elif rate < config.WORDS_PER_SECOND_MIN * 0.5:
                issues.append(f"Scene {s.number} quá ít lời ({s.words} tiếng trong {s.length}s) — "
                              "thêm lời dẫn hoặc rút ngắn cảnh.")

    breakdown = {
        "duration": POINTS["duration"] * compliance,
        "timeline": POINTS["timeline"] * timeline_ratio,
        "completeness": POINTS["completeness"] * completeness_ratio,
        "format": POINTS["format"] * format_ratio,
        "speech_rate": POINTS["speech_rate"] * speech_ratio,
    }
    return {
        "hard_score": round(sum(breakdown.values()), 1),
        "hard_max": HARD_MAX,
        "breakdown": {k: round(v, 1) for k, v in breakdown.items()},
        "duration_expected": expected,
        "duration_actual": actual,
        "duration_exact": exact,
        "duration_compliance": round(compliance, 3),
        "timeline_valid": bool(scenes) and not t_issues,
        "scene_count": len(scenes),
        "narration_words": total_words,
        "words_per_second": round(wps, 2),
        "issues": issues,
        "scenes": [{k: v for k, v in asdict(s).items() if k not in ("visual", "dialogue")}
                   for s in scenes],
    }
