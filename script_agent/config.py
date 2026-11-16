"""Central configuration. Every value here can be overridden from the CLI."""

# --- Closed-loop driver -------------------------------------------------------
TARGET_SCORE = 92.0          # % of the total score required to stop early
MAX_ITERATIONS = 5           # generate + (max_iterations - 1) revisions

# --- Generation ---------------------------------------------------------------
GENERATION_TEMPERATURE = 0.7
JUDGE_TEMPERATURE = 0.0      # deterministic grading
MAX_OUTPUT_TOKENS = 8192     # leave room for "thinking" tokens on reasoning models

# --- Duration rules -----------------------------------------------------------
MIN_DURATION_SECONDS = 15
MAX_DURATION_SECONDS = 300   # 5 minutes

# --- Narration speaking rate (Vietnamese) --------------------------------------
# Vietnamese words are mono-syllabic, so whitespace-separated tokens ~= syllables.
# A natural voice-over pace is roughly 150-200 syllables/minute.
WORDS_PER_SECOND_MIN = 2.2
WORDS_PER_SECOND_TARGET = 2.8
WORDS_PER_SECOND_MAX = 3.6

# --- Default production knowledge (acts as a tiny "knowledge base") -----------
DEFAULT_KNOWLEDGE = {
    "structure": "Hook -> Introduction -> Main Content -> Conclusion -> CTA",
    "pacing": (
        "Nhịp nhanh; đổi hình ảnh mỗi 3–8 giây; Hook nằm trong 3–5 giây đầu; "
        "mỗi cảnh truyền tải đúng một ý."
    ),
    "dialogue": (
        "Giọng văn tự nhiên như đang nói chuyện, câu ngắn, dùng ngôn ngữ phù hợp "
        "với khán giả; tránh thuật ngữ khó nếu không giải thích."
    ),
}
