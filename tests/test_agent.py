"""tests/test_agent.py

End-to-end integration and unit tests for the Caliper Sewing Machine Setup & Calibration Agent.
Verifies all 3 core scenarios:
1. Fabric Calibration: 'Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam'
2. Defect Diagnosis: 'Severe bird-nesting on underside of Singer 4423'
3. Safety Constraint Audit: '14oz denim flat-felled seam with 70/10 needle on Brother SM3701'
Also verifies strict MAX_STEPS = 6 guardrails, trace schemas, and dial extraction.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from caliper.agent import (
    MAX_STEPS,
    AgentResult,
    CaliperAgent,
    extract_dial_settings,
    run_agent,
)
from caliper.tools import (
    OLLAMA_TOOLS,
    OPENAI_TOOLS,
    TOOL_DEFINITIONS,
    TOOLS,
    calculate_fabric_calibration,
    diagnose_stitch_defect,
    lookup_sewing_machine_specs,
    verify_safety_constraints,
)


class TestCaliperTools(unittest.TestCase):
    """Unit tests for caliper/tools.py wrappers and schemas."""

    def test_lookup_sewing_machine_specs(self):
        # Known model lookup
        specs_str = lookup_sewing_machine_specs("Brother SM3701")
        self.assertIn("MACHINE SPECIFICATIONS", specs_str)
        self.assertIn("Brother SM3701", specs_str)
        self.assertIn("brother_sm3701", specs_str)
        self.assertIn("Upper Tension Dial", specs_str)
        self.assertIn("Needle System: 130/705 H", specs_str)

        # Singer 4423 lookup
        singer_str = lookup_sewing_machine_specs("Singer 4423")
        self.assertIn("Singer Heavy Duty 4423", singer_str)
        self.assertIn("Top Drop-in", singer_str)

        # Missing machine query
        missing_str = lookup_sewing_machine_specs("UnknownBrand XYZ999")
        self.assertIn("MachineNotFound", missing_str)

    def test_calculate_fabric_calibration(self):
        cal_str = calculate_fabric_calibration(
            fabric_name="polyester spandex jersey knit",
            gsm_weight=200.0,
            stretch_pct=50.0,
            seam_type="side seam",
            machine_query="Brother SM3701",
        )
        self.assertIn("CALIBRATION RECOMMENDATIONS FOR", cal_str)
        self.assertIn("Upper Tension Dial: 3.5", cal_str)
        self.assertIn("Stitch Length: 2.5 mm", cal_str)
        self.assertIn("Stitch Width: 1.5 mm", cal_str)
        self.assertIn("Stretch Zig-zag", cal_str)
        self.assertIn("75/11 Ballpoint", cal_str)
        self.assertIn("Walking foot", cal_str)
        self.assertIn("[SAFE]", cal_str)

    def test_diagnose_stitch_defect(self):
        diag_str = diagnose_stitch_defect(
            defect_symptom="Severe bird-nesting on underside of Singer 4423",
            machine_query="Singer 4423",
        )
        self.assertIn("DEFECT DIAGNOSTIC REPORT", diag_str)
        self.assertIn("Bird-nesting", diag_str)
        self.assertIn("Root Cause", diag_str)
        self.assertIn("Corrective Action", diag_str)
        self.assertIn("presser foot", diag_str)
        self.assertIn("Singer Heavy Duty 4423", diag_str)

    def test_verify_safety_constraints(self):
        # Heavy denim deflection hazard
        hazard_str = verify_safety_constraints(needle_size_eu=70, fabric_gsm=474.7, fabric_type="14oz denim")
        self.assertIn("[CRITICAL]", hazard_str)
        self.assertIn("CRITICAL DEFLECTION HAZARD", hazard_str)
        self.assertIn("HAZARD DETECTED - HALT OPERATION", hazard_str)
        self.assertIn("100/16 or 110/18 Jeans/Denim", hazard_str)

        # Safe parameter verification
        safe_str = verify_safety_constraints(needle_size_eu=80, fabric_gsm=180.0, fabric_type="Cotton")
        self.assertIn("[SAFE]", safe_str)
        self.assertIn("SAFE TO OPERATE", safe_str)

    def test_tool_definitions_and_schemas(self):
        self.assertEqual(len(TOOLS), 4)
        self.assertEqual(len(TOOL_DEFINITIONS), 4)
        self.assertEqual(len(OPENAI_TOOLS), 4)
        self.assertEqual(len(OLLAMA_TOOLS), 4)

        for name, defn in TOOL_DEFINITIONS.items():
            self.assertIn("fn", defn)
            self.assertIn("name", defn)
            self.assertIn("description", defn)
            self.assertIn("parameters", defn)
            self.assertIn("openai_schema", defn)
            self.assertEqual(defn["openai_schema"]["type"], "function")
            self.assertEqual(defn["openai_schema"]["function"]["name"], name)


class TestCaliperAgentScenarios(unittest.TestCase):
    """End-to-end integration tests for the 3 core required scenarios."""

    def setUp(self):
        self.agent = CaliperAgent(provider="deterministic")

    def test_scenario_1_fabric_calibration(self):
        """Scenario 1: Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam."""
        goal = "Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam"
        result = self.agent.run(goal)

        # Verify structured result
        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.stopped_reason, "completed")
        self.assertGreaterEqual(len(result.trace), 2)
        self.assertLessEqual(len(result.trace), MAX_STEPS)

        # Verify machine context
        self.assertEqual(result.machine_context.get("machine_id"), "brother_sm3701")

        # Verify trace structure
        tool_names = [s["tool_name"] for s in result.trace if s["tool_name"]]
        self.assertIn("lookup_sewing_machine_specs", tool_names)
        self.assertIn("calculate_fabric_calibration", tool_names)

        for step in result.trace:
            self.assertIn("step", step)
            self.assertIn("thought", step)
            self.assertIn("tool_name", step)
            self.assertIn("tool_args", step)
            self.assertIn("observation", step)
            self.assertIn("answer", step)
            self.assertLessEqual(step["step"], MAX_STEPS)

        # Verify dials extraction
        dials = result.dials
        self.assertEqual(dials["tension"], 3.5)
        self.assertEqual(dials["stitch_length"], 2.5)
        self.assertEqual(dials["stitch_width"], 1.5)
        self.assertEqual(dials["stitch_type"], "Stretch Zig-zag")
        self.assertIn("75/11 Ballpoint", dials["needle"])
        self.assertIn("Walking foot", dials["foot"])

    def test_scenario_2_defect_diagnosis(self):
        """Scenario 2: Severe bird-nesting on underside of Singer 4423."""
        goal = "Severe bird-nesting on underside of Singer 4423"
        result = self.agent.run(goal, defect_mode=True)

        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.stopped_reason, "completed")
        self.assertGreaterEqual(len(result.trace), 2)
        self.assertLessEqual(len(result.trace), MAX_STEPS)

        # Verify machine context
        self.assertEqual(result.machine_context.get("machine_id"), "singer_hd_4423")

        # Verify trace has diagnose_stitch_defect
        tool_names = [s["tool_name"] for s in result.trace if s["tool_name"]]
        self.assertIn("diagnose_stitch_defect", tool_names)

        # Verify final answer includes root cause & presser foot UP guidance
        self.assertIn("Bird-nesting", result.final_answer)
        self.assertIn("presser foot", result.final_answer.lower())

        # Verify dials
        self.assertEqual(result.dials["tension"], 5.0)
        self.assertEqual(result.dials["stitch_length"], 2.5)
        self.assertIn("Universal", result.dials["needle"])

    def test_scenario_3_safety_constraint_audit(self):
        """Scenario 3: 14oz denim flat-felled seam with 70/10 needle on Brother SM3701."""
        goal = "14oz denim flat-felled seam with 70/10 needle on Brother SM3701"
        result = self.agent.run(goal, safety_mode=True)

        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.stopped_reason, "completed")
        self.assertGreaterEqual(len(result.trace), 3)
        self.assertLessEqual(len(result.trace), MAX_STEPS)

        # Verify trace contains safety audit
        tool_names = [s["tool_name"] for s in result.trace if s["tool_name"]]
        self.assertIn("verify_safety_constraints", tool_names)
        self.assertIn("calculate_fabric_calibration", tool_names)

        # Verify critical deflection hazard caught in trace observation
        safety_obs = [s["observation"] for s in result.trace if s["tool_name"] == "verify_safety_constraints"][0]
        self.assertIn("[CRITICAL]", safety_obs)
        self.assertIn("CRITICAL DEFLECTION HAZARD", safety_obs)

        # Verify dials recommend safe denim needle
        self.assertIn("Jeans/Denim", result.dials["needle"])
        self.assertIn("100/16 or 110/18", result.dials["needle"])
        self.assertGreaterEqual(result.dials["tension"], 5.0)
        self.assertIn("Walking foot", result.dials["foot"])


class TestAgentGuardrailsAndEdgeCases(unittest.TestCase):
    """Tests strictly guarded MAX_STEPS = 6 and error recovery."""

    def test_max_steps_guard(self):
        agent = CaliperAgent(provider="deterministic", max_steps=2)
        result = agent.run("Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam")
        # Should not exceed max_steps = 2
        self.assertLessEqual(len(result.trace), 2)
        for step in result.trace:
            self.assertLessEqual(step["step"], 2)

    def test_empty_query(self):
        agent = CaliperAgent(provider="deterministic")
        result = agent.run("")
        self.assertEqual(result.stopped_reason, "error")
        self.assertIn("ERROR", result.final_answer)

    def test_extract_dial_settings_from_various_inputs(self):
        # 1. Direct text
        txt = (
            "- Upper Tension Dial: 4.5 (Dial (0-9))\n"
            "- Stitch Length: 3.0 mm\n"
            "- Stitch Width: 0.0 mm\n"
            "- Stitch Type: Straight\n"
            "- Needle Recommendation: 90/14 Universal\n"
            "- Presser Foot: Standard J / All-purpose\n"
        )
        d = extract_dial_settings(txt)
        self.assertEqual(d["tension"], 4.5)
        self.assertEqual(d["stitch_length"], 3.0)
        self.assertEqual(d["stitch_width"], 0.0)
        self.assertEqual(d["stitch_type"], "Straight")
        self.assertEqual(d["needle"], "90/14 Universal")
        self.assertEqual(d["foot"], "Standard J / All-purpose")

        # 2. List of steps
        steps = [
            {"step": 1, "observation": "- Upper Tension Dial: 3.5\n- Stitch Length: 2.5 mm\n- Stitch Width: 1.5 mm\n- Stitch Type: Stretch Zig-zag\n- Needle Recommendation: 75/11 Ballpoint/Stretch\n- Presser Foot: Walking foot"}
        ]
        d2 = extract_dial_settings(steps)
        self.assertEqual(d2["tension"], 3.5)
        self.assertEqual(d2["stitch_length"], 2.5)
        self.assertEqual(d2["stitch_width"], 1.5)
        self.assertEqual(d2["stitch_type"], "Stretch Zig-zag")
        self.assertIn("75/11", d2["needle"])
        self.assertIn("Walking foot", d2["foot"])

    def test_ollama_execution_if_available(self):
        """Tests local Ollama execution when active on localhost:11434."""
        agent = CaliperAgent(provider="ollama", model="qwen2.5:0.5b")
        if not agent._check_ollama_available():
            self.skipTest("Ollama is not running locally.")

        result = agent.run("Brother SM3701, polyester spandex jersey knit 200 GSM 50% stretch, side seam")
        self.assertIsInstance(result, AgentResult)
        self.assertLessEqual(len(result.trace), MAX_STEPS)
        self.assertIn("Brother SM3701", result.final_answer)


if __name__ == "__main__":
    unittest.main()
