# Caliper: The Sewing & Calibration Atelier

<div align="center">
  <img src="assets/caliper_logo.svg" alt="Caliper Logo" width="380"/>
  <p><strong>A thoughtful sewing machine setup, tension calibration, and fabric safety companion</strong></p>
  <p>
    <em>CIS 4394: Agentic AI — Final Term Project</em><br>
    <strong>Arya Devkota</strong> · Georgia State University · Fall 2026
  </p>
  <p>
    <span style="display:inline-block; background:#BFD7EA; color:#1F435B; padding:3px 12px; border-radius:12px; font-weight:700; font-size:12px;">50 SEWING MACHINES</span>
    <span style="display:inline-block; background:#CDE3D0; color:#2F5734; padding:3px 12px; border-radius:12px; font-weight:700; font-size:12px;">FABRIC &amp; NEEDLE SAFETY</span>
    <span style="display:inline-block; background:#FAD2E1; color:#3D1E28; padding:3px 12px; border-radius:12px; font-weight:700; font-size:12px;">ATELIER COMPANION</span>
  </p>
</div>

---

## 🌸 Overview: The Sewing & Calibration Atelier

Caliper turns sewing machine setup from trial-and-error guesswork into a calm, tactile studio experience. Inspired by vintage haberdasheries and neighborhood tailor shops, Caliper pairs real sewing mechanics and needle safety checks with a warm, hand-crafted web interface.

### What Caliper Helps With

- **50 Popular Sewing Machines:** Knows the dial ranges, bobbin styles, needle systems, and presser feet for 50 models across Brother, Singer, Janome, Juki, Baby Lock, and Bernette.
- **Fabric-Specific Dial Settings:** Recommends upper thread tension (tailored to each machine's exact dial scale), stitch length, stitch width, needle gauge, and presser foot based on your fabric's weight and stretch.
- **Gentle Safety Checks:** Catches risky pairings before you sew—like using a fine 70/10 needle on heavy 14oz denim, or a thick needle on delicate silk chiffon.
- **Focused, Predictable Reasoning:** Keeps every calibration clear and concise within a 6-step limit, with an inspectable reasoning drawer if you want to see how it arrived at an answer.
- **A Tactile Workbench Interface:** Built with FastAPI, Uvicorn, and vanilla JavaScript, featuring interactive rotating dials, spiral-bound notebook chat, fabric swatch presets, and subtle mechanical dial clicks via the Web Audio API.
- **Flexible Ways to Run:** Works offline out of the box with a built-in deterministic engine, or connects to Google Gemini 2.5 Flash or local Ollama (`llama3.1:latest`, `qwen2.5:0.5b`).

---

## 🎨 Design & Workbench Details

Caliper is designed to feel like a physical sewing table rather than a standard dashboard:

| Atelier Detail | Look & Feel |
| :--- | :--- |
| **Top Awning Border** | Alternating Powder Blue (`#BFD7EA`) and White (`#FFFFFF`) stripe along the top edge. |
| **Logo & Tagline** | Patchwork SVG logo paired with "The Sewing & Calibration Atelier" in Autography and the stitched "SEW IT!" badge in Oslo Stitch. |
| **Machine Catalog** | Illustrated machine stage with hardware readout pills and a soft Powder Blue focus glow. |
| **Consultation Notebook** | Lined notepad chat with subtle notebook ruling (`repeating-linear-gradient`) and Confectioner's Blush user notes (`#FAD2E1`). |
| **Sample Swatches** | Six quick-start fabric scenarios styled as pinked fabric swatches on a wooden workbench slab. |
| **Rolling Yarn Loader** | Animated Cherry Red (`#BF1318`) yarn ball with Blush Pink (`#FAD2E1`) and Powder Blue (`#BFD7EA`) wraps while thinking. |
| **Stitched Calibrate Button** | Cherry Red patch button with a dashed running-stitch border and soft press motion. |
| **Interactive Rotary Dials** | Draggable sewing machine dials for Upper Tension, Stitch Length, and Stitch Width that spin smoothly into place. |
| **Pinned Spec Tags** | Stitch Type, Needle Gauge, and Presser Foot displayed on pinned fabric tags with brass pin heads. |
| **Agent Logs Drawer** | Deep Atelier Plum (`#3D1E28`) drawer with Mint Green step badges (`#CDE3D0`) showing each reasoning step and tool check. |
| **Web Audio Clicks** | Subtle mechanical ratchet clicks synthesized in the browser as you turn dials or switch machines. |

### Typography

- **Title (Oslo Stitch):** Playful stitched accents and the "SEW IT!" badge.
- **Subtitle (Autography):** Flowing script for "The Sewing & Calibration Atelier".
- **Heading (Photography):** Section headers for Consultation, Physical Machine Dials, and Agent Logs.
- **Subheading (Biro Script):** Handwritten notes on fabric swatch cards.
- **Section Header (Pastel Crayon):** Labels, dial titles, and small badges.
- **Body (Jupiteroid):** Chat messages, specs, and dial readouts.
- **Code (SF Mono / monospace):** Tool calls and trace logs.

---

## 🚀 Quick Start: Launch Caliper

### Option 1: 1-Click Launch from .zip (Easiest for Local Testing)

If you downloaded the project .zip from GitHub or Canvas:
1. Extract the .zip folder on your computer.
2. Double-click the launcher for your system:
   - **Windows:** [`START_HERE_WINDOWS.bat`](START_HERE_WINDOWS.bat)
   - **macOS:** [`START_HERE_MAC.command`](START_HERE_MAC.command)
3. The script sets up a local `.venv`, installs `requirements.txt`, starts the server, and opens your browser to: 👉 **http://127.0.0.1:7860**

> [!TIP]
> **macOS Gatekeeper / .zip Note:**  
> If macOS blocks double-clicking `START_HERE_MAC.command` after extracting a .zip, open Terminal inside the extracted folder and run:
> ```bash
> bash START_HERE_MAC.command
> ```

---

### Option 2: Deploy Online on Render (Free Tier)

You can host Caliper online on Render's Free Tier ($0) using the included [`render.yaml`](render.yaml) Blueprint:
1. Push or fork this repository on GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** → **Blueprint**.
3. Select your repository. Render reads `render.yaml`, sets up the Python web service (`caliper-atelier`), installs `requirements.txt`, and checks `/api/machines`.
4. Paste your `GEMINI_API_KEY` when prompted.

---

### Option 3: Manual Developer Setup (Git Clone)

```bash
# Clone the repository
git clone https://github.com/aryadevkota/caliper.git
cd caliper

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the web app
python app.py
```

Open your browser to **http://127.0.0.1:7860**.  
*(To test on another device on your Wi-Fi: `LAN=1 python app.py`)*

---

### 🔑 Offline & Model Options

- **Works With No API Key:** Caliper includes a built-in Deterministic ReAct mode that computes tension curves, stitch settings, and safety checks completely offline.
- **Google Gemini 2.5 Flash:** Choose *Google Gemini 2.5 Flash* in the UI and paste your key into the **`Key:`** field (or set `GEMINI_API_KEY` in `.env` / Render).
- **Local Ollama:** Choose *Local Ollama (llama3.1)* or *Local Ollama (qwen2.5)* if you have Ollama running locally.

---

### 3. Run from the Command Line (CLI)

You can also test Caliper directly in your terminal:

```bash
# Stretch Jersey Calibration on Brother SM3701
python caliper_cli.py "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"

# Bird-Nesting Defect Troubleshooting on Singer 4423
python caliper_cli.py --defect "Severe bird-nesting and looping on underside of fabric on Singer 4423"

# Safety Check (Fine needle on 14oz denim)
python caliper_cli.py --safety "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701"

# Silk Chiffon Rolled Hem on Janome HD1000
python caliper_cli.py "Janome HD1000, silk chiffon 45 GSM rolled hem"
```

---

### 4. Run the Automated Test Suite (45 Tests)

```bash
python3 -m unittest discover -s tests -v
```

All 45 tests covering machine specs, calibration math, multi-turn conversation history, and safety guardrails run in about 0.05 seconds.

---

### 5. Run the pass^k (k = 3) Evaluation Harness

```bash
python3 evals/run_passk_eval.py
```

Runs 3 trials per test case across 14 cases (42 trials total) to compare single-run accuracy (`pass@1`) against full-consistency (`pass^k`), saving the results to [`caliper_eval_results.xlsx`](caliper_eval_results.xlsx).

---

## 🏗️ Project Structure

```
caliper/
├── app.py                                       # FastAPI Web Server & API Routes (Port 7860)
├── caliper_cli.py                               # Command-Line Interface
├── caliper_eval_results.xlsx                    # Pass^k Evaluation Results (3 Sheets, 42 Trials)
├── render.yaml                                  # Render Cloud Deployment Blueprint
├── Procfile                                     # Cloud Start Command
├── START_HERE_MAC.command                       # 1-Click macOS Launcher
├── START_HERE_WINDOWS.bat                       # 1-Click Windows Launcher
├── requirements.txt                             # Production Dependencies
├── requirements-dev.txt                         # Local Testing Dependencies
├── MILESTONE_I_REPORT.md                        # Milestone Report & Trace Analysis
├── caliper_sewing_machines_hardware_specs.xlsx  # 50 Sewing Machine Specifications
├── assets/                                      # App Screenshots & Preview Images
├── evals/                                       # Evaluation Harness
│   └── run_passk_eval.py                        # Automated Pass^k (k=3) Runner & Excel Exporter
├── caliper/                                     # Core Agent & Sewing Mechanics
│   ├── __init__.py                              # Public Exports
│   ├── hardware_db.py                           # 50-Machine Lookup & Fuzzy Matcher
│   ├── mechanics.py                             # Tension Physics, Diagnostics & Safety Rules
│   ├── guardrails.py                            # Input/Output & Scope Guardrails
│   ├── tools.py                                 # 4 Agent Tools & Schemas (Ollama / Gemini)
│   ├── agent.py                                 # ReAct Loop (MAX_STEPS=6) & Memory Handling
│   └── ui_helpers.py                            # SVG Dials & HTML Helpers
├── static/
│   ├── atelier_assets/                          # Consolidated Brand, Catalog & UI Assets
│   │   ├── brand/                               # Logo, Background & Emblems
│   │   ├── catalog/                             # Hero Machine, Gauge & Spec Icons
│   │   ├── dials/                               # Rotary Dial Bezels & Wheels
│   │   ├── folders/                             # Tab & Drawer Graphics
│   │   ├── fonts/                               # 6 Brand Web Fonts (.otf / .ttf)
│   │   ├── icons/                               # Haberdashery Accent SVGs
│   │   └── swatches/                            # Fabric Swatch SVGs
│   ├── css/style.css                            # Atelier Design System & Styling
│   └── js/app.js                                # Dial Physics, Web Audio & API Calls
├── templates/
│   └── index.html                               # Main Atelier Web Page
└── tests/
    ├── test_mechanics.py                        # Hardware, Physics & Defect Unit Tests
    ├── test_agent.py                            # Agent, Tool & Guardrail Integration Tests
    ├── test_conversational_upgrades.py          # Multi-Turn Context & Clarification Tests
    └── test_guardrails_hardened.py              # Prompt Injection & Input Hardening Tests
```

---

## 🛠️ The 4 Agent Tools

| Tool | What It Does | Inputs | Outputs |
| :--- | :--- | :--- | :--- |
| **`lookup_sewing_machine_specs`** | Looks up dial ranges, hook type, bobbin, and needle system for a machine | Machine brand or model (e.g. Brother SM3701, Singer 4423, Janome HD1000) | Tension range, default tension, needle system, feed dogs, max speed |
| **`calculate_fabric_calibration`** | Computes upper tension, stitch dimensions, needle, and presser foot | Fabric name, GSM weight, stretch %, seam type, machine model | Upper tension setting, stitch length (mm), stitch width (mm), needle gauge, presser foot |
| **`diagnose_stitch_defect`** | Identifies common stitch issues and how to fix them | Symptom (bird-nesting, skipped stitches, puckering, needle breakage) | Root causes, tension adjustments, bobbin & threading checks |
| **`verify_safety_constraints`** | Checks whether a needle and fabric pairing is safe to sew | Needle EU size, fabric GSM weight, fabric type | Safety status (`SAFE`, `WARNING`, `CRITICAL`), risk note, safer needle suggestion |

---

## 📊 Sewing Machine Dataset

Caliper reads directly from `caliper_sewing_machines_hardware_specs.xlsx`, which includes:
- **Brands:** Brother, Singer, Janome, Juki, Baby Lock, and Bernette.
- **Machine Types:** Mechanical, Mechanical Heavy Duty, Computerized, and Semi-Industrial Tailoring.
- **Dial Scales:** Dial (0–9), Dial (1–8), Dial (1–9), and Automatic Electronic.
- **Bobbin Systems:** Top Drop-in (Class 15/SA156), Front-Loading Oscillating Shuttle, Rotary Horizontal, and Industrial Class L.
- **Hardware Details:** Needle size limits, presser foot pressure adjustment, feed dogs, drop feed support, and thread cutters.

---

## 📄 Links & Deliverables

- **Local Web App:** [http://127.0.0.1:7860](http://127.0.0.1:7860)
- **GitHub Repository:** [https://github.com/aryadevkota/caliper](https://github.com/aryadevkota/caliper)
- **Pass^k Evaluation Results:** [`caliper_eval_results.xlsx`](caliper_eval_results.xlsx) (14 cases, 3 trials each, pass@1 vs pass^3)
- **Milestone Report:** [`MILESTONE_I_REPORT.md`](MILESTONE_I_REPORT.md)
- **Original Project Proposal:** [`DevkotaArya_ProjectProposal-AgenticAI.pdf`](DevkotaArya_ProjectProposal-AgenticAI.pdf)
