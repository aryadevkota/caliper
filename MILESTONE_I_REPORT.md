# Caliper: Universal Sewing Machine Setup & Calibration Agent
## Capstone Milestone I Deliverable Report (CIS 4394 · Agentic AI)
**Author:** Arya Devkota  
**Course:** CIS 4394: Agentic AI — Robinson College of Business, Georgia State University  
**Instructor:** Dr. Xinyu Fu  
**Milestone:** Capstone Milestone I: Your First Working Agent (5 pts)

---

## 1. System Architecture & Tool Design Overview

In accordance with the CIS 4394 Milestone I specification, Caliper is implemented as a **single autonomous agent with well-designed domain tools, explicit reasoning traces, and a deterministic stop-condition guard**. 

Rather than prematurely introducing multi-agent coordination overhead before establishing a verifiable single-agent baseline (the core lesson of Week 9), Milestone I establishes the complete end-to-end execution loop for mechanical sewing machine calibration.

```
                  ┌──────────────────────────────────────────────┐
                  │          USER TASK / SEWING QUERY             │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │                CALIPER AGENT                 │
                  │   - Harness: Max-iteration guard (MAX_STEPS=6)│
                  │   - Providers: Local Ollama / Gemini / Engine│
                  └──────┬───────────────┬───────────────┬───────┘
                         │               │               │
         ┌───────────────┴────┐   ┌──────┴─────────┐   ┌─┴────────────────┐
         │ lookup_sewing_     │   │ calculate_     │   │ verify_safety_   │
         │ machine_specs      │   │ fabric_        │   │ constraints      │
         │                    │   │ calibration    │   │                  │
         │ Reads 50 hardware  │   │ Tension scaling│   │ Needle deflection│
         │ chassis from Excel │   │ needle & foot  │   │ & blowout audit  │
         └────────────────────┘   └────────────────┘   └──────────────────┘
                                         │
                                  ┌──────┴─────────┐
                                  │ diagnose_      │
                                  │ stitch_defect  │
                                  │                │
                                  │ Bird-nesting & │
                                  │ loop analysis  │
                                  └────────────────┘
```

### Core Components
1. **Machine Hardware Knowledge Base (`caliper/hardware_db.py`)**:
   - Ingests and indexes `caliper_sewing_machines_hardware_specs.xlsx` containing **50 distinct commercial sewing machines** across Brother, Singer, Janome, Juki, Baby Lock, and Bernette.
   - Indexes 370+ normalized alias keys for typo-tolerant, fuzzy lookup.
   - Extracts physical dial bounds (e.g. 0–9 vs 1–8), default tension, hook type, bobbin system (top drop-in vs front-load), needle systems (130/705 H), and speed ratings.

2. **Physical Mechanics & Safety Engine (`caliper/mechanics.py`)**:
   - Calculates non-linear upper thread tension values scaled to machine chassis limits.
   - Selects needle systems and gauges based on fabric weight (GSM), stretch elasticity, and weave type.
   - Implements closed-loop stitch defect diagnosis for bird-nesting, skipped stitches, puckering, and needle breakage.
   - Enforces physical safety boundaries, halting execution upon detecting high-deflection hazards (e.g., fine needles on heavy canvas/denim).

3. **Agent Orchestration Harness (`caliper/agent.py`)**:
   - Implements the agent loop with an immutable **`MAX_STEPS = 6` stop condition**.
   - Supports dual-homed inference: Local Ollama (`llama3.1:latest` or `qwen2.5:0.5b`), Google Gemini (`gemini-2.5-flash`), and an offline deterministic ReAct engine that guarantees 100% test reproducibility.

4. **Localhost Web Application (`app.py`)**:
   - Runs locally at `http://127.0.0.1:7860` (or accessible over local Wi-Fi with `LAN=1`).
   - Features dynamic SVG rotary dial gauges, machine selection dropdown, live execution trace inspector, and chat interface.

---

## 2. End-to-End Execution Trace

The trace below records a real run executed on real input from Scenario 1 of the project proposal:
- **Input Goal:** `"Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"`
- **Harness Guard:** `MAX_STEPS = 6`

```text
==============================================================================
CALIPER UNIVERSAL SEWING MACHINE SETUP & CALIBRATION AGENT
Goal: Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam
Provider: auto | Model: default | Stop Condition: MAX_STEPS = 6
==============================================================================

[step 1]
  REASONING : Identify sewing machine specifications and dial bounds for 'Brother SM3701'.
  TOOL CALL : lookup_sewing_machine_specs({'model_query': 'Brother SM3701'})
  OBSERVATION:
    MACHINE SPECIFICATIONS: Brother SM3701 [brother_sm3701]
    - Brand & Model: Brother SM3701
    - Category / Control: Mechanical | Dial Mechanical
    - Bobbin Mechanism: Top Drop-in (Class 15 / SA156, Hook: Rotary Horizontal)
    - Needle System: 130/705 H (Needle Size Range: EU 65 - 110)
    - Upper Tension Dial: Dial (0-9) | Default: 4.0 | Dial Bounds: 0.0 - 9.0
    - Stitch Length Range: 0.0 - 4.0 mm
    - Stitch Width Range: 0.0 - 5.0 mm
    - Presser Foot System: Snap-on (Low Shank) (Pressure Adjustment: Fixed (Auto))
    - Feed Dogs / Drop Feed: 6-piece | Drop Feed: Cover Plate
    - Max Speed: 800 SPM | Built-in Stitches: 37

[step 2]
  REASONING : Calculate optimal physical dial calibrations for polyester spandex jersey knit (200.0 GSM, 50.0% stretch, seam: side seam).
  TOOL CALL : calculate_fabric_calibration({'fabric_name': 'polyester spandex jersey knit', 'gsm_weight': 200.0, 'stretch_pct': 50.0, 'seam_type': 'side seam', 'machine_query': 'Brother SM3701'})
  OBSERVATION:
    CALIBRATION RECOMMENDATIONS FOR: polyester spandex jersey knit
    - Target Machine: Brother SM3701 (brother_sm3701)
    - Fabric Parameters: 200.0 GSM | 50.0% Stretch | Seam: side seam
    - Upper Tension Dial: 3.5 (Dial (0-9))
    - Stitch Length: 2.5 mm
    - Stitch Width: 1.5 mm
    - Stitch Type: Stretch Zig-zag
    - Needle Recommendation: 75/11 Ballpoint/Stretch (Needle System: 130/705 H)
    - Presser Foot: Walking foot / Even feed
    - Safety Verification: [SAFE] Parameters verified within safe physical limits.

[step 3]
  REASONING : Verify safety limits for recommended needle gauge (EU 75) with material.
  TOOL CALL : verify_safety_constraints({'needle_size_eu': 75, 'fabric_gsm': 200.0, 'fabric_type': 'polyester spandex jersey knit'})
  OBSERVATION:
    SAFETY VERIFICATION AUDIT: [SAFE]
    - Needle Gauge Tested: EU 75 / US 11
    - Material Tested: polyester spandex jersey knit (200.0 GSM)
    - Operational Status: SAFE TO OPERATE
    - Engineering Assessment: Physical parameters within safe operating thresholds.

[step 4]
  REASONING : Generate comprehensive calibrated machine setup readout and instructions.
  ANSWER    :
    ### Caliper Machine Calibration Readout
    
    **Target Machine:** Brother SM3701
    **Fabric:** polyester spandex jersey knit (200.0 GSM, 50.0% stretch)
    **Seam Type:** side seam
    
    CALIBRATION RECOMMENDATIONS FOR: polyester spandex jersey knit
    - Target Machine: Brother SM3701 (brother_sm3701)
    - Fabric Parameters: 200.0 GSM | 50.0% Stretch | Seam: side seam
    - Upper Tension Dial: 3.5 (Dial (0-9))
    - Stitch Length: 2.5 mm
    - Stitch Width: 1.5 mm
    - Stitch Type: Stretch Zig-zag
    - Needle Recommendation: 75/11 Ballpoint/Stretch (Needle System: 130/705 H)
    - Presser Foot: Walking foot / Even feed
    - Safety Verification: [SAFE] Parameters verified within safe physical limits.
    
    SAFETY VERIFICATION AUDIT: [SAFE]
    - Needle Gauge Tested: EU 75 / US 11
    - Material Tested: polyester spandex jersey knit (200.0 GSM)
    - Operational Status: SAFE TO OPERATE
    - Engineering Assessment: Physical parameters within safe operating thresholds.
    
    **Setup Checklist:**
    1. Thread machine with presser foot UP.
    2. Install specified needle and verify flat side faces back.
    3. Set upper tension dial, stitch length, and stitch width to the indicated readout values.

==============================================================================
CALIPER PHYSICAL MACHINE DIAL READOUT [Brother SM3701]
==============================================================================
  Upper Tension Dial Setting : 3.5
  Stitch Length Knob / Dial  : 2.5 mm
  Stitch Width Knob / Dial   : 1.5 mm
  Stitch Selection Pattern   : Stretch Zig-zag
  Needle Gauge & System      : 75/11 Ballpoint/Stretch
  Presser Foot Attachment    : Walking foot / Even feed
==============================================================================
```

---

## 3. Half a Page: What Works, What Does Not Yet, and Next Steps

### What Works
1. **Deterministic Hardware Extraction from 50 Machines:** The system reliably ingests `caliper_sewing_machines_hardware_specs.xlsx`, extracting dial boundaries, bobbin mechanics, and shank types across 50 production sewing machines without hallucination.
2. **Four Real, Verified Domain Tools:** 
   - `lookup_sewing_machine_specs` (machine chassis query),
   - `calculate_fabric_calibration` (tension and stitch math),
   - `diagnose_stitch_defect` (physical troubleshooting for bird-nesting, skipped stitches, puckering),
   - `verify_safety_constraints` (needle deflection vs GSM boundaries).
3. **Multi-Provider Resilience & Offline Execution:** The harness runs locally against Ollama (`llama3.1:latest`, `qwen2.5:0.5b`), supports Google Gemini API, and includes a zero-latency deterministic fallback engine.
4. **Interactive Localhost Web Interface:** A browser-based interface running at `http://127.0.0.1:7860` renders dynamic SVG rotary dials (tension, stitch length, stitch width) that visually turn to calibrated values when the agent responds.
5. **Rigorous Test Suite:** 28 unit and integration tests passing in `< 0.25 seconds`.

### What Does Not Work Yet
1. **Unindexed Machine Web Scraping:** If a user specifies an unindexed, vintage, or rare machine not in the 50-machine database, the system currently falls back to a generic baseline rather than scraping PDF instruction manuals dynamically via DuckDuckGo.
2. **AST-Sandboxed Code Execution:** In the current prototype, tension scaling and physics calculations are computed via compiled Python functions rather than dynamically generated LLM code evaluated in an isolated REPL container.
3. **Multi-Agent Decoupling:** In accordance with the Milestone I rule ("Do not add a second agent without written justification"), the system currently runs as a single unified agent. The planned 5-node LangGraph topology (Machine Ingestion, Fabric Mechanics, Calibration REPL, Visualization, and Safety Critic) is scheduled for Milestone II.

### What We Will Do Next (Milestone II Roadmap)
1. **LangGraph 5-Node Architecture with XML Grounding:** Transition from a single loop to a stateful LangGraph multi-agent topology with context isolation between hardware parsing, fabric mechanics, and safety criticism.
2. **Sandboxed Python REPL Tool:** Implement an isolated code execution environment where the Calibration Agent generates Python snippets to solve complex stitch tension differential equations.
3. **Automated Internal Audit Nodes:** Implement post-task verification functions (`validate_machine_schema()`, `verify_fabric_physics()`, `audit_calibration_code()`) to mathematically check each node's output before state transitions.
4. **Manual Scraper Fallback:** Integrate BeautifulSoup and search tools to ingest unknown machine manuals on demand.

---

## 4. Exact Steps to Reproduce & Run Locally

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/aryadevkota/caliper-sewing-agent.git
cd Caliper_AgenticAI-FinalTermProject

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option A: Launch the Localhost Web Demo (Recommended)
```bash
python app.py
```
Open your browser to:
```
http://127.0.0.1:7860
```
- Select any of the **50 sewing machines** from the dropdown.
- Click any of the **Quick Scenario** buttons or type a custom query.
- Watch the **SVG Rotary Dials** turn and inspect the **Live Execution Trace Drawer**.

### Option B: Run the Command-Line Interface (CLI)
```bash
# Scenario 1: Fabric Calibration
python caliper_cli.py "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"

# Scenario 2: Defect Diagnostic
python caliper_cli.py --defect "Severe bird-nesting on underside of Singer 4423"

# Scenario 3: Safety Intercept
python caliper_cli.py --safety "14oz heavy denim flat-felled seam with 70/10 needle on Brother SM3701"
```

### Option C: Run the Automated Test Suite (28 Tests)
```bash
python -m unittest discover -s tests -v
```
All 28 tests will pass in `~0.2 seconds`.
