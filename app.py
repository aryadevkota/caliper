"""
Caliper: Universal Sewing Machine Setup & Calibration Agent
Localhost Web Interface (Gradio 6.x)

Milestone I Working Prototype
Run locally:
    python app.py
    # Opens at http://127.0.0.1:7860
"""
import os
import sys
import base64
import gradio as gr

from caliper.hardware_db import list_all_machines, get_machine, load_machines
from caliper.agent import run_caliper_agent, extract_dial_settings
from caliper.ui_helpers import render_machine_card, render_dial_dashboard, format_trace_html

# Ensure database is loaded
load_machines()

# Build machine choices for dropdown
all_machines = list_all_machines()
MACHINE_CHOICES = [
    (f"{m['brand']} {m['model_name']} ({m['category']})", m["machine_id"])
    for m in all_machines
]
# Default machine: Brother SM3701
DEFAULT_MACHINE_ID = "brother_sm3701" if any(m["machine_id"] == "brother_sm3701" for m in all_machines) else all_machines[0]["machine_id"]

# Load logo as base64 for reliable local display
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "caliper_logo.png")
LOGO_HTML = ""
if os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as f:
            b64_logo = base64.b64encode(f.read()).decode("utf-8")
            LOGO_HTML = f'<img src="data:image/png;base64,{b64_logo}" alt="Caliper Logo" style="height:48px; max-width:220px; object-fit:contain; margin-right:16px; vertical-align:middle;" />'
    except Exception:
        LOGO_HTML = ""

def get_initial_ui_state(machine_id: str):
    specs = get_machine(machine_id) or {}
    card = render_machine_card(specs)
    default_dials = {
        "tension": specs.get("tension_default", 4.0),
        "stitch_length": 2.5,
        "stitch_width": 0.0,
        "needle": f"{specs.get('min_needle_size_eu', 75)}/11 Universal",
        "foot": specs.get("presser_foot_system", "Snap-on (Low Shank)"),
        "stitch_type": "Straight",
    }
    dashboard = render_dial_dashboard(specs, default_dials, {"severity": "SAFE", "message": "Baseline hardware ready."})
    return card, dashboard, default_dials

def on_machine_change(machine_id: str):
    specs = get_machine(machine_id) or {}
    card = render_machine_card(specs)
    default_dials = {
        "tension": specs.get("tension_default", 4.0),
        "stitch_length": 2.5,
        "stitch_width": 0.0,
        "needle": f"{specs.get('min_needle_size_eu', 75)}/11 Universal",
        "foot": specs.get("presser_foot_system", "Snap-on (Low Shank)"),
        "stitch_type": "Straight",
    }
    dashboard = render_dial_dashboard(specs, default_dials, {"severity": "SAFE", "message": f"{specs.get('brand', '')} {specs.get('model_name', '')} chassis loaded."})
    return card, dashboard, default_dials

def handle_user_message(message: str, history: list, machine_id: str, provider: str, gemini_key: str, current_dials: dict):
    if not message or not message.strip():
        return history, render_dial_dashboard(get_machine(machine_id), current_dials), "", current_dials
    
    # Prefix machine context if not in query
    query = message.strip()
    specs = get_machine(machine_id) or {}
    machine_name = f"{specs.get('brand', '')} {specs.get('model_name', '')}".strip()
    
    # If the user didn't mention any machine model, attach the currently selected machine
    if machine_name and not any(k in query.lower() for k in ["brother", "singer", "janome", "juki", "bernette", "baby lock"]):
        query_with_context = f"{query} on my {machine_name}"
    else:
        query_with_context = query
        
    # Provider mapping
    engine_provider = "auto"
    engine_model = None
    if "Gemini" in provider:
        engine_provider = "gemini"
        if gemini_key and gemini_key.strip():
            os.environ["GEMINI_API_KEY"] = gemini_key.strip()
    elif "Deterministic" in provider:
        engine_provider = "deterministic"
    elif "llama3.1" in provider:
        engine_provider = "ollama"
        engine_model = "llama3.1:latest"
    elif "qwen2.5" in provider:
        engine_provider = "ollama"
        engine_model = "qwen2.5:0.5b"
    else:
        engine_provider = "auto"
        
    # Execute Caliper Agent
    result = run_caliper_agent(
        goal=query_with_context,
        provider=engine_provider,
        model=engine_model,
        max_steps=6,
    )
    
    # Extract updated dials
    updated_dials = extract_dial_settings(result.final_answer)
    # Merge with previous dials if missing
    for k, v in (current_dials or {}).items():
        if k not in updated_dials or updated_dials[k] is None:
            updated_dials[k] = v
            
    # Check for safety warnings in observations or answer
    safety_status = {"severity": "SAFE", "message": "Parameters verified safe."}
    for step in result.trace:
        obs = str(step.get("observation") or "")
        if "[CRITICAL]" in obs or "CRITICAL DEFLECTION HAZARD" in obs:
            safety_status = {
                "severity": "CRITICAL",
                "message": "Hazard Intercepted: Fabric density exceeds needle gauge capacity. Needle upgraded to prevent snapping.",
            }
            break
        elif "[WARNING]" in obs:
            safety_status = {
                "severity": "WARNING",
                "message": "Caution: Fabric fiber puncture risk detected.",
            }
            
    # Format trace
    trace_html = format_trace_html(result.trace)
    
    # Format dashboard
    dashboard_html = render_dial_dashboard(specs, updated_dials, safety_status)
    
    # Append to chatbot history
    new_history = list(history or [])
    new_history.append({"role": "user", "content": message})
    new_history.append({"role": "assistant", "content": result.final_answer})
    
    return new_history, dashboard_html, trace_html, updated_dials

# Create Gradio Blocks App
custom_css = """
body, .gradio-container {
    background-color: #0b0f17 !important;
    color: #e2e8f0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}
.header-bar {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.badge-pill {
    background: rgba(168, 28, 37, 0.2);
    border: 1px solid #a81c25;
    color: #fca5a5;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 20px;
    text-transform: uppercase;
}
button.primary-btn {
    background: #a81c25 !important;
    color: white !important;
    border: none !important;
}
button.primary-btn:hover {
    background: #8b131b !important;
}
"""

with gr.Blocks(title="Caliper: Universal Sewing Machine Setup Agent") as demo:
    # Header
    with gr.Row():
        gr.HTML(f"""
        <div class="header-bar" style="background:#111827; border:1px solid #1f2937; border-radius:12px; padding:16px 20px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; width:100%;">
          <div style="display:flex; align-items:center;">
            {LOGO_HTML}
            <div>
              <h1 style="font-size:22px; margin:0; font-weight:800; color:#ffffff; letter-spacing:-0.02em;">Caliper</h1>
              <p style="font-size:12px; margin:2px 0 0 0; color:#94a3b8;">Universal Sewing Machine Setup & Calibration Agent · Milestone I Prototype</p>
            </div>
          </div>
          <div style="display:flex; gap:8px;">
            <span style="background:rgba(168, 28, 37, 0.25); border:1px solid #a81c25; color:#fca5a5; font-size:10px; font-weight:700; padding:4px 8px; border-radius:12px; text-transform:uppercase;">50 Hardware Profiles</span>
            <span style="background:rgba(16, 185, 129, 0.15); border:1px solid #10b981; color:#6ee7b7; font-size:10px; font-weight:700; padding:4px 8px; border-radius:12px; text-transform:uppercase;">Max-Steps: 6 Guard</span>
            <span style="background:rgba(59, 130, 246, 0.15); border:1px solid #3b82f6; color:#93c5fd; font-size:10px; font-weight:700; padding:4px 8px; border-radius:12px; text-transform:uppercase;">Localhost</span>
          </div>
        </div>
        """)

    # Top Control Bar
    with gr.Row():
        with gr.Column(scale=2):
            machine_dropdown = gr.Dropdown(
                label="Selected Sewing Machine Chassis (50 Verified Hardware Models)",
                choices=MACHINE_CHOICES,
                value=DEFAULT_MACHINE_ID,
                interactive=True,
            )
        with gr.Column(scale=1):
            provider_dropdown = gr.Dropdown(
                label="Inference Provider",
                choices=[
                    "Auto (Local Ollama / Fallback)",
                    "Local Ollama (llama3.1:latest)",
                    "Local Ollama (qwen2.5:0.5b)",
                    "Deterministic ReAct Engine (Fast / Offline)",
                    "Google Gemini 2.5 Flash",
                ],
                value="Auto (Local Ollama / Fallback)",
                interactive=True,
            )
        with gr.Column(scale=1):
            gemini_key_box = gr.Textbox(
                label="Gemini API Key (Optional)",
                placeholder="AIzaSy...",
                type="password",
                interactive=True,
            )

    # Machine Specs Summary Card
    init_specs = get_machine(DEFAULT_MACHINE_ID) or {}
    init_card, init_dash, init_dials = get_initial_ui_state(DEFAULT_MACHINE_ID)
    
    machine_card_html = gr.HTML(init_card)
    
    # State tracking
    dials_state = gr.State(init_dials)

    # Main Workspace (2 Columns)
    with gr.Row():
        # Left Column: Chat and Prompts
        with gr.Column(scale=6):
            gr.Markdown("### 💬 Calibration & Defect Diagnostic Assistant")
            
            # Scenario Preset Buttons
            gr.Markdown("**Quick Scenarios from Proposal:**")
            with gr.Row():
                btn_scen1 = gr.Button("🧵 Scenario 1: Stretch Jersey (Brother SM3701)", size="sm")
                btn_scen2 = gr.Button("⚠️ Scenario 2: Bird-nesting Defect (Singer 4423)", size="sm")
                btn_scen3 = gr.Button("🛡️ Scenario 3: 14oz Denim Hazard (Brother SM3701)", size="sm")
                
            chatbot = gr.Chatbot(
                label="Caliper Agent Session",
                height=420,
                show_label=False,
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Enter your fabric, needle, seam, or defect description:",
                    placeholder="e.g. 'Sewing 200 GSM 4-way polyester spandex jersey knit side seam' or 'Underside thread looping bird-nesting'",
                    scale=5,
                    lines=1,
                )
                send_btn = gr.Button("Send to Agent", variant="primary", scale=1)

        # Right Column: Live Visual Dials & Execution Trace
        with gr.Column(scale=5):
            gr.Markdown("### 🎛️ Physical Machine Dial Panel")
            dial_panel_html = gr.HTML(init_dash)
            
            gr.Markdown("### 🔍 Live Agent Execution Trace")
            with gr.Accordion("Inspection Drawer (Reasoning → Tool Calls → Observations)", open=True):
                trace_html = gr.HTML(format_trace_html([]))

    # Event handlers
    machine_dropdown.change(
        fn=on_machine_change,
        inputs=[machine_dropdown],
        outputs=[machine_card_html, dial_panel_html, dials_state],
    )

    send_btn.click(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, machine_dropdown, provider_dropdown, gemini_key_box, dials_state],
        outputs=[chatbot, dial_panel_html, trace_html, dials_state],
    ).then(
        fn=lambda: "",
        outputs=[msg_input],
    )
    
    msg_input.submit(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, machine_dropdown, provider_dropdown, gemini_key_box, dials_state],
        outputs=[chatbot, dial_panel_html, trace_html, dials_state],
    ).then(
        fn=lambda: "",
        outputs=[msg_input],
    )

    # Preset button click actions
    btn_scen1.click(
        fn=lambda: "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam",
        outputs=[msg_input],
    ).then(
        fn=lambda: "brother_sm3701",
        outputs=[machine_dropdown],
    ).then(
        fn=on_machine_change,
        inputs=[machine_dropdown],
        outputs=[machine_card_html, dial_panel_html, dials_state],
    ).then(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, machine_dropdown, provider_dropdown, gemini_key_box, dials_state],
        outputs=[chatbot, dial_panel_html, trace_html, dials_state],
    )

    btn_scen2.click(
        fn=lambda: "Severe bird-nesting and looping on underside of fabric on Singer 4423",
        outputs=[msg_input],
    ).then(
        fn=lambda: "singer_hd_4423",
        outputs=[machine_dropdown],
    ).then(
        fn=on_machine_change,
        inputs=[machine_dropdown],
        outputs=[machine_card_html, dial_panel_html, dials_state],
    ).then(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, machine_dropdown, provider_dropdown, gemini_key_box, dials_state],
        outputs=[chatbot, dial_panel_html, trace_html, dials_state],
    )

    btn_scen3.click(
        fn=lambda: "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701",
        outputs=[msg_input],
    ).then(
        fn=lambda: "brother_sm3701",
        outputs=[machine_dropdown],
    ).then(
        fn=on_machine_change,
        inputs=[machine_dropdown],
        outputs=[machine_card_html, dial_panel_html, dials_state],
    ).then(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, machine_dropdown, provider_dropdown, gemini_key_box, dials_state],
        outputs=[chatbot, dial_panel_html, trace_html, dials_state],
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    share = bool(os.environ.get("SHARE", False))
    lan = bool(os.environ.get("LAN", False))
    print(f"Starting Caliper Localhost Web Application on http://127.0.0.1:{port}")
    demo.launch(
        server_name="0.0.0.0" if lan else "127.0.0.1",
        server_port=port,
        share=share,
    )
