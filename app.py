"""
Caliper: Universal Sewing Machine Setup & Calibration Agent
Localhost Web Application (FastAPI & Uvicorn)

Milestone I Working Prototype
Aesthetic Craft-Inspired Atelier UI with Tactile Rotary Dials & Rolling Yarn Loader
"""

import os
import sys
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from caliper.hardware_db import list_all_machines, get_machine, load_machines
from caliper.agent import run_agent, extract_dial_settings

# Pre-load the 50-machine hardware database
load_machines()

app = FastAPI(title="Caliper: Sewing Machine Calibration Companion")

# Mount static and assets directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
NEWBRANDKIT_DIR = os.path.join(BASE_DIR, "newbrandkit")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/newbrandkit", StaticFiles(directory=NEWBRANDKIT_DIR), name="newbrandkit")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class CalibrateRequest(BaseModel):
    message: str
    machine_id: Optional[str] = "brother_sm3701"
    provider: Optional[str] = "auto"
    api_key: Optional[str] = ""

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
    
    brand_keywords = ["brother", "singer", "janome", "juki", "bernette", "baby lock"]
    if machine_name and not any(k in query.lower() for k in brand_keywords):
        query_with_context = f"{query} on my {machine_name}"
    else:
        query_with_context = query

    # Provider and model resolution
    engine_provider = "auto"
    engine_model = None

    p = (req.provider or "auto").lower()
    if "gemini" in p:
        engine_provider = "gemini"
        if req.api_key and req.api_key.strip():
            os.environ["GEMINI_API_KEY"] = req.api_key.strip()
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

    # Execute Caliper Agent with strict MAX_STEPS = 6 guard
    result = run_agent(
        goal=query_with_context,
        provider=engine_provider,
        model=engine_model,
        max_steps=6,
    )

    # Extract updated dials
    dials = extract_dial_settings(result.final_answer)

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
