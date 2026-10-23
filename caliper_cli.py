#!/usr/bin/env python3
"""caliper_cli.py

Universal Sewing Machine Setup & Calibration Agent CLI.
Execution entrypoint matching the course pattern:
- Runs multi-provider ReAct loop (Ollama, Gemini, Deterministic Fallback)
- Prints explicit step-by-step trace: [step N] REASONING -> TOOL CALL -> OBSERVATION -> ANSWER
- Outputs final machine dial readout (Tension, Stitch Length, Width, Needle, Foot)

Usage Examples:
  python caliper_cli.py "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"
  python caliper_cli.py --defect "Severe bird-nesting on underside of Singer 4423"
  python caliper_cli.py --safety "14oz denim flat-felled seam with 70/10 needle on Brother SM3701"
  python caliper_cli.py --provider deterministic "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from caliper.agent import MAX_STEPS, AgentResult, CaliperAgent, run_agent


def format_step_trace(step_info: dict) -> str:
    """Formats a single trace step into the course-standard REASONING -> TOOL CALL -> OBSERVATION -> ANSWER layout."""
    step_num = step_info.get("step", 1)
    thought = step_info.get("thought")
    tool_name = step_info.get("tool_name")
    tool_args = step_info.get("tool_args")
    obs = step_info.get("observation")
    answer = step_info.get("answer")

    lines = [f"\n[step {step_num}]"]

    if thought:
        lines.append(f"  REASONING : {thought.strip()}")

    if tool_name:
        lines.append(f"  TOOL CALL : {tool_name}({tool_args})")

    if obs:
        lines.append("  OBSERVATION:")
        for line in obs.strip().splitlines():
            lines.append(f"    {line}")

    if answer:
        lines.append("  ANSWER    :")
        for line in answer.strip().splitlines():
            lines.append(f"    {line}")

    return "\n".join(lines)


def print_dial_readout(dials: dict, machine_context: dict) -> None:
    """Prints the final calibrated visual dial settings readout."""
    m_name = (
        f"{machine_context.get('brand', '')} {machine_context.get('model_name', '')}".strip()
        or "Universal Sewing Machine"
    )

    tension_str = f"{dials.get('tension'):.1f}" if dials.get("tension") is not None else "4.0 (Default)"
    len_str = f"{dials.get('stitch_length'):.1f} mm" if dials.get("stitch_length") is not None else "2.5 mm"
    wid_str = f"{dials.get('stitch_width'):.1f} mm" if dials.get("stitch_width") is not None else "0.0 mm"
    stitch_type = dials.get("stitch_type") or "Straight"
    needle_str = dials.get("needle") or "80/12 Universal"
    foot_str = dials.get("foot") or "Standard J / All-purpose"

    print("\n" + "=" * 78)
    print(f"CALIPER PHYSICAL MACHINE DIAL READOUT [{m_name}]")
    print("=" * 78)
    print(f"  Upper Tension Dial Setting : {tension_str}")
    print(f"  Stitch Length Knob / Dial  : {len_str}")
    print(f"  Stitch Width Knob / Dial   : {wid_str}")
    print(f"  Stitch Selection Pattern   : {stitch_type}")
    print(f"  Needle Gauge & System      : {needle_str}")
    print(f"  Presser Foot Attachment    : {foot_str}")
    print("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Caliper: Universal Sewing Machine Setup, Calibration & Diagnostic Agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python caliper_cli.py "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"
  python caliper_cli.py --defect "Severe bird-nesting on underside of Singer 4423"
  python caliper_cli.py --safety "14oz denim flat-felled seam with 70/10 needle on Brother SM3701"
        """,
    )

    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Primary setup or calibration query string.",
    )
    parser.add_argument(
        "--defect",
        nargs="?",
        const="",
        default=None,
        help="Diagnose a stitch defect (e.g. 'Severe bird-nesting on underside of Singer 4423').",
    )
    parser.add_argument(
        "--safety",
        nargs="?",
        const="",
        default=None,
        help="Audit sewing safety constraints (e.g. '14oz denim flat-felled seam with 70/10 needle on Brother SM3701').",
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("PROVIDER", "auto"),
        choices=["auto", "ollama", "gemini", "deterministic", "fallback"],
        help="Agent provider backend: 'auto', 'ollama', 'gemini', or 'deterministic' (default: auto).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("MODEL"),
        help="Model identifier override (e.g. 'llama3.1:latest', 'qwen2.5:0.5b', 'gemini-2.5-flash').",
    )
    parser.add_argument(
        "--machine",
        default=None,
        help="Explicit sewing machine model name or machine_id override.",
    )

    args = parser.parse_args()

    # Determine goal and operational mode
    defect_mode = False
    safety_mode = False

    if args.defect is not None:
        defect_mode = True
        goal = args.defect if args.defect else args.query
    elif args.safety is not None:
        safety_mode = True
        goal = args.safety if args.safety else args.query
    else:
        goal = args.query

    if not goal.strip():
        # Default prompt if none provided
        goal = "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"

    print("=" * 78)
    print("CALIPER UNIVERSAL SEWING MACHINE SETUP & CALIBRATION AGENT")
    print(f"Goal: {goal}")
    print(f"Provider: {args.provider} | Model: {args.model or 'default'} | Stop Condition: MAX_STEPS = {MAX_STEPS}")
    print("=" * 78)

    agent = CaliperAgent(provider=args.provider, model=args.model)
    result = agent.run(
        goal=goal,
        defect_mode=defect_mode,
        safety_mode=safety_mode,
        machine_override=args.machine,
    )

    # Print execution trace
    for step_info in result.trace:
        print(format_step_trace(step_info))

    # Print summary dial readout
    print_dial_readout(result.dials, result.machine_context)

    return 0


if __name__ == "__main__":
    sys.exit(main())
