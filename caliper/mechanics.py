"""caliper.mechanics

Physical mechanics, calibration equations, defect diagnostic rules,
and sewing safety constraints for Caliper.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# Needle sizing mapping: European (metric / hundredths of mm) to US numbering
EU_TO_US_NEEDLE_SIZES: Dict[int, int] = {
    60: 8,
    65: 9,
    70: 10,
    75: 11,
    80: 12,
    85: 13,
    90: 14,
    95: 15,
    100: 16,
    105: 17,
    110: 18,
    120: 19,
}


def _needle_label(eu_size: int, needle_type: str) -> str:
    """Formats needle recommendation label, e.g. '75/11 Ballpoint/Stretch'."""
    us_size = EU_TO_US_NEEDLE_SIZES.get(eu_size, round((eu_size - 60) * 0.1 + 8))
    # Clean type presentation
    type_label = needle_type.replace(" / ", "/").strip()
    return f"{eu_size}/{us_size} {type_label}"


def verify_safety_constraints(
    needle_size_eu: int, fabric_gsm: float, fabric_type: str = ""
) -> Dict[str, Any]:
    """Audits physical safety limits for needle gauge and fabric weight.

    Rules:
    - If fabric_gsm >= 350 and needle_size_eu <= 75:
      CRITICAL DEFLECTION HAZARD. HALT: High risk of needle deflection, striking throat plate,
      and violent shank snapping. Prescribe needle >= 100 (100/16 or 110/18 Jeans/Denim).
    - If fabric_gsm <= 80 and needle_size_eu >= 90:
      FABRIC DAMAGE HAZARD. Hole punch blowout / fiber tearing. Prescribe needle 60/8 or 70/10 Microtex.

    Returns:
        {'is_safe': bool, 'severity': 'SAFE'|'WARNING'|'CRITICAL', 'hazard_message': str, 'recommended_fix': dict}
    """
    try:
        eu_size = int(needle_size_eu)
        gsm = float(fabric_gsm)
    except (ValueError, TypeError) as exc:
        return {
            "is_safe": False,
            "severity": "CRITICAL",
            "hazard_message": f"Invalid parameter types for safety verification: {exc}",
            "recommended_fix": {"action": "Ensure needle_size_eu is int and fabric_gsm is float."},
        }

    # 1. Critical deflection hazard on heavy materials
    if gsm >= 350.0 and eu_size <= 75:
        return {
            "is_safe": False,
            "severity": "CRITICAL",
            "hazard_message": (
                "CRITICAL DEFLECTION HAZARD. HALT: High risk of needle deflection, "
                "striking throat plate, and violent shank snapping."
            ),
            "recommended_fix": {
                "min_needle_size_eu": 100,
                "recommended_needle": "100/16 or 110/18 Jeans/Denim",
                "action": "Prescribe needle >= 100 (100/16 or 110/18 Jeans/Denim).",
            },
        }

    # 2. Fabric puncture / fiber tear hazard on delicate materials
    if gsm <= 80.0 and eu_size >= 90:
        return {
            "is_safe": False,
            "severity": "WARNING",
            "hazard_message": (
                "FABRIC DAMAGE HAZARD. Hole punch blowout / fiber tearing."
            ),
            "recommended_fix": {
                "max_needle_size_eu": 70,
                "recommended_needle": "60/8 or 70/10 Microtex",
                "action": "Prescribe needle 60/8 or 70/10 Microtex.",
            },
        }

    return {
        "is_safe": True,
        "severity": "SAFE",
        "hazard_message": "Physical parameters within safe operating thresholds.",
        "recommended_fix": {},
    }


def calculate_fabric_calibration(
    fabric_name: str,
    gsm: float,
    stretch_pct: float,
    seam_type: str = "standard",
    machine_specs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Computes recommended needle system & size, upper tension dial value scaled to
    the machine's tension bounds, stitch type, stitch length & width, and presser foot.

    Args:
        fabric_name: Name or description of fabric (e.g. 'Cotton Jersey', '14oz Denim', 'Silk Chiffon')
        gsm: Fabric weight in grams per square meter (g/m²)
        stretch_pct: Fabric stretch percentage (0.0 - 100.0+)
        seam_type: Construction seam type ('standard', 'edge', 'overcast', 'basting', 'topstitch', 'heavy', 'reinforce')
        machine_specs: Optional machine specifications dictionary from hardware_db.

    Returns:
        Dictionary containing comprehensive physical calibration recommendations.
    """
    fname_lower = str(fabric_name).lower()
    gsm_val = float(gsm)
    stretch_val = float(stretch_pct)
    st_lower = str(seam_type).lower().strip()

    # Needle system: default standard home sewing needle system
    needle_sys = "130/705 H"
    if machine_specs and "needle_system" in machine_specs:
        needle_sys = machine_specs["needle_system"]

    # 1. Determine Needle Type & Size
    is_leather = any(k in fname_lower for k in ["leather", "vinyl", "suede", "pleather", "oilcloth"])
    is_knit = stretch_val > 20.0 or any(
        k in fname_lower for k in ["knit", "jersey", "spandex", "lycra", "rib", "interlock", "terry", "fleece"]
    )
    is_denim_heavy = gsm_val >= 350.0 or any(
        k in fname_lower for k in ["denim", "jeans", "canvas", "duck", "twill", "corduroy"]
    )
    is_delicate = (gsm_val < 120.0 and stretch_val <= 10.0) or any(
        k in fname_lower for k in ["silk", "chiffon", "organza", "voile", "batiste", "satin", "microfiber"]
    )

    if is_leather:
        needle_type = "Leather"
        needle_size_eu = 90 if gsm_val < 300.0 else 100
    elif is_knit:
        needle_type = "Ballpoint / Stretch"
        if gsm_val < 150.0:
            needle_size_eu = 70
        elif gsm_val <= 260.0:
            needle_size_eu = 75
        elif gsm_val <= 350.0:
            needle_size_eu = 80
        else:
            needle_size_eu = 90
    elif is_denim_heavy:
        needle_type = "Jeans / Denim"
        if gsm_val >= 450.0:
            needle_size_eu = 110
        elif gsm_val >= 350.0:
            needle_size_eu = 100
        else:
            needle_size_eu = 90
    elif is_delicate:
        needle_type = "Microtex"
        if gsm_val <= 70.0:
            needle_size_eu = 60
        elif gsm_val < 120.0:
            needle_size_eu = 70
        else:
            needle_size_eu = 75
    else:
        needle_type = "Universal"
        if gsm_val < 150.0:
            needle_size_eu = 70
        elif gsm_val <= 250.0:
            needle_size_eu = 80
        elif gsm_val <= 350.0:
            needle_size_eu = 90
        else:
            needle_size_eu = 100

    needle_size_us = EU_TO_US_NEEDLE_SIZES.get(needle_size_eu, 12)
    needle_rec = _needle_label(needle_size_eu, needle_type)

    # 2. Determine Stitch Type
    if st_lower in ("overcast", "edge", "finishing", "serge"):
        stitch_type = "Overcast"
    elif stretch_val > 20.0 or is_knit:
        if st_lower in ("heavy", "crotch", "reinforce", "activewear_high_stress"):
            stitch_type = "Triple Straight"
        else:
            stitch_type = "Stretch Zig-zag"
    elif stretch_val > 10.0:
        stitch_type = "Stretch Zig-zag"
    else:
        if st_lower in ("heavy", "reinforce", "heavy_duty"):
            stitch_type = "Triple Straight"
        else:
            stitch_type = "Straight"

    # 3. Determine Stitch Length and Width
    if stitch_type == "Straight":
        if gsm_val < 120.0:
            stitch_length = 2.0
        elif gsm_val <= 300.0:
            stitch_length = 2.5
        elif gsm_val < 450.0:
            stitch_length = 3.0
        else:
            stitch_length = 3.5
        stitch_width = 0.0
    elif stitch_type == "Stretch Zig-zag":
        stitch_length = 2.5
        stitch_width = 1.5
    elif stitch_type == "Triple Straight":
        stitch_length = 2.8
        stitch_width = 0.0
    elif stitch_type == "Overcast":
        stitch_length = 2.0
        stitch_width = 4.5
    else:
        stitch_length = 2.5
        stitch_width = 0.0

    # Specific seam overrides
    if st_lower == "basting":
        stitch_length = 4.0
        stitch_width = 0.0
    elif st_lower == "topstitch":
        stitch_length = 3.5
        stitch_width = 0.0

    # Clamp stitch dimensions to machine limits if provided
    if machine_specs:
        len_min = float(machine_specs.get("stitch_length_min_mm", 0.0))
        len_max = float(machine_specs.get("stitch_length_max_mm", 4.0))
        wid_min = float(machine_specs.get("stitch_width_min_mm", 0.0))
        wid_max = float(machine_specs.get("stitch_width_max_mm", 5.0))
        stitch_length = round(max(len_min, min(stitch_length, len_max)), 1)
        stitch_width = round(max(wid_min, min(stitch_width, wid_max)), 1)

    # 4. Determine Presser Foot
    if is_leather:
        presser_foot = "Teflon foot"
    elif stretch_val > 20.0 or is_knit:
        presser_foot = "Walking foot / Even feed"
    elif gsm_val >= 350.0 or st_lower in ("heavy", "quilting", "multi-layer"):
        presser_foot = "Walking foot / Even feed"
    elif stitch_type == "Overcast":
        presser_foot = "Overcasting foot"
    else:
        presser_foot = "Standard J / All-purpose"

    # 5. Calculate Upper Tension Dial Value
    # Reference baseline dial (standard 0-9 scale, nominal default is 4.0)
    base_tension = 4.0

    # Fabric weight delta
    if gsm_val < 100.0:
        base_tension -= 0.8  # prevent puckering on sheers
    elif gsm_val < 150.0:
        base_tension -= 0.4
    elif gsm_val >= 450.0:
        base_tension += 1.2  # high tension to seat thread in ultra heavy plies
    elif gsm_val >= 350.0:
        base_tension += 0.8  # heavy denim / canvas
    elif gsm_val > 250.0:
        base_tension += 0.3

    # Stretch delta: loosen slightly so stitches can expand
    if stretch_val > 20.0:
        base_tension -= 0.5

    # Seam type delta
    if st_lower == "basting":
        base_tension = 2.0
    elif st_lower == "gathering":
        base_tension = 2.2
    elif st_lower == "topstitch":
        base_tension += 0.6
    elif st_lower in ("overcast", "edge"):
        base_tension = 3.8

    # Scale tension to the machine's dial range
    if machine_specs:
        dial_min = float(machine_specs.get("tension_min", 0.0))
        dial_max = float(machine_specs.get("tension_max", 9.0))
        dial_def = float(machine_specs.get("tension_default", (dial_min + dial_max) / 2.0))
        # Scale the delta relative to the machine's range span vs reference 9.0
        range_span = max(1.0, dial_max - dial_min)
        scale_ratio = range_span / 9.0
        scaled_t = dial_def + (base_tension - 4.0) * scale_ratio
        tension_value = round(max(dial_min, min(scaled_t, dial_max)), 1)
        tension_dial_type = machine_specs.get("tension_dial_type", f"Dial ({int(dial_min)}-{int(dial_max)})")
    else:
        tension_value = round(max(0.0, min(base_tension, 9.0)), 1)
        tension_dial_type = "Dial (0-9)"

    # 6. Safety Verification
    safety_audit = verify_safety_constraints(needle_size_eu, gsm_val, fabric_name)

    return {
        "fabric_name": fabric_name,
        "gsm": gsm_val,
        "stretch_pct": stretch_val,
        "seam_type": seam_type,
        "needle_system": needle_sys,
        "needle_type": needle_type,
        "needle_size_eu": needle_size_eu,
        "needle_size_us": needle_size_us,
        "needle_recommendation": needle_rec,
        "tension_dial_value": tension_value,
        "tension_dial_type": tension_dial_type,
        "stitch_type": stitch_type,
        "stitch_length_mm": stitch_length,
        "stitch_width_mm": stitch_width,
        "presser_foot": presser_foot,
        "safety_audit": safety_audit,
    }


def diagnose_stitch_defect(symptom: str, machine_specs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyzes sewing stitch defects and prescribes precise mechanical corrective actions.

    Defects analyzed:
    - Bird-nesting / looping underside / tangled bobbin
    - Skipped stitches
    - Seam puckering
    - Needle breakage
    """
    s_clean = str(symptom).strip()
    s_lower = s_clean.lower()

    # Match defect category
    is_nesting = any(
        k in s_lower
        for k in [
            "bird-nesting",
            "bird nesting",
            "birdnesting",
            "looping underside",
            "looping bottom",
            "looping under",
            "tangled bobbin",
            "tangle under",
            "tangled underside",
            "thread jam under",
            "loops on underside",
            "loops underneath",
            "nesting",
            "bunching underneath",
            "clump underneath",
        ]
    )

    is_skipped = any(
        k in s_lower
        for k in [
            "skipped stitches",
            "skipped stitch",
            "skipping stitches",
            "skipping stitch",
            "skips stitches",
            "missing stitches",
            "missed stitch",
            "drop stitches",
        ]
    )

    is_puckering = any(
        k in s_lower
        for k in [
            "seam puckering",
            "puckering",
            "pucker",
            "puckered seam",
            "fabric bunching along seam",
            "tunneling",
            "wrinkled seam",
            "gathered seam",
        ]
    )

    is_breakage = any(
        k in s_lower
        for k in [
            "needle breakage",
            "needle breaking",
            "broken needle",
            "snapped needle",
            "needle snaps",
            "needle hit",
            "striking plate",
            "needle bent",
        ]
    )

    machine_notes = []
    if machine_specs:
        mid = machine_specs.get("machine_id", "machine")
        brand = machine_specs.get("brand", "")
        model = machine_specs.get("model_name", "")
        b_sys = machine_specs.get("bobbin_system", "")
        b_class = machine_specs.get("bobbin_class", "")
        n_sys = machine_specs.get("needle_system", "130/705 H")
        t_dial = machine_specs.get("tension_dial_type", "")
        machine_notes.append(f"Target machine: {brand} {model} ({mid})")
        if b_sys or b_class:
            machine_notes.append(f"Bobbin mechanism: {b_sys} utilizing {b_class} bobbins.")
        if n_sys:
            machine_notes.append(f"Needle specification standard: {n_sys}.")
        if t_dial:
            machine_notes.append(f"Tension dial layout: {t_dial}.")

    if is_nesting:
        return {
            "symptom": s_clean,
            "defect_category": "bird-nesting",
            "defect_name": "Bird-nesting / Underside Thread Looping",
            "root_cause": (
                "Upper thread tension too loose, upper thread not seated between tension discs "
                "(presser foot was not raised during threading), bobbin misthreaded."
            ),
            "corrective_action": (
                "Re-thread upper thread with presser foot UP, increase upper tension by +1.0 to +1.5."
            ),
            "action_steps": [
                "Raise the presser foot lever UP fully before re-threading (this opens the upper tension discs).",
                "Completely re-thread the upper thread path, ensuring the thread engages the take-up lever.",
                "Increase upper thread tension dial by +1.0 to +1.5.",
                "Remove and inspect the bobbin. Ensure the thread unspools counter-clockwise ('P' orientation) and clicks into the bobbin tension spring notch.",
            ],
            "machine_context": machine_notes,
        }

    if is_skipped:
        return {
            "symptom": s_clean,
            "defect_category": "skipped-stitches",
            "defect_name": "Skipped Stitches",
            "root_cause": (
                "Needle blunt or wrong needle type for stretch fabric (e.g. Universal used instead "
                "of Ballpoint/Stretch), needle bent, needle inserted backwards."
            ),
            "corrective_action": (
                "Swap to Ballpoint/Stretch needle, verify flat side to back."
            ),
            "action_steps": [
                "Swap to a genuine Ballpoint or Stretch needle if sewing knit/elastic materials.",
                "Inspect needle tip for burrs or bends; install a fresh needle (standard lifetime is 6-8 sewing hours).",
                "Verify the flat side of the needle shank faces the BACK of the machine (away from operator).",
                "Loosen needle clamp screw, push the needle fully upward until it hits the needle stop pin, then re-tighten securely.",
            ],
            "machine_context": machine_notes,
        }

    if is_puckering:
        return {
            "symptom": s_clean,
            "defect_category": "seam-puckering",
            "defect_name": "Seam Puckering",
            "root_cause": (
                "Upper tension too tight, needle too large for fine fabric, feed dog pulling unevenly."
            ),
            "corrective_action": (
                "Reduce upper tension by -1.0, reduce needle gauge to 65/9 or 70/10."
            ),
            "action_steps": [
                "Reduce upper tension dial setting by -1.0.",
                "Reduce needle gauge to 65/9 or 70/10 Microtex for fine or lightweight materials.",
                "Slightly increase stitch length (e.g., from 2.0mm to 2.5mm) to decrease stitch density per inch.",
                "Ensure feed dogs are clean of lint and advance fabric without manual pulling or dragging.",
            ],
            "machine_context": machine_notes,
        }

    if is_breakage:
        return {
            "symptom": s_clean,
            "defect_category": "needle-breakage",
            "defect_name": "Needle Breakage / Needle Strike",
            "root_cause": (
                "Fabric too thick for fine needle (e.g. 70/10 needle on 14oz denim), "
                "bent needle striking needle plate, pulling fabric manually while sewing."
            ),
            "corrective_action": (
                "Switch to 100/16 Jeans needle, let feed dogs advance material naturally."
            ),
            "action_steps": [
                "Switch to 100/16 or 110/18 Jeans/Denim needle equipped with a reinforced blade for heavy plies.",
                "Let feed dogs advance material naturally—never push or pull fabric manually while needle is engaged.",
                "Turn the handwheel toward you manually to verify needle clears the needle plate hole and presser foot groove without contact.",
                "Verify presser foot screw and needle clamp screw are tightened securely.",
            ],
            "machine_context": machine_notes,
        }

    # Fallback for general unclassified defects
    return {
        "symptom": s_clean,
        "defect_category": "unknown",
        "defect_name": "Unspecified Stitch Irregularity",
        "root_cause": (
            "Thread tension imbalance, improper needle/fabric pairing, or incorrect thread path routing."
        ),
        "corrective_action": (
            "Perform baseline 3-point reset: re-thread upper path with presser foot UP, insert a fresh needle appropriate for fabric weight, and verify bobbin installation."
        ),
        "action_steps": [
            "Re-thread with presser foot UP.",
            "Insert fresh needle matching fabric type and GSM.",
            "Verify bobbin seating and check upper tension dial against machine standard.",
        ],
        "machine_context": machine_notes,
    }
