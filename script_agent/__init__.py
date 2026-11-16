"""AI Script Agent — closed-loop short-video script generation with LLMs.

Pipeline: validate input -> build framework prompt -> generate -> evaluate
(rule-based + LLM-as-a-judge) -> revise with feedback -> repeat until the
target score is reached or the iteration budget runs out.
"""

from script_agent.driver import run_driver
from script_agent.schemas import ScriptRequest

__all__ = ["run_driver", "ScriptRequest"]
__version__ = "1.0.0"
