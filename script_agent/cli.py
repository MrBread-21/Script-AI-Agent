"""Command-line interface.

    python -m script_agent generate  --topic "..." --duration 1 --platform TikTok --audience "..."
    python -m script_agent benchmark --cases data/test_cases.json --frameworks RACE TAG
    python -m script_agent prompt    --framework RISE --topic "..."   # preview, no API call
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from script_agent import config


def _setup(verbose: bool) -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Vietnamese output on Windows consoles
        except (AttributeError, ValueError):
            pass
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "httpcore", "openai", "groq", "google_genai", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _request_args(p: argparse.ArgumentParser, required: bool = True) -> None:
    p.add_argument("--topic", required=required, help="Video topic")
    p.add_argument("--duration", type=float, default=1, help="Length in minutes (0.5 = 30s)")
    p.add_argument("--platform", default="TikTok")
    p.add_argument("--audience", default="người xem phổ thông")
    p.add_argument("--brief", default="", help="Optional creative direction")
    p.add_argument("--characters", nargs="*", default=[])


def _provider_args(p: argparse.ArgumentParser) -> None:
    from script_agent.providers import AVAILABLE_PROVIDERS

    p.add_argument("--provider", default="gemini", choices=AVAILABLE_PROVIDERS)
    p.add_argument("--model", default=None, help="Override the provider's default model")
    p.add_argument("--judge-provider", default=None, choices=AVAILABLE_PROVIDERS,
                   help="Use a different LLM as judge (reduces self-preference bias)")
    p.add_argument("--judge-model", default=None)
    p.add_argument("--max-iterations", type=int, default=config.MAX_ITERATIONS)
    p.add_argument("--target", type=float, default=config.TARGET_SCORE, help="Target score in %%")
    p.add_argument("--no-system-prompt", action="store_true")
    p.add_argument("--out", default="outputs", help="Output directory")


def _build_payload(args) -> dict:
    return {
        "topic": args.topic,
        "screenplay": args.brief,
        "characters": args.characters,
        "metadata": {"platform": args.platform, "audience": args.audience,
                     "duration": args.duration},
    }


def _providers(args):
    from script_agent.providers import get_provider

    provider = get_provider(args.provider, model=args.model)
    judge = None
    if args.judge_provider or args.judge_model:
        judge = get_provider(args.judge_provider or args.provider, model=args.judge_model)
    return provider, judge


def _frameworks(value: list[str]) -> list[str]:
    from script_agent.prompts import AVAILABLE_FRAMEWORKS

    if [v.upper() for v in value] == ["ALL"]:
        return AVAILABLE_FRAMEWORKS
    unknown = [v for v in value if v.upper() not in AVAILABLE_FRAMEWORKS]
    if unknown:
        raise SystemExit(f"Unknown framework(s) {unknown}. Available: {AVAILABLE_FRAMEWORKS} or ALL")
    return [v.upper() for v in value]


def cmd_generate(args) -> int:
    from script_agent.driver import run_driver
    from script_agent.report import save_result

    provider, judge = _providers(args)
    payload = _build_payload(args)
    exit_code = 0
    for fw in _frameworks(args.framework):
        result = run_driver(payload, framework=fw, provider=provider, judge_provider=judge,
                            target_score=args.target, max_iterations=args.max_iterations,
                            use_system_prompt=not args.no_system_prompt)
        if result["status"] == "failed":
            print(f"\n[{fw}] FAILED: {result.get('errors') or result.get('error')}")
            exit_code = 1
            continue
        md, js = save_result(args.topic, result, args.out)
        print(f"\n{'=' * 70}\n[{fw}] {result['status'].upper()} — {result['percentage']}% "
              f"(iteration {result['best_iteration']}/{result['iterations']})\n{'=' * 70}")
        print(result["script"])
        print(f"\nSaved: {md}\n       {js}")
    return exit_code


def cmd_benchmark(args) -> int:
    from script_agent.benchmark import run_benchmark, save_benchmark, summarize, summary_table

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    if args.ids:
        cases = [c for c in cases if c["id"] in args.ids]
    provider, judge = _providers(args)
    frameworks = _frameworks(args.frameworks)
    results = run_benchmark(cases, frameworks, provider, judge_provider=judge,
                            target_score=args.target, max_iterations=args.max_iterations,
                            use_system_prompt=not args.no_system_prompt)
    summary = summarize(results)
    meta = {"generator": f"{provider.name}/{provider.model}",
            "judge": f"{(judge or provider).name}/{(judge or provider).model}",
            "test_cases": len(cases), "max_iterations": args.max_iterations,
            "target": args.target}
    json_path, md_path = save_benchmark(results, summary, args.out, meta)
    print("\n" + summary_table(summary))
    print(f"\nSaved: {md_path}\n       {json_path}")
    return 0


def cmd_prompt(args) -> int:
    from script_agent.prompts import SYSTEM_PROMPT, build_context, build_prompt
    from script_agent.validators import validate_input

    v = validate_input(_build_payload(args))
    if not v.valid:
        print("\n".join(v.errors))
        return 1
    context = build_context(v.data)
    for fw in _frameworks(args.framework):
        print(f"\n{'=' * 30} {fw} {'=' * 30}\n")
        if args.system:
            print(f"--- SYSTEM ---\n{SYSTEM_PROMPT}\n--- USER ---")
        print(build_prompt(fw, context))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="script-agent",
                                     description="Closed-loop short-video script generator")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="Generate a script with the closed loop")
    _request_args(g)
    g.add_argument("--framework", nargs="+", default=["RACE"], help="Framework(s) or ALL")
    _provider_args(g)
    g.set_defaults(func=cmd_generate)

    b = sub.add_parser("benchmark", help="Compare frameworks over test cases")
    b.add_argument("--cases", default="data/test_cases.json")
    b.add_argument("--ids", nargs="*", help="Only run these test-case ids")
    b.add_argument("--frameworks", nargs="+", default=["ALL"])
    _provider_args(b)
    b.set_defaults(func=cmd_benchmark)

    pr = sub.add_parser("prompt", help="Print the rendered prompt (no API call)")
    _request_args(pr)
    pr.add_argument("--framework", nargs="+", default=["RACE"])
    pr.add_argument("--system", action="store_true", help="Also print the system prompt")
    pr.set_defaults(func=cmd_prompt)

    args = parser.parse_args(argv)
    _setup(args.verbose)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # surface provider/config errors without a traceback
        logging.getLogger(__name__).debug("fatal", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
