# Caliper: The Sewing & Calibration Atelier

<div align="center">
  <img src="assets/caliper_logo.svg" alt="Caliper Logo" width="380"/>
  <p><strong>Universal Mechanical Sewing Machine Setup, Real-Time Physics Calibration & Safety Verification Agent</strong></p>
  <p>
    <em>CIS 4394: Agentic AI — Final Term Project</em><br>
    <strong>Arya Devkota</strong> · Georgia State University · Fall 2026
  </p>
  <p>
    <span style="display:inline-block; background:#BFD7EA; color:#1F435B; padding:3px 12px; border-radius:12px; font-weight:700; font-size:12px;">50 INDEXED CHASSIS</span>
    <span style="display:inline-block; background:#CDE3D0; color:#2F5734; padding:3px 12px; border-radius:12px; font-weight:700; font-size:12px;">PHYSICS &amp; SAFETY GUARD</span>
    <span style="display:inline-block; background:#FAD2E1; color:#3D1E28; padding:3px 12px; border-radius:12px; font-weight:700; font-size:12px;">MAX-STEPS: 6</span>
  </p>
</div>

---

## 🌸 Overview: The Sewing & Calibration Atelier

**Caliper** transforms sewing machine setup from an intimidating trial-and-error guessing game into a tactile, whimsical maker's atelier experience. Inspired by vintage haberdasheries and tailor studios, Caliper combines real mechanical physics, needle deflection safety guardrails, and multi-provider agentic reasoning with a rich, hand-crafted web interface.

### Key Capabilities
- **50 Verified Sewing Machine Chassis:** Ingests 30 hardware parameters per machine across Brother, Singer, Janome, Juki, Baby Lock, and Bernette chassis.
- **Physical Tension & Seam Physics:** Calculates non-linear upper thread tension curves scaled to each machine's physical dial range (0–9, 1–8, etc.), stitch length, stitch width, and presser foot requirements based on fabric GSM weight and stretch percentage.
- **Active Safety Guardrails:** Automatically audits configurations to intercept critical broken needle hazards (e.g. fine 70/10 needle on heavy 14oz denim) and fabric tearing risks before stitches are made.
- **Strict Iteration Guard (`MAX_STEPS = 6`):** Guarantees bounded agent execution with zero runaway tool loops.
- **Tactile Web Atelier UI:** Built with FastAPI, Uvicorn, and vanilla JavaScript—featuring interactive rotating dials, 4-hole resin button caps, spiral lined notepad chat, and synthesized mechanical detent clicks via the Web Audio API.
- **Flexible Multi-Provider Inference:** Runs out-of-the-box locally with an offline **Deterministic ReAct Engine** (0 external dependencies), **Google Gemini 2.5 Flash**, or local **Ollama** (`llama3.1:latest`, `qwen2.5:0.5b`).

---

## 🎨 The Brand Design System: The Maker's Workbench

Caliper replaces generic flat web dashboards with a physical, whimsical workshop aesthetic:

| Atelier Component | Design Metaphor & Implementation |
| :--- | :--- |
| **Viewport Awning Border** | Alternating vertical awning stripe in Powder Blue (`#BFD7EA`) and White (`#FFFFFF`). |
| **Brand Logo & Slogan** | Authentic patchwork fabric logo in SVG accompanied by the cursive tagline *"The Sewing & Calibration Atelier"* in **Autography** and the stitched **"SEW IT!"** badge in **Oslo Stitch**. |
| **Selector Ribbon Panel** | Tailor's manila pattern envelope tray with Jupiteroid inputs, gold dashed chassis specs, and Powder Blue focus glow. |
| **Consultation Chat** | Spiral-bound lined notepad with metallic double-wire coil binding, faint horizontal notebook ruling (`repeating-linear-gradient`), and Confectioner's Blush memo notes (`#FAD2E1`). |
| **Starter Swatch Tray** | Quick starter scenarios styled as pinked fabric swatches secured by strips of Buttercup Yellow masking tape (`#DEA458`). |
| **Rolling Wool Yarn Loader** | Continuous 360° animated SVG yarn ball in Cherry Red (`#BF1318`) with Blush Pink (`#FAD2E1`) and Powder Blue (`#BFD7EA`) wrap ribbons. |
| **Stitched Send Button** | Cherry Red patch button with an inset `2px dashed` running stitch, 3D shadow (`0 4px 0 #851314`), and tactile active press. |
| **Tactile Rotary Dials** | Hand-crafted sewing machine dials with running-stitch tick perimeters, static 12 o'clock red thread indicator notches, and **4-hole resin button centers with crossed thread stitches**: Upper Tension in Buttercup Yellow (`#DEA458`), Stitch Length in Cherry Red (`#BF1318`), and Stitch Width in Denim Blue (`#1F435B`). Smooth `-120°` to `+120°` wobble-free rotation. |
| **Pinned Fabric Tags** | Stitch Type, Needle Gauge, and Presser Foot displayed as pinned fabric tags with brass pin heads and subtle rotational tilts (`-1deg` to `0.8deg`). |
| **Tailor's Reasoning Drawer** | High-contrast drawer in Deep Atelier Plum (`#3D1E28`) with Mint Green step badges (`#CDE3D0`), monospaced code tool calls, and Buttercup Gold answer highlights. |
| **Web Audio Detents** | Realistic mechanical transient clicks synthesized in real time via the Web Audio API on form submits, machine changes, and swatch chip clicks. |

### Typography Hierarchy (6 Local Brand Fonts)
- **Title (`Oslo Stitch`):** Celebratory callouts and the stitched `"SEW IT!"` slogan badge.
- **Subtitle (`Autography`):** Flowing cursive script for the brand tagline: *"The Sewing & Calibration Atelier"*.
- **Heading (`Photography`):** Atelier Consultation, Physical Machine Dials, and Tailor's Reasoning headers.
- **Subheading (`Biro Script`):** Fluid cursive script for chassis highlights, scenario headers, and section intros.
- **Section Header (`Pastel Crayon`):** Form labels, knob titles, and mini-tag badges.
- **Body (`Jupiteroid`):** Chat messages, input controls, chassis specs, and digital readouts.
- **Code (`SF Mono` / monospace):** Step tool calls, JSON arguments, and execution traces.

---

## 🚀 Quick Start: Launch Caliper

### Option 1: 1-Click Launch from `.zip` (Recommended for Graders & Offline Users)
If you downloaded the Caliper project archive `.zip` from GitHub or Canvas:
1. **Extract** the downloaded `.zip` archive on your computer.
2. **Double-click** the launcher for your operating system:
   * **Windows:** Double-click [`START_HERE_WINDOWS.bat`](START_HERE_WINDOWS.bat)
   * **macOS:** Double-click [`START_HERE_MAC.command`](START_HERE_MAC.command)
3. The launcher will automatically provision an isolated `.venv`, install production dependencies from `requirements.txt`, launch the FastAPI server, pre-load the 50-machine hardware database, and automatically open your default browser to:
   👉 **[http://127.0.0.1:7860](http://127.0.0.1:7860)**

> [!TIP]
> **macOS Gatekeeper / `.zip` Extraction Permissions Fallback:**  
> If macOS blocks double-clicking with *"START_HERE_MAC.command cannot be opened"* due to Gatekeeper quarantine or stripped execute bits from archive extraction, simply open your Terminal, navigate to the extracted folder, and run:
> ```bash
> bash START_HERE_MAC.command
> ```

---

### Option 2: 1-Click Cloud Deployment on Render
Deploy your own live, server-side Caliper web application on **Render's Free Tier ($0)** using the included [`render.yaml`](render.yaml) Blueprint:
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** → **Blueprint**.
3. Select your repository. Render automatically reads `render.yaml`, provisions the Python 3.11 web service (`caliper-atelier`), installs `requirements.txt`, and configures health monitoring via `/api/machines`.
4. Enter your `GEMINI_API_KEY` when prompted in the Render dashboard.

---

### Option 3: Manual Developer Setup (Git Clone)
```bash
# Clone the repository
git clone https://github.com/aryadevkota/caliper.git
cd caliper

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install runtime dependencies
pip install -r requirements.txt

# Launch web server
python app.py
```
Open your browser to: **[http://127.0.0.1:7860](http://127.0.0.1:7860)**  
*(To expose on your local Wi-Fi for mobile/tablet testing: `LAN=1 python app.py`)*

---

### 🔑 Zero-Config LLM & Offline Modes
* **Zero API Key Needed (Offline ReAct):** Caliper ships with an embedded **Deterministic ReAct Engine** that calculates true mechanical tension curves, stitch dimensions, and safety limits entirely offline with **0 API keys and 0 external dependencies**.
* **Google Gemini 2.5 Flash:** Select *Google Gemini 2.5 Flash* in the UI and enter your API key directly in the **`Key:`** input field (or provide `GEMINI_API_KEY` in `.env` / Render).
* **Local Ollama:** Select *Local Ollama (llama3.1)* or *Local Ollama (qwen2.5)* to run on your local hardware via Ollama.

---

### 3. Run the Command-Line Agent (CLI)
Test the agent on real inputs directly from your terminal:

```bash
# Scenario 1: Stretch Jersey Calibration on Brother SM3701
python caliper_cli.py "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"

# Scenario 2: Bird-Nesting Defect Troubleshooting on Singer 4423
python caliper_cli.py --defect "Severe bird-nesting and looping on underside of fabric on Singer 4423"

# Scenario 3: Safety Guardrail Intercept (Fine needle on 14oz denim)
python caliper_cli.py --safety "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701"

# Scenario 4: Silk Chiffon Rolled Hem on Janome HD1000
python caliper_cli.py "Janome HD1000, silk chiffon 45 GSM rolled hem"
```

### 4. Run the Automated Test Suite (45 Tests)
```bash
python3 -m unittest discover -s tests -v
```
All 45 tests across hardware specs, physics calibration, multi-turn history, and security guardrails pass in `~0.05 seconds`.

### 5. Run the pass^k (k = 3) Evaluation Harness
```bash
python3 evals/run_passk_eval.py
```
Runs repeated executions ($k = 3$ trials per case across 14 test cases, 42 trials total) comparing single-run accuracy (`pass@1`) against strict all-trial consistency (`pass^k`). Results are saved to [`caliper_eval_results.xlsx`](caliper_eval_results.xlsx) with side-by-side category summaries and complete trial logs.

---

## 🏗️ Project Architecture

```
caliper/
├── app.py                                       # FastAPI Web Server & API Router (Port 7860)
├── caliper_cli.py                               # Standalone CLI Interface with Multi-Provider Support
├── caliper_eval_results.xlsx                    # Pass^k Evaluation Results (3 Sheets, 42 Trials)
├── render.yaml                                  # 1-Click Render Cloud Deployment Blueprint
├── Procfile                                     # Cloud Process Starter
├── START_HERE_MAC.command                       # 1-Click macOS Localhost Launcher
├── START_HERE_WINDOWS.bat                       # 1-Click Windows Localhost Launcher
├── requirements.txt                             # Lightweight Production Dependencies
├── requirements-dev.txt                         # Local Testing & Verification Dependencies
├── MILESTONE_I_REPORT.md                        # Milestone Deliverable Report & Trace Analysis
├── caliper_sewing_machines_hardware_specs.xlsx  # 50 Sewing Machine Hardware Specs Database
├── assets/                                      # Application Previews & Verification Captures
├── evals/                                       # Pass^k Evaluation Harness
│   └── run_passk_eval.py                        # Automated Pass^k (k=3) Test Suite & Excel Exporter
├── caliper/                                     # Core Agentic Calibration & Physics Engine
│   ├── __init__.py                              # Public API exports
│   ├── hardware_db.py                           # 50-Machine Catalog & Fuzzy Chassis Matcher
│   ├── mechanics.py                             # Thread Tension Physics, Diagnostics & Safety
│   ├── guardrails.py                            # Input/Output Deflection & Injection Guardrails
│   ├── tools.py                                 # 4 Agent Tools & Schemas (Ollama / Gemini)
│   ├── agent.py                                 # ReAct Loop with Strict MAX_STEPS=6 Guard
│   └── ui_helpers.py                            # SVG Rotary Dials & HTML Visualizer
├── static/
│   ├── atelier_assets/                          # Consolidated Shippable Brand & Catalog Assets
│   │   ├── brand/                               # Caliper Logo, Background & Emblems
│   │   ├── catalog/                             # Hero Machine, Gauge & Symbol Assets
│   │   ├── dials/                               # Rotary Dial Bezels & Rotors
│   │   ├── folders/                             # Tab & Drawer Cardstock Graphics
│   │   ├── fonts/                               # 6 Bundled Brand Web Fonts (.otf / .ttf)
│   │   ├── icons/                               # Active Haberdashery Accent SVGs
│   │   └── swatches/                            # Fabric Texture Specimen SVGs
│   ├── css/style.css                            # Atelier Brand Design System & CSS Animations
│   └── js/app.js                                # Dial Physics, Web Audio Detents & API Streaming
├── templates/
│   └── index.html                               # Semantic Workshop Atelier Single-Page Interface
└── tests/
    ├── test_mechanics.py                        # 16 Hardware, Physics & Defect Unit Tests
    ├── test_agent.py                            # 12 Integration, Tool & Guardrail Tests
    ├── test_conversational_upgrades.py          # Multi-Turn Context & Clarification Tests
    └── test_guardrails_hardened.py              # Prompt Injection & Input Hardening Tests
```

---

## 🛠️ The 4 Domain Agent Tools

| Tool | Purpose | Physical Inputs | Outputs |
| :--- | :--- | :--- | :--- |
| **`lookup_sewing_machine_specs`** | Queries hardware dial bounds, hook type, bobbin, and shank system | Machine brand or model name (e.g. `Brother SM3701`, `Singer 4423`, `Janome HD1000`) | Tension bounds (0–9), default tension, needle system, feed dog type, max speed SPM |
| **`calculate_fabric_calibration`** | Non-linear dial calculation for upper thread tension, stitch dimensions, and foot | Fabric name, GSM weight, stretch percentage, seam type, machine chassis | Upper tension dial setting, stitch length (mm), stitch width (mm), needle gauge, presser foot |
| **`diagnose_stitch_defect`** | Mechanical diagnosis of stitch failures | Defect symptom (bird-nesting, skipped stitches, puckering, needle breakage) | Root causes, tension deltas, bobbin seating checks, presser foot lift rules |
| **`verify_safety_constraints`** | Physical safety audit preventing needle deflection or fabric tearing | Needle EU size, fabric GSM weight, fabric type | Safety status (`SAFE`, `WARNING`, `CRITICAL`), deflection risk warning, safe needle upgrade |

---

## 📊 50 Sewing Machine Hardware Dataset

The agent directly queries `caliper_sewing_machines_hardware_specs.xlsx`, containing:
- **Major Brands:** Brother, Singer, Janome, Juki, Baby Lock, Bernette (by Bernina).
- **Chassis Categories:** Mechanical, Mechanical Heavy Duty, Computerized, Semi-Industrial Tailoring.
- **Dial Ranges:** Dial (0–9), Dial (1–8), Dial (1–9), Automatic Electronic.
- **Bobbin Systems:** Top Drop-in (Class 15/SA156), Front-Loading Oscillating Shuttle, Rotary Horizontal, Industrial Class L.
- **30 Hardware Attributes:** Needle size limits, presser foot pressure adjustment, feed dogs, drop feed lever, thread cutters, and layout specs.

---

## 📄 Deliverable Links & References

- **Live Application:** [http://127.0.0.1:7860](http://127.0.0.1:7860)
- **GitHub Repository:** [https://github.com/aryadevkota/caliper](https://github.com/aryadevkota/caliper)
- **Pass^k Evaluation Results:** See [`caliper_eval_results.xlsx`](caliper_eval_results.xlsx) (14 cases, $k = 3$, 42 runs, side-by-side pass@1 vs pass^3).
- **Execution Trace & Analysis Report:** See [`MILESTONE_I_REPORT.md`](MILESTONE_I_REPORT.md).
- **Original Project Proposal:** See [`DevkotaArya_ProjectProposal-AgenticAI.pdf`](DevkotaArya_ProjectProposal-AgenticAI.pdf).
