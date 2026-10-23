"""caliper.tools

Universal Sewing Machine Setup & Calibration Agent Tools.
Wraps hardware_db and mechanics engines into clean, human-readable structured tools
with JSON/Ollama/OpenAI schema definitions.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

from caliper.hardware_db import get_machine, list_all_machines
from caliper.mechanics import (
    EU_TO_US_NEEDLE_SIZES,
    calculate_fabric_calibration as calc_calibration_engine,
    diagnose_stitch_defect as diagnose_defect_engine,
    verify_safety_constraints as verify_safety_engine,
)


def lookup_sewing_machine_specs(model_query: str = "", **kwargs: Any) -> str:
    """Look up technical specifications, tension dial bounds, needle systems, and
    bobbin mechanics for a sewing machine model.

    Args:
        model_query: Name, model number, or brand of sewing machine (e.g., 'Brother SM3701', 'Singer 4423', 'Janome HD1000').
    """
    q_val = model_query or kwargs.get("machine_query") or kwargs.get("model") or kwargs.get("machine") or kwargs.get("query") or ""
    if not q_val or not str(q_val).strip():
        return "ERROR: Please provide a sewing machine model query (e.g. 'Brother SM3701', 'Singer 4423')."

    q_str = str(q_val).strip()
    specs = get_machine(q_str)

    if not specs:
        # Suggest available machine brands or common matches
        return (
            f"MachineNotFound: No machine matching '{q_str}' was found in the database. "
            "Please check the model number (e.g., 'Brother SM3701', 'Singer Heavy Duty 4423', 'Janome HD1000')."
        )

    brand = specs.get("brand", "Unknown")
    model = specs.get("model_name", "Unknown")
    mid = specs.get("machine_id", "unknown")
    category = specs.get("machine_category") or specs.get("category", "Standard")
    ctrl = specs.get("control_type", "Mechanical")
    bobbin_sys = specs.get("bobbin_system", "Drop-in")
    bobbin_cls = specs.get("bobbin_class", "Class 15")
    hook = specs.get("hook_type", "Rotary")
    needle_sys = specs.get("needle_system", "130/705 H")
    min_n = specs.get("min_needle_size_eu", 65)
    max_n = specs.get("max_needle_size_eu", 110)
    t_type = specs.get("tension_dial_type", "Dial (0-9)")
    t_min = specs.get("tension_min", 0.0)
    t_max = specs.get("tension_max", 9.0)
    t_def = specs.get("tension_default", 4.0)
    len_min = specs.get("stitch_length_min_mm", 0.0)
    len_max = specs.get("stitch_length_max_mm", 4.0)
    wid_min = specs.get("stitch_width_min_mm", 0.0)
    wid_max = specs.get("stitch_width_max_mm", 5.0)
    spm = specs.get("max_speed_spm", 800)
    stitches = specs.get("total_stitch_count", 1)
    foot_sys = specs.get("presser_foot_system", "Snap-on")
    press_adj = specs.get("presser_foot_pressure_adj", "Manual")
    feed = specs.get("feed_dog_system", "Standard")
    drop_feed = specs.get("drop_feed_support", "No")

    lines = [
        f"MACHINE SPECIFICATIONS: {brand} {model} [{mid}]",
        f"- Brand & Model: {brand} {model}",
        f"- Category / Control: {category} | {ctrl}",
        f"- Bobbin Mechanism: {bobbin_sys} ({bobbin_cls}, Hook: {hook})",
        f"- Needle System: {needle_sys} (Needle Size Range: EU {min_n} - {max_n})",
        f"- Upper Tension Dial: {t_type} | Default: {t_def:.1f} | Dial Bounds: {t_min:.1f} - {t_max:.1f}",
        f"- Stitch Length Range: {len_min:.1f} - {len_max:.1f} mm",
        f"- Stitch Width Range: {wid_min:.1f} - {wid_max:.1f} mm",
        f"- Presser Foot System: {foot_sys} (Pressure Adjustment: {press_adj})",
        f"- Feed Dogs / Drop Feed: {feed} | Drop Feed: {drop_feed}",
        f"- Max Speed: {spm} SPM | Built-in Stitches: {stitches}",
    ]
    return "\n".join(lines)


def calculate_fabric_calibration(
    fabric_name: str = "",
    gsm_weight: float = 200.0,
    stretch_pct: float = 0.0,
    seam_type: str = "standard",
    machine_query: str = "",
    **kwargs: Any,
) -> str:
    """Calculate optimal mechanical dial settings (upper tension, stitch length, stitch width),
    needle gauge/type, and presser foot for a specific fabric and seam.

    Args:
        fabric_name: Name or description of fabric (e.g. 'polyester spandex jersey knit', '14oz denim', 'silk chiffon').
        gsm_weight: Fabric weight in grams per square meter (g/m²). Default is 200.0.
        stretch_pct: Fabric stretch percentage (0.0 to 100.0+). Default is 0.0.
        seam_type: Construction seam type ('standard', 'side seam', 'basting', 'topstitch', 'overcast', 'heavy').
        machine_query: Optional sewing machine name or model (e.g. 'Brother SM3701', 'Singer 4423').
    """
    fname = fabric_name or kwargs.get("fabric") or kwargs.get("material") or kwargs.get("fabric_type") or ""
    if not fname or not str(fname).strip():
        return "ERROR: fabric_name is required for fabric calibration."

    fname = str(fname).strip()

    # Resilient fallback parameter extraction if full prompt was packed into fabric_name
    raw_gsm = gsm_weight if gsm_weight != 200.0 else (kwargs.get("gsm") or kwargs.get("weight") or 200.0)
    try:
        gsm_val = float(raw_gsm)
    except (ValueError, TypeError):
        gsm_val = 200.0

    raw_stretch = stretch_pct if stretch_pct != 0.0 else (kwargs.get("stretch") or kwargs.get("stretch_percentage") or 0.0)
    try:
        stretch_val = float(raw_stretch)
    except (ValueError, TypeError):
        stretch_val = 0.0

    stype = seam_type or kwargs.get("seam") or "standard"
    mquery = machine_query or kwargs.get("model_query") or kwargs.get("machine") or ""

    # Auto-detect GSM if ounces mentioned (1 oz/yd² = ~33.906 g/m²)
    if gsm_val == 200.0:
        oz_match = re.search(r"(\d+(?:\.\d+)?)\s*oz", fname, re.IGNORECASE)
        gsm_match = re.search(r"(\d+(?:\.\d+)?)\s*gsm", fname, re.IGNORECASE)
        if gsm_match:
            gsm_val = float(gsm_match.group(1))
        elif oz_match:
            gsm_val = float(oz_match.group(1)) * 33.906

    # Auto-detect stretch if in fabric_name and default 0.0 was passed
    if stretch_val == 0.0:
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*stretch", fname, re.IGNORECASE)
        if pct_match:
            stretch_val = float(pct_match.group(1))

    # Look up machine specs if query supplied
    machine_specs = None
    machine_label = "Universal / Generic Standard"
    if mquery and str(mquery).strip():
        machine_specs = get_machine(str(mquery).strip())
        if machine_specs:
            machine_label = f"{machine_specs['brand']} {machine_specs['model_name']} ({machine_specs['machine_id']})"
        else:
            machine_label = f"Query '{mquery}' (specs not in DB, used standard bounds)"

    # Compute calibration via physical mechanics engine
    cal = calc_calibration_engine(
        fabric_name=fname,
        gsm=gsm_val,
        stretch_pct=stretch_val,
        seam_type=stype,
        machine_specs=machine_specs,
    )

    lines = [
        f"CALIBRATION RECOMMENDATIONS FOR: {fname}",
        f"- Target Machine: {machine_label}",
        f"- Fabric Parameters: {cal['gsm']:.1f} GSM | {cal['stretch_pct']:.1f}% Stretch | Seam: {cal['seam_type']}",
        f"- Upper Tension Dial: {cal['tension_dial_value']:.1f} ({cal['tension_dial_type']})",
        f"- Stitch Length: {cal['stitch_length_mm']:.1f} mm",
        f"- Stitch Width: {cal['stitch_width_mm']:.1f} mm",
        f"- Stitch Type: {cal['stitch_type']}",
        f"- Needle Recommendation: {cal['needle_recommendation']} (Needle System: {cal['needle_system']})",
        f"- Presser Foot: {cal['presser_foot']}",
    ]

    audit = cal.get("safety_audit", {})
    if not audit.get("is_safe", True):
        lines.append(f"- SAFETY ALERT [{audit.get('severity', 'WARNING')}]: {audit.get('hazard_message', '')}")
        fix = audit.get("recommended_fix", {})
        if "action" in fix:
            lines.append(f"- Corrective Action Required: {fix['action']}")
    else:
        lines.append("- Safety Verification: [SAFE] Parameters verified within safe physical limits.")

    return "\n".join(lines)


def diagnose_stitch_defect(
    defect_symptom: str = "",
    machine_query: str = "",
    **kwargs: Any,
) -> str:
    """Diagnose sewing stitch defects (bird-nesting, skipped stitches, seam puckering,
    needle breakage) and prescribe mechanical corrective actions.

    Args:
        defect_symptom: Description of the stitch problem (e.g. 'Severe bird-nesting on underside', 'skipped stitches', 'puckering').
        machine_query: Optional sewing machine model to integrate machine-specific bobbin and tension mechanics.
    """
    symptom = defect_symptom or kwargs.get("symptom") or kwargs.get("defect") or kwargs.get("issue") or ""
    if not symptom or not str(symptom).strip():
        return "ERROR: defect_symptom is required for stitch diagnosis."

    symptom = str(symptom).strip()
    mquery = machine_query or kwargs.get("machine") or kwargs.get("model") or ""

    machine_specs = None
    if mquery and str(mquery).strip():
        machine_specs = get_machine(str(mquery).strip())

    diag = diagnose_defect_engine(symptom=symptom, machine_specs=machine_specs)

    lines = [
        f"DEFECT DIAGNOSTIC REPORT: {diag['defect_name']} (Category: {diag['defect_category']})",
        f"- Reported Symptom: {diag['symptom']}",
        f"- Probable Root Cause: {diag['root_cause']}",
        f"- Primary Corrective Action: {diag['corrective_action']}",
        "- Prescribed Action Steps:",
    ]
    for i, step in enumerate(diag.get("action_steps", []), 1):
        lines.append(f"  {i}. {step}")

    if diag.get("machine_context"):
        lines.append("- Machine Hardware Context:")
        for note in diag["machine_context"]:
            lines.append(f"  * {note}")

    return "\n".join(lines)


def verify_safety_constraints(
    needle_size_eu: int = 70,
    fabric_gsm: float = 200.0,
    fabric_type: str = "",
    **kwargs: Any,
) -> str:
    """Audit physical sewing safety limits to prevent needle deflection shank snapping
    or fabric blowout.

    Args:
        needle_size_eu: European needle gauge number (e.g. 60, 70, 80, 90, 100, 110).
        fabric_gsm: Fabric weight in grams per square meter (g/m²). (e.g. 475 for 14oz denim, 200 for jersey, 60 for chiffon).
        fabric_type: Optional fabric name or description (e.g. '14oz denim', 'silk chiffon').
    """
    raw_needle = needle_size_eu or kwargs.get("needle_size") or kwargs.get("needle") or 70
    raw_gsm = fabric_gsm or kwargs.get("gsm") or kwargs.get("weight") or 200.0
    ftype = fabric_type or kwargs.get("fabric") or kwargs.get("material") or ""

    try:
        eu_size = int(raw_needle)
        gsm_val = float(raw_gsm)
    except (ValueError, TypeError) as exc:
        return f"ERROR: Invalid numeric arguments to verify_safety_constraints: {exc}"

    audit = verify_safety_engine(needle_size_eu=eu_size, fabric_gsm=gsm_val, fabric_type=ftype)
    us_size = EU_TO_US_NEEDLE_SIZES.get(eu_size, round((eu_size - 60) * 0.1 + 8))
    ftype_label = fabric_type.strip() if fabric_type else "Fabric"

    lines = [
        f"SAFETY VERIFICATION AUDIT: [{audit['severity']}]",
        f"- Needle Gauge Tested: EU {eu_size} / US {us_size}",
        f"- Material Tested: {ftype_label} ({gsm_val:.1f} GSM)",
        f"- Operational Status: {'SAFE TO OPERATE' if audit['is_safe'] else 'HAZARD DETECTED - HALT OPERATION'}",
        f"- Engineering Assessment: {audit['hazard_message']}",
    ]

    fix = audit.get("recommended_fix", {})
    if fix:
        if "action" in fix:
            lines.append(f"- Corrective Action Required: {fix['action']}")
        if "recommended_needle" in fix:
            lines.append(f"- Recommended Safe Needle: {fix['recommended_needle']}")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Tool Dictionary & Schemas (OpenAI, Ollama, Gemini compatible)
# -----------------------------------------------------------------------------

TOOLS: Dict[str, Callable[..., str]] = {
    "lookup_sewing_machine_specs": lookup_sewing_machine_specs,
    "calculate_fabric_calibration": calculate_fabric_calibration,
    "diagnose_stitch_defect": diagnose_stitch_defect,
    "verify_safety_constraints": verify_safety_constraints,
}

TOOL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "lookup_sewing_machine_specs": {
        "fn": lookup_sewing_machine_specs,
        "name": "lookup_sewing_machine_specs",
        "description": "Look up sewing machine hardware specifications, tension dial bounds, needle systems, and bobbin mechanics.",
        "parameters": {
            "type": "object",
            "properties": {
                "model_query": {
                    "type": "string",
                    "description": "Model name, number, or brand of sewing machine (e.g. 'Brother SM3701', 'Singer 4423', 'HD1000').",
                }
            },
            "required": ["model_query"],
        },
        "openai_schema": {
            "type": "function",
            "function": {
                "name": "lookup_sewing_machine_specs",
                "description": "Look up sewing machine hardware specifications, tension dial bounds, needle systems, and bobbin mechanics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_query": {
                            "type": "string",
                            "description": "Model name, number, or brand of sewing machine (e.g. 'Brother SM3701', 'Singer 4423', 'HD1000').",
                        }
                    },
                    "required": ["model_query"],
                },
            },
        },
    },
    "calculate_fabric_calibration": {
        "fn": calculate_fabric_calibration,
        "name": "calculate_fabric_calibration",
        "description": "Calculate calibrated machine dial settings (tension, stitch length, stitch width), needle gauge/type, and presser foot for a fabric.",
        "parameters": {
            "type": "object",
            "properties": {
                "fabric_name": {
                    "type": "string",
                    "description": "Name or description of fabric (e.g. 'polyester spandex jersey knit', '14oz denim', 'silk chiffon').",
                },
                "gsm_weight": {
                    "type": "number",
                    "description": "Fabric weight in grams per square meter (g/m²). Default is 200.0.",
                },
                "stretch_pct": {
                    "type": "number",
                    "description": "Fabric stretch percentage from 0 to 100+. Default is 0.0.",
                },
                "seam_type": {
                    "type": "string",
                    "description": "Construction seam type ('standard', 'side seam', 'basting', 'topstitch', 'overcast', 'heavy').",
                },
                "machine_query": {
                    "type": "string",
                    "description": "Optional machine name or model (e.g. 'Brother SM3701', 'Singer 4423').",
                },
            },
            "required": ["fabric_name"],
        },
        "openai_schema": {
            "type": "function",
            "function": {
                "name": "calculate_fabric_calibration",
                "description": "Calculate calibrated machine dial settings (tension, stitch length, stitch width), needle gauge/type, and presser foot for a fabric.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fabric_name": {
                            "type": "string",
                            "description": "Name or description of fabric (e.g. 'polyester spandex jersey knit', '14oz denim', 'silk chiffon').",
                        },
                        "gsm_weight": {
                            "type": "number",
                            "description": "Fabric weight in grams per square meter (g/m²). Default is 200.0.",
                        },
                        "stretch_pct": {
                            "type": "number",
                            "description": "Fabric stretch percentage from 0 to 100+. Default is 0.0.",
                        },
                        "seam_type": {
                            "type": "string",
                            "description": "Construction seam type ('standard', 'side seam', 'basting', 'topstitch', 'overcast', 'heavy').",
                        },
                        "machine_query": {
                            "type": "string",
                            "description": "Optional machine name or model (e.g. 'Brother SM3701', 'Singer 4423').",
                        },
                    },
                    "required": ["fabric_name"],
                },
            },
        },
    },
    "diagnose_stitch_defect": {
        "fn": diagnose_stitch_defect,
        "name": "diagnose_stitch_defect",
        "description": "Diagnose sewing stitch defects (bird-nesting, skipped stitches, puckering, needle breakage) and prescribe mechanical corrective actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "defect_symptom": {
                    "type": "string",
                    "description": "Description of the stitch defect or symptom (e.g. 'Severe bird-nesting on underside of Singer 4423', 'skipped stitches').",
                },
                "machine_query": {
                    "type": "string",
                    "description": "Optional sewing machine model to contextualize bobbin and tension mechanics.",
                },
            },
            "required": ["defect_symptom"],
        },
        "openai_schema": {
            "type": "function",
            "function": {
                "name": "diagnose_stitch_defect",
                "description": "Diagnose sewing stitch defects (bird-nesting, skipped stitches, puckering, needle breakage) and prescribe mechanical corrective actions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "defect_symptom": {
                            "type": "string",
                            "description": "Description of the stitch defect or symptom (e.g. 'Severe bird-nesting on underside of Singer 4423', 'skipped stitches').",
                        },
                        "machine_query": {
                            "type": "string",
                            "description": "Optional sewing machine model to contextualize bobbin and tension mechanics.",
                        },
                    },
                    "required": ["defect_symptom"],
                },
            },
        },
    },
    "verify_safety_constraints": {
        "fn": verify_safety_constraints,
        "name": "verify_safety_constraints",
        "description": "Audit physical sewing safety limits to prevent needle deflection shank snapping or fabric blowout.",
        "parameters": {
            "type": "object",
            "properties": {
                "needle_size_eu": {
                    "type": "integer",
                    "description": "European needle gauge number (e.g. 60, 70, 80, 90, 100, 110).",
                },
                "fabric_gsm": {
                    "type": "number",
                    "description": "Fabric weight in grams per square meter (g/m²). (e.g. 475 for 14oz denim, 200 for jersey).",
                },
                "fabric_type": {
                    "type": "string",
                    "description": "Optional fabric name or description (e.g. '14oz denim').",
                },
            },
            "required": ["needle_size_eu", "fabric_gsm"],
        },
        "openai_schema": {
            "type": "function",
            "function": {
                "name": "verify_safety_constraints",
                "description": "Audit physical sewing safety limits to prevent needle deflection shank snapping or fabric blowout.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "needle_size_eu": {
                            "type": "integer",
                            "description": "European needle gauge number (e.g. 60, 70, 80, 90, 100, 110).",
                        },
                        "fabric_gsm": {
                            "type": "number",
                            "description": "Fabric weight in grams per square meter (g/m²). (e.g. 475 for 14oz denim, 200 for jersey).",
                        },
                        "fabric_type": {
                            "type": "string",
                            "description": "Optional fabric name or description (e.g. '14oz denim').",
                        },
                    },
                    "required": ["needle_size_eu", "fabric_gsm"],
                },
            },
        },
    },
}

OPENAI_TOOLS: List[Dict[str, Any]] = [
    defn["openai_schema"] for defn in TOOL_DEFINITIONS.values()
]

# For Ollama: list of raw Python functions or schemas
OLLAMA_TOOLS = list(TOOLS.values())

__all__ = [
    "lookup_sewing_machine_specs",
    "calculate_fabric_calibration",
    "diagnose_stitch_defect",
    "verify_safety_constraints",
    "TOOLS",
    "TOOL_DEFINITIONS",
    "OPENAI_TOOLS",
    "OLLAMA_TOOLS",
]
