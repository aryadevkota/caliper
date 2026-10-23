# Caliper: Universal Sewing Machine Setup & Calibration Agent

<div align="center">
  <img src="assets/caliper_logo.png" alt="Caliper Logo" width="320"/>
  <p><strong>Universal Mechanical Sewing Machine Setup, Real-Time Physics Calibration & Safety Verification Agent</strong></p>
  <p>
    <em>CIS 4394: Agentic AI — Final Term Project</em><br>
    <strong>Arya Devkota</strong> · Georgia State University · Fall 2026
  </p>
</div>

---

## 📌 Milestone I: Your First Working Agent

This repository contains the first working prototype of **Caliper**, designed for **Capstone Milestone I** in CIS 4394:
- **Single Agent with Real Tools:** Implements 4 domain-specific tools querying 50 real sewing machines, calculating non-linear thread tension physics, diagnosing stitch defects, and auditing physical safety constraints.
- **Strict Stop Condition:** Immutable max-iteration guard (`MAX_STEPS = 6`).
- **Interactive Localhost Web UI:** Gradio 6.x app running at `http://127.0.0.1:7860` with animated SVG rotary dials (tension, stitch length, stitch width), hardware chassis card, and live trace inspection.
- **Multi-Provider Inference:** Runs out-of-the-box locally with **Ollama** (`llama3.1:latest`, `qwen2.5:0.5b`), **Google Gemini 2.5 Flash**, or an offline **Deterministic ReAct Engine** with 0 external dependencies.
- **50-Machine Hardware Catalog:** Directly ingests `caliper_sewing_machines_hardware_specs.xlsx` with 30 hardware parameters per machine.

---

## 🚀 Quickstart: Run Caliper Locally

### 1. Environment Setup
```bash
# Clone the repository
cd Caliper_AgenticAI-FinalTermProject

# Ensure your virtual environment is active
source .venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### 2. Launch the Localhost Web Demo (Recommended)
```bash
python app.py
```
Then open your browser to **[http://127.0.0.1:7860](http://127.0.0.1:7860)**.

*To open on mobile devices connected to the same Wi-Fi, run:*
```bash
LAN=1 python app.py
```

### 3. Run the Command-Line Agent (CLI)
You can test the agent on real inputs directly from the terminal:

```bash
# Scenario 1: Delicate Stretch Fabric Calibration
python caliper_cli.py "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"

# Scenario 2: Real-Time Stitch Defect Troubleshooting
python caliper_cli.py --defect "Severe bird-nesting and looping on underside of fabric on Singer 4423"

# Scenario 3: Safety Guardrail Intercept (Fine needle on 14oz heavy denim)
python caliper_cli.py --safety "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701"
```

### 4. Run the Automated Test Suite (28 Tests)
```bash
python -m unittest discover -s tests -v
```
All 28 tests will pass in `~0.2 seconds`.

---

## 🏗️ Project Architecture

```
Caliper_AgenticAI-FinalTermProject/
├── app.py                                       # Localhost Web Interface (Gradio 6.x)
├── caliper_cli.py                               # Standalone CLI Interface
├── MILESTONE_I_REPORT.md                        # Milestone I Deliverable Report & Trace
├── caliper_sewing_machines_hardware_specs.xlsx  # 50 Sewing Machine Hardware Specs
├── assets/
│   └── caliper_logo.png                         # Caliper Brand Logo
├── caliper/
│   ├── __init__.py                              # Public API exports
│   ├── hardware_db.py                           # 50-Machine Catalog & Fuzzy Matcher
│   ├── mechanics.py                             # Physics, Defect Diagnostics & Safety
│   ├── tools.py                                 # 4 Agent Tools & Schemas (Ollama / Gemini)
│   ├── agent.py                                 # Caliper Agent Loop (MAX_STEPS=6 Guard)
│   └── ui_helpers.py                            # SVG Rotary Dials & HTML Visualizer
└── tests/
    ├── test_mechanics.py                        # 16 Hardware & Physics Unit Tests
    └── test_agent.py                            # 12 Integration, Tool & Guard Tests
```

---

## 🛠️ The 4 Real Domain Tools

| Tool | Purpose | Physical Inputs | Outputs |
| :--- | :--- | :--- | :--- |
| **`lookup_sewing_machine_specs`** | Queries hardware dial bounds, hook type, bobbin, and shank system | Machine brand or model name (e.g. `Brother SM3701`, `Singer 4423`, `Janome HD1000`) | Tension bounds (0–9), default tension, needle system, feed dog type, max speed SPM |
| **`calculate_fabric_calibration`** | Non-linear dial calculation for upper thread tension, stitch dimensions, and foot | Fabric name, GSM weight, stretch percentage, seam type, machine chassis | Upper tension dial setting, stitch length (mm), stitch width (mm), needle gauge, presser foot |
| **`diagnose_stitch_defect`** | Mechanical diagnosis of stitch failures | Defect symptom (bird-nesting, skipped stitches, puckering, needle breakage) | Root causes, tension deltas, bobbin seating checks, presser foot lift rules |
| **`verify_safety_constraints`** | Physical safety audit preventing needle deflection or fabric tearing | Needle EU size, fabric GSM weight, fabric type | Safety status (`SAFE`, `WARNING`, `CRITICAL`), deflection risk warning, safe needle fix |

---

## 📊 50 Sewing Machine Hardware Dataset

The agent queries `caliper_sewing_machines_hardware_specs.xlsx`, containing:
- **Brands:** Brother, Singer, Janome, Juki, Baby Lock, Bernette (by Bernina).
- **Categories:** Mechanical, Mechanical Heavy Duty, Computerized, Semi-Industrial Tailoring.
- **Dial Types:** Dial (0–9), Dial (1–8), Dial (1–9), Automatic Electronic.
- **Bobbin Systems:** Top Drop-in (Class 15/SA156), Front-Loading Oscillating Shuttle, Rotary Horizontal, Industrial Class L.
- **30 Hardware Attributes:** Needle size limits, presser foot pressure adjustment, feed dogs, drop feed lever, thread cutters, and layout specs.

---

## 📄 Milestone Deliverable Links

- **Execution Trace & Analysis Report:** See [`MILESTONE_I_REPORT.md`](MILESTONE_I_REPORT.md) for the required half-page evaluation: what works, what does not yet, and what we will do next.
- **Original Proposal:** See [`DevkotaArya_ProjectProposal-AgenticAI.pdf`](DevkotaArya_ProjectProposal-AgenticAI.pdf).
