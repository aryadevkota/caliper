"""
Caliper: Universal Sewing Machine Setup & Calibration Agent
Localhost Web Application (FastAPI & Uvicorn)

Milestone I Working Prototype
Aesthetic Craft-Inspired Atelier UI with Tactile Rotary Dials & Rolling Yarn Loader
"""

import os
import sys
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

from caliper.hardware_db import list_all_machines, get_machine, load_machines
from caliper.agent import run_agent, extract_dial_settings
from caliper.guardrails import evaluate_input, MAX_INPUT_LENGTH

# Pre-load the 50-machine hardware database
load_machines()

app = FastAPI(title="Caliper: Sewing Machine Calibration Companion")

# Mount static directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

class CalibrateRequest(BaseModel):
    message: str
    machine_id: Optional[str] = "brother_sm3701"
    provider: Optional[str] = "auto"
    api_key: Optional[str] = ""
    history: Optional[List[Dict[str, str]]] = []
    current_dials: Optional[Dict[str, Any]] = None

@app.get("/assets/caliper_logo.png")
async def get_logo():
    logo_path = os.path.join(ASSETS_DIR, "caliper_logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "Logo not found"})

@app.get("/assets/caliper_logo.svg")
async def get_logo_svg():
    logo_path = os.path.join(ASSETS_DIR, "caliper_logo.svg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/svg+xml")
    return JSONResponse(status_code=404, content={"error": "Logo not found"})

INDEX_FILE = os.path.join(TEMPLATES_DIR, "index.html")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/machines")
async def get_all_machines():
    """Return all 50 verified sewing machine hardware profiles."""
    machines = list_all_machines()
    return {"count": len(machines), "machines": machines}

@app.get("/api/machine/{machine_id}")
async def get_machine_specs(machine_id: str):
    """Return hardware specifications for a specific sewing machine."""
    specs = get_machine(machine_id)
    if not specs:
        return JSONResponse(status_code=404, content={"error": f"Machine '{machine_id}' not found"})
    return specs

@app.post("/api/calibrate")
async def run_calibration(req: CalibrateRequest):
    """Run Caliper Agent with multi-provider routing and return reasoning trace + dial values."""
    query = req.message.strip()
    if not query:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty"})

    # Attach machine context if not in query
    specs = get_machine(req.machine_id or "brother_sm3701") or {}
    machine_name = f"{specs.get('brand', '')} {specs.get('model_name', '')}".strip()

    # Pre-flight input evaluation on raw query and history user turns BEFORE appending machine context
    guardrail_decision = evaluate_input(query)
    if guardrail_decision.allowed and req.history:
        for turn in req.history:
            if isinstance(turn, dict) and turn.get("role") == "user":
                h_content = (turn.get("content") or "").strip()
                if h_content:
                    h_dec = evaluate_input(h_content)
                    if not h_dec.allowed:
                        guardrail_decision = h_dec
                        break
    if not guardrail_decision.allowed:
        dials = {
            "tension": specs.get("tension_default", 4.0),
            "stitch_length": 2.5,
            "stitch_width": 0.0,
            "needle": "Default / Baseline",
            "foot": "Standard Presser Foot",
            "stitch_type": "Straight",
        }
        safety = {
            "severity": "WARNING",
            "message": "Request blocked by Caliper security & safety guardrails.",
        }
        return {
            "final_answer": guardrail_decision.refusal_message,
            "trace": [{
                "step": 1,
                "thought": f"Guardrail intercepted {guardrail_decision.category}: {guardrail_decision.reason}",
                "tool_name": "guardrail_check",
                "tool_args": {"category": guardrail_decision.category},
                "observation": "BLOCKED",
                "answer": guardrail_decision.refusal_message,
            }],
            "dials": dials,
            "safety": safety,
            "stopped_reason": "blocked_by_guardrail",
            "machine_specs": specs,
        }

    # Safely attach machine context if not already in query without exceeding MAX_INPUT_LENGTH
    brand_keywords = ["brother", "singer", "janome", "juki", "bernette", "baby lock"]
    machine_suffix = f" on my {machine_name}" if machine_name else ""
    if machine_suffix and not any(k in query.lower() for k in brand_keywords):
        if len(query) + len(machine_suffix) <= MAX_INPUT_LENGTH:
            query_with_context = f"{query}{machine_suffix}"
        else:
            query_with_context = query
    else:
        query_with_context = query

    # Provider and model resolution
    engine_provider = "auto"
    engine_model = None

    p = (req.provider or "auto").lower()
    if "gemini" in p:
        engine_provider = "gemini"
    elif "deterministic" in p:
        engine_provider = "deterministic"
    elif "llama" in p:
        engine_provider = "ollama"
        engine_model = "llama3.1:latest"
    elif "qwen" in p:
        engine_provider = "ollama"
        engine_model = "qwen2.5:0.5b"
    else:
        engine_provider = "auto"

    api_key_clean = req.api_key.strip() if req.api_key and req.api_key.strip() else None

    # Execute Caliper Agent with strict MAX_STEPS = 6 guard and clean api_key
    result = run_agent(
        goal=query_with_context,
        provider=engine_provider,
        model=engine_model,
        max_steps=6,
        machine_override=req.machine_id,
        api_key=api_key_clean,
        history=req.history,
        current_dials=req.current_dials,
    )

    # Intercept guardrail rejections with safe baseline dials and warning status
    if result.stopped_reason == "blocked_by_guardrail":
        dials = {
            "tension": specs.get("tension_default", 4.0),
            "stitch_length": 2.5,
            "stitch_width": 0.0,
            "needle": "Default / Baseline",
            "foot": "Standard Presser Foot",
            "stitch_type": "Straight",
        }
        safety = {
            "severity": "WARNING",
            "message": "Request blocked by Caliper security & safety guardrails.",
        }
        return {
            "final_answer": result.final_answer,
            "trace": result.trace,
            "dials": dials,
            "safety": safety,
            "stopped_reason": result.stopped_reason,
            "machine_specs": specs,
        }

    # If clarifying question needed, preserve current dial positions
    if result.stopped_reason == "needs_clarification":
        curr = req.current_dials or {}
        dials = {
            "tension": curr.get("tension") if curr.get("tension") is not None else specs.get("tension_default", 4.0),
            "stitch_length": curr.get("length") if curr.get("length") is not None else curr.get("stitch_length", 2.5),
            "stitch_width": curr.get("width") if curr.get("width") is not None else curr.get("stitch_width", 0.0),
            "needle": curr.get("needle") or "Current Needle",
            "foot": curr.get("foot") or "Current Presser Foot",
            "stitch_type": curr.get("stitch_type") or "Current Stitch",
        }
        safety = {
            "severity": "SAFE",
            "message": "Awaiting fabric and setup clarification before adjusting dials.",
        }
        return {
            "final_answer": result.final_answer,
            "trace": result.trace,
            "dials": dials,
            "safety": safety,
            "stopped_reason": result.stopped_reason,
            "machine_specs": specs,
        }

    # Extract updated dials: prioritize result.dials, then trace/final_answer
    dials = result.dials if result.dials and any(result.dials.values()) else extract_dial_settings(result)

    # Fallback to specs baseline for missing dial fields
    if dials.get("tension") is None:
        dials["tension"] = specs.get("tension_default", 4.0)
    if dials.get("stitch_length") is None:
        dials["stitch_length"] = 2.5
    if dials.get("stitch_width") is None:
        dials["stitch_width"] = 0.0

    # Determine Safety Status
    safety = {"severity": "SAFE", "message": "All parameters within safe physical limits."}
    for step in result.trace:
        obs = str(step.get("observation") or "")
        if "[CRITICAL]" in obs or "CRITICAL DEFLECTION HAZARD" in obs:
            safety = {
                "severity": "CRITICAL",
                "message": "Hazard Intercepted: Fabric density exceeds needle gauge capacity. Needle upgraded to heavy Jeans needle to prevent snapping."
            }
            break
        elif "[WARNING]" in obs or "FABRIC DAMAGE HAZARD" in obs:
            safety = {
                "severity": "WARNING",
                "message": "Caution: Needle size may cause fiber damage or punch holes in delicate weave."
            }

    return {
        "final_answer": result.final_answer,
        "trace": result.trace,
        "dials": dials,
        "safety": safety,
        "stopped_reason": result.stopped_reason,
        "machine_specs": specs
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    host = "0.0.0.0" if os.environ.get("LAN") else "127.0.0.1"
    print(f"[Caliper] Starting Caliper Atelier Web Application on http://127.0.0.1:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
