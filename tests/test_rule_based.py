from script_agent.evaluators.rule_based import HARD_MAX, evaluate_rule_based, parse_scenes

CTX_60 = {"duration_seconds": 60}


def test_good_script_gets_full_hard_score(good_script):
    r = evaluate_rule_based(CTX_60, good_script)
    assert r["scene_count"] == 4
    assert r["duration_exact"] and r["timeline_valid"]
    assert r["hard_score"] == HARD_MAX, r["issues"]
    assert r["issues"] == []


def test_markdown_formatting_is_tolerated(good_script):
    md = (good_script
          .replace("Scene ", "**Scene ")
          .replace("Visual/Action:", "**Visual/Action:**")
          .replace("Dialogue/Narration:", "**Dialogue/Narration:**"))
    scenes = parse_scenes(md)
    assert len(scenes) == 4
    assert all(s.visual and s.dialogue for s in scenes)


def test_inline_labels_and_short_timestamps():
    script = ("Scene 1 — 0:00–0:10\nVisual/Action: A\nDialogue/Narration: một hai ba\n"
              "Scene 2 - 0:10 - 0:30\nVisual/Action: B\nDialogue/Narration: bốn năm\n")
    scenes = parse_scenes(script)
    assert [(s.start, s.end) for s in scenes] == [(0, 10), (10, 30)]
    assert scenes[0].dialogue == "một hai ba" and scenes[0].words == 3


def test_shot_labels_inside_visual_are_not_scene_headers(good_script):
    # Seen in a real Gemini run: sub-shots written as "Cảnh 1: ..." inside Visual/Action.
    script = good_script.replace(
        "Chuyển cảnh nhanh: nhóm bạn",
        "Cảnh 1: nhóm bạn thì thầm.\nCảnh 2: nhóm bạn")
    r = evaluate_rule_based(CTX_60, script)
    assert r["breakdown"]["format"] == 5.0, r["issues"]


def test_wrong_end_time_is_penalised(good_script):
    r = evaluate_rule_based(CTX_60, good_script.replace("00:45–01:00", "00:45–00:55"))
    assert not r["duration_exact"]
    assert r["duration_actual"] == 55
    assert r["breakdown"]["duration"] < 15
    assert any("01:00" in issue for issue in r["issues"])


def test_gap_and_overlap_are_reported(good_script):
    gap = good_script.replace("Scene 3 — 00:20–00:45", "Scene 3 — 00:22–00:45")
    r = evaluate_rule_based(CTX_60, gap)
    assert not r["timeline_valid"]
    assert any("khoảng hở" in i for i in r["issues"])

    overlap = good_script.replace("Scene 3 — 00:20–00:45", "Scene 3 — 00:18–00:45")
    r = evaluate_rule_based(CTX_60, overlap)
    assert any("chồng lấn" in i for i in r["issues"])


def test_missing_dialogue_is_reported():
    script = ("Scene 1 — 00:00–00:30\nVisual/Action:\nCảnh mở đầu\n"
              "Scene 2 — 00:30–01:00\nVisual/Action:\nCảnh kết\nDialogue/Narration:\nlời\n")
    r = evaluate_rule_based(CTX_60, script)
    assert r["breakdown"]["completeness"] == 5.0
    assert any("Scene 1 thiếu phần Dialogue/Narration" in i for i in r["issues"])


def test_too_little_narration_lowers_speech_rate():
    sparse ="Scene 1 — 00:00–00:30\nVisual/Action:\nA\nDialogue/Narration:\nngắn thôi\n" \
             "Scene 2 — 00:30–00:45\nVisual/Action:\nB\nDialogue/Narration:\nngắn\n" \
             "Scene 3 — 00:45–01:00\nVisual/Action:\nC\nDialogue/Narration:\nhết\n"
    r = evaluate_rule_based(CTX_60, sparse)
    assert r["breakdown"]["speech_rate"] == 0
    assert any("Thêm lời dẫn" in i for i in r["issues"])


def test_unparseable_output_scores_zero():
    r = evaluate_rule_based(CTX_60, "Xin lỗi, tôi không thể giúp việc này.")
    assert r["hard_score"] == 0
    assert r["scene_count"] == 0
