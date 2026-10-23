"""caliper.hardware_db

Hardware specifications database for sewing machines.
Loads machine specifications from Excel, provides fast indexing,
fuzzy model searching, and schema validation.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import openpyxl


# Global caches for fast retrieval
_CACHED_MACHINES: Optional[Dict[str, Dict[str, Any]]] = None
_CACHED_CANONICAL: Optional[Dict[str, Dict[str, Any]]] = None
_CACHED_FILE_PATH: Optional[Path] = None


def _find_specs_file(file_path: Optional[str] = None) -> Path:
    """Locates the hardware specifications spreadsheet."""
    if file_path:
        p = Path(file_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Hardware specs file not found at: {file_path}")

    # Standard search paths
    candidates = [
        Path.cwd() / "caliper_sewing_machines_hardware_specs.xlsx",
        Path(__file__).resolve().parent / "caliper_sewing_machines_hardware_specs.xlsx",
        Path(__file__).resolve().parent.parent / "caliper_sewing_machines_hardware_specs.xlsx",
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    raise FileNotFoundError(
        "Could not locate 'caliper_sewing_machines_hardware_specs.xlsx'. "
        "Please provide the file path explicitly."
    )


def _normalize_token(text: str) -> str:
    """Removes non-alphanumeric characters and converts to lowercase."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def _generate_aliases(specs: Dict[str, Any]) -> List[str]:
    """Generates normalized lookup aliases for a machine."""
    aliases: List[str] = []
    mid = specs.get("machine_id", "")
    brand = specs.get("brand", "")
    model = specs.get("model_name", "")

    if mid:
        aliases.append(mid)
        aliases.append(_normalize_token(mid))

    if model:
        aliases.append(model)
        aliases.append(_normalize_token(model))
        # Add model numbers (e.g. '4423' from 'Heavy Duty 4423')
        digits = re.findall(r"\d+", model)
        for d in digits:
            aliases.append(d)

    if brand and model:
        aliases.append(f"{brand} {model}")
        aliases.append(_normalize_token(f"{brand} {model}"))

        # Common short aliases (e.g. 'Singer 4423' for 'Singer Heavy Duty 4423')
        digits = re.findall(r"\d+", model)
        for d in digits:
            aliases.append(f"{brand} {d}")
            aliases.append(_normalize_token(f"{brand} {d}"))

    return aliases


def load_machines(file_path: Optional[str] = None, force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
    """Loads all machine specifications from the Excel file.

    Returns:
        Dict mapping machine_id and normalized names/aliases to machine specs.
    """
    global _CACHED_MACHINES, _CACHED_CANONICAL, _CACHED_FILE_PATH

    path = _find_specs_file(file_path)

    if not force_reload and _CACHED_MACHINES is not None and _CACHED_FILE_PATH == path:
        return _CACHED_MACHINES

    wb = openpyxl.load_workbook(path, data_only=True)
    sheet = wb.active

    headers = [str(cell.value).strip() for cell in sheet[1]]

    canonical: Dict[str, Dict[str, Any]] = {}
    mapping: Dict[str, Dict[str, Any]] = {}

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        raw_dict = dict(zip(headers, row))
        mid = str(raw_dict.get("machine_id", "")).strip()
        if not mid:
            continue

        # Convert types safely
        specs: Dict[str, Any] = {
            "machine_id": mid,
            "brand": str(raw_dict.get("brand", "")).strip(),
            "model_name": str(raw_dict.get("model_name", "")).strip(),
            "machine_category": str(raw_dict.get("machine_category", "")).strip(),
            "category": str(raw_dict.get("machine_category", "")).strip(),
            "control_type": str(raw_dict.get("control_type", "")).strip(),
            "bobbin_system": str(raw_dict.get("bobbin_system", "")).strip(),
            "bobbin_class": str(raw_dict.get("bobbin_class", "")).strip(),
            "hook_type": str(raw_dict.get("hook_type", "")).strip(),
            "needle_system": str(raw_dict.get("needle_system", "")).strip(),
            "min_needle_size_eu": int(raw_dict.get("min_needle_size_eu", 65)),
            "max_needle_size_eu": int(raw_dict.get("max_needle_size_eu", 110)),
            "max_speed_spm": int(raw_dict.get("max_speed_spm", 800)),
            "feed_dog_system": str(raw_dict.get("feed_dog_system", "")).strip(),
            "drop_feed_support": str(raw_dict.get("drop_feed_support", "")).strip(),
            "presser_foot_system": str(raw_dict.get("presser_foot_system", "")).strip(),
            "presser_foot_pressure_adj": str(raw_dict.get("presser_foot_pressure_adj", "")).strip(),
            "tension_dial_type": str(raw_dict.get("tension_dial_type", "")).strip(),
            "tension_min": float(raw_dict.get("tension_min", 0)),
            "tension_max": float(raw_dict.get("tension_max", 9)),
            "tension_default": float(raw_dict.get("tension_default", 4)),
            "tension_range": (float(raw_dict.get("tension_min", 0)), float(raw_dict.get("tension_max", 9))),
            "stitch_length_min_mm": float(raw_dict.get("stitch_length_min_mm", 0)),
            "stitch_length_max_mm": float(raw_dict.get("stitch_length_max_mm", 4)),
            "stitch_width_min_mm": float(raw_dict.get("stitch_width_min_mm", 0)),
            "stitch_width_max_mm": float(raw_dict.get("stitch_width_max_mm", 5)),
            "total_stitch_count": int(raw_dict.get("total_stitch_count", 1)),
            "buttonhole_style": str(raw_dict.get("buttonhole_style", "")).strip(),
            "free_arm_available": str(raw_dict.get("free_arm_available", "")).strip(),
            "thread_cutter_type": str(raw_dict.get("thread_cutter_type", "")).strip(),
            "auto_needle_threader": str(raw_dict.get("auto_needle_threader", "")).strip(),
            "dial_ui_layout_spec": str(raw_dict.get("dial_ui_layout_spec", "")).strip(),
        }

        canonical[mid] = specs
        mapping[mid] = specs

        # Register aliases in mapping
        for alias in _generate_aliases(specs):
            key = alias.strip().lower()
            norm = _normalize_token(alias)
            if key not in mapping:
                mapping[key] = specs
            if norm not in mapping:
                mapping[norm] = specs

    _CACHED_CANONICAL = canonical
    _CACHED_MACHINES = mapping
    _CACHED_FILE_PATH = path

    return mapping


def list_all_machines(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns a list of unique machine specification dictionaries.

    Suitable for dropdown menus, catalogs, and hardware UI tables.
    """
    global _CACHED_CANONICAL
    if _CACHED_CANONICAL is None:
        load_machines(file_path)
    return list(_CACHED_CANONICAL.values()) if _CACHED_CANONICAL else []


def get_machine(query: str, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Searches for a sewing machine by machine_id, model name, brand + model,
    or fuzzy/case-insensitive match.

    Examples:
        get_machine('brother_sm3701') -> Brother SM3701
        get_machine('SM3701') -> Brother SM3701
        get_machine('4423') -> Singer Heavy Duty 4423
        get_machine('HD1000') -> Janome HD1000
        get_machine('Brother SM3701') -> Brother SM3701
        get_machine('Singer Heavy Duty 4423') -> Singer Heavy Duty 4423
    """
    if not query or not isinstance(query, str):
        return None

    mapping = load_machines(file_path)
    q_str = query.strip()
    q_lower = q_str.lower()
    q_norm = _normalize_token(q_str)

    # 1. Direct match in mapping
    if q_str in mapping:
        return mapping[q_str]
    if q_lower in mapping:
        return mapping[q_lower]
    if q_norm in mapping:
        return mapping[q_norm]

    all_machines = list_all_machines(file_path)

    # 2. Check exact matches against model_name or machine_id
    for m in all_machines:
        if m["machine_id"].lower() == q_lower:
            return m
        if m["model_name"].lower() == q_lower:
            return m
        if _normalize_token(m["model_name"]) == q_norm:
            return m

    # 3. Check combined brand + model matches
    for m in all_machines:
        combined = f"{m['brand']} {m['model_name']}"
        if _normalize_token(combined) == q_norm:
            return m

    # 4. Token subset matching (e.g., 'Singer 4423' in 'Singer Heavy Duty 4423')
    q_tokens = [tok for tok in re.split(r"[^a-z0-9]+", q_lower) if tok]
    best_candidate = None
    best_score = 0
    for m in all_machines:
        target_text = f"{m['brand']} {m['model_name']} {m['machine_id']}".lower()
        target_tokens = re.split(r"[^a-z0-9]+", target_text)
        # Check if all query tokens appear in target tokens or as substrings
        matches = sum(1 for q in q_tokens if any(q in t for t in target_tokens))
        if matches == len(q_tokens):
            score = matches * 10 - len(target_tokens)
            if score > best_score:
                best_score = score
                best_candidate = m

    if best_candidate is not None:
        return best_candidate

    # 5. Fuzzy matching with difflib
    # Build list of candidate display names and IDs
    candidates: Dict[str, Dict[str, Any]] = {}
    for m in all_machines:
        candidates[f"{m['brand']} {m['model_name']}".lower()] = m
        candidates[m["model_name"].lower()] = m
        candidates[m["machine_id"].lower()] = m

    matches = difflib.get_close_matches(q_lower, candidates.keys(), n=1, cutoff=0.55)
    if matches:
        return candidates[matches[0]]

    # Also try fuzzy match on normalized string
    norm_candidates = {_normalize_token(k): v for k, v in candidates.items()}
    norm_matches = difflib.get_close_matches(q_norm, norm_candidates.keys(), n=1, cutoff=0.6)
    if norm_matches:
        return norm_candidates[norm_matches[0]]

    return None


def validate_machine_schema(specs: Dict[str, Any]) -> bool:
    """Validates that all required hardware fields are present and typed correctly.

    Checks:
        - machine_id, brand, model_name (non-empty strings)
        - tension limits (min, max, default numbers with min < max)
        - stitch length and width limits (min <= max)
        - needle size limits (positive min <= max)
        - needle and bobbin systems (non-empty strings)
    """
    if not isinstance(specs, dict):
        return False

    required_str_fields = [
        "machine_id",
        "brand",
        "model_name",
        "needle_system",
        "bobbin_system",
    ]
    for field in required_str_fields:
        val = specs.get(field)
        if not isinstance(val, str) or not val.strip():
            return False

    # Check category
    category = specs.get("machine_category") or specs.get("category")
    if not isinstance(category, str) or not category.strip():
        return False

    # Numeric fields validation
    num_fields = [
        "tension_min",
        "tension_max",
        "stitch_length_min_mm",
        "stitch_length_max_mm",
        "stitch_width_min_mm",
        "stitch_width_max_mm",
        "min_needle_size_eu",
        "max_needle_size_eu",
    ]
    for field in num_fields:
        val = specs.get(field)
        if not isinstance(val, (int, float)):
            return False

    # Boundary checks
    if specs["tension_min"] >= specs["tension_max"]:
        return False

    if specs["stitch_length_min_mm"] > specs["stitch_length_max_mm"]:
        return False

    if specs["stitch_width_min_mm"] > specs["stitch_width_max_mm"]:
        return False

    if specs["min_needle_size_eu"] <= 0 or specs["max_needle_size_eu"] <= 0:
        return False

    if specs["min_needle_size_eu"] > specs["max_needle_size_eu"]:
        return False

    if "tension_default" in specs:
        t_def = specs["tension_default"]
        if not isinstance(t_def, (int, float)):
            return False
        if not (specs["tension_min"] <= t_def <= specs["tension_max"]):
            return False

    return True
