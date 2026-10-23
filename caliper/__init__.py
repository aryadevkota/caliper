"""Caliper Sewing Hardware, Mechanics & Agent Engine.

Provides sewing machine hardware catalog specifications, physical calibration equations,
defect diagnostics, real-time safety constraint verification, and the Caliper ReAct Agent.
"""

from caliper.agent import (
    MAX_STEPS,
    AgentResult,
    CaliperAgent,
    extract_dial_settings,
    run_agent,
)
from caliper.hardware_db import (
    get_machine,
    list_all_machines,
    load_machines,
    validate_machine_schema,
)
from caliper.mechanics import (
    calculate_fabric_calibration,
    diagnose_stitch_defect,
    verify_safety_constraints,
)
from caliper.tools import (
    OLLAMA_TOOLS,
    OPENAI_TOOLS,
    TOOL_DEFINITIONS,
    TOOLS,
    lookup_sewing_machine_specs,
)

__all__ = [
    # Database
    "load_machines",
    "get_machine",
    "list_all_machines",
    "validate_machine_schema",
    # Mechanics Engine
    "calculate_fabric_calibration",
    "diagnose_stitch_defect",
    "verify_safety_constraints",
    # Tools & Schemas
    "lookup_sewing_machine_specs",
    "TOOLS",
    "TOOL_DEFINITIONS",
    "OPENAI_TOOLS",
    "OLLAMA_TOOLS",
    # Agent & Orchestration
    "MAX_STEPS",
    "AgentResult",
    "CaliperAgent",
    "run_agent",
    "extract_dial_settings",
]
