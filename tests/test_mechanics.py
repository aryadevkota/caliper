"""tests/test_mechanics.py

Unit and integration tests for Caliper Hardware Specifications Database
and Mechanics / Calibration / Defect Diagnostic / Safety Engine.
"""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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


class TestHardwareDB(unittest.TestCase):
    """Tests for caliper.hardware_db."""

    def test_load_machines(self):
        machines = load_machines()
        self.assertIsInstance(machines, dict)
        self.assertGreater(len(machines), 50)
        # Verify key machines exist
        self.assertIn("brother_sm3701", machines)
        self.assertIn("singer_hd_4423", machines)
        self.assertIn("janome_hd1000", machines)
        self.assertIn("brother_pq1500sl", machines)

    def test_list_all_machines(self):
        machine_list = list_all_machines()
        self.assertEqual(len(machine_list), 50)
        for m in machine_list:
            self.assertIn("machine_id", m)
            self.assertIn("brand", m)
            self.assertIn("model_name", m)
            self.assertIn("category", m)
            self.assertIn("tension_range", m)
            self.assertIn("bobbin_system", m)
            self.assertIn("needle_system", m)
            self.assertTrue(validate_machine_schema(m))

    def test_validate_machine_schema_valid_and_invalid(self):
        machine = get_machine("brother_sm3701")
        self.assertIsNotNone(machine)
        self.assertTrue(validate_machine_schema(machine))

        # Test corrupt schema cases
        corrupt_no_id = machine.copy()
        del corrupt_no_id["machine_id"]
        self.assertFalse(validate_machine_schema(corrupt_no_id))

        corrupt_tension = machine.copy()
        corrupt_tension["tension_min"] = 10
        corrupt_tension["tension_max"] = 2
        self.assertFalse(validate_machine_schema(corrupt_tension))

        corrupt_needle = machine.copy()
        corrupt_needle["min_needle_size_eu"] = 120
        corrupt_needle["max_needle_size_eu"] = 65
        self.assertFalse(validate_machine_schema(corrupt_needle))

        self.assertFalse(validate_machine_schema("not-a-dict"))

    def test_get_machine_exact_and_fuzzy(self):
        # Exact machine_id
        m1 = get_machine("brother_sm3701")
        self.assertIsNotNone(m1)
        self.assertEqual(m1["machine_id"], "brother_sm3701")

        # Model name lookups
        m2 = get_machine("SM3701")
        self.assertIsNotNone(m2)
        self.assertEqual(m2["machine_id"], "brother_sm3701")

        m3 = get_machine("4423")
        self.assertIsNotNone(m3)
        self.assertEqual(m3["machine_id"], "singer_hd_4423")

        m4 = get_machine("HD1000")
        self.assertIsNotNone(m4)
        self.assertEqual(m4["machine_id"], "janome_hd1000")

        # Fuzzy / Brand + Model lookups
        m5 = get_machine("Brother SM3701")
        self.assertIsNotNone(m5)
        self.assertEqual(m5["machine_id"], "brother_sm3701")

        m6 = get_machine("Singer Heavy Duty 4423")
        self.assertIsNotNone(m6)
        self.assertEqual(m6["machine_id"], "singer_hd_4423")

        m7 = get_machine("Singer 4423")
        self.assertIsNotNone(m7)
        self.assertEqual(m7["machine_id"], "singer_hd_4423")

        m8 = get_machine("TL-2000Qi")
        self.assertIsNotNone(m8)
        self.assertEqual(m8["machine_id"], "juki_tl2000qi")

        # Nonexistent lookup
        self.assertIsNone(get_machine("NonExistentSewingMachineXYZ999"))
        self.assertIsNone(get_machine(""))


class TestMechanicsSafety(unittest.TestCase):
    """Tests for verify_safety_constraints in caliper.mechanics."""

    def test_critical_deflection_hazard(self):
        # Heavy denim (400 GSM) with fine needle 70 EU (<= 75)
        result = verify_safety_constraints(needle_size_eu=70, fabric_gsm=400, fabric_type="14oz Denim")
        self.assertFalse(result["is_safe"])
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertIn("CRITICAL DEFLECTION HAZARD", result["hazard_message"])
        self.assertIn("HALT", result["hazard_message"])
        self.assertGreaterEqual(result["recommended_fix"]["min_needle_size_eu"], 100)
        self.assertIn("100/16", result["recommended_fix"]["recommended_needle"])

    def test_fabric_damage_hazard(self):
        # Delicate silk (50 GSM <= 80) with thick needle 100 EU (>= 90)
        result = verify_safety_constraints(needle_size_eu=100, fabric_gsm=50, fabric_type="Silk Chiffon")
        self.assertFalse(result["is_safe"])
        self.assertEqual(result["severity"], "WARNING")
        self.assertIn("FABRIC DAMAGE HAZARD", result["hazard_message"])
        self.assertIn("fiber tearing", result["hazard_message"])
        self.assertLessEqual(result["recommended_fix"]["max_needle_size_eu"], 70)
        self.assertIn("Microtex", result["recommended_fix"]["recommended_needle"])

    def test_safe_configuration(self):
        # Medium cotton (180 GSM) with size 80 EU needle
        result = verify_safety_constraints(needle_size_eu=80, fabric_gsm=180, fabric_type="Cotton Calico")
        self.assertTrue(result["is_safe"])
        self.assertEqual(result["severity"], "SAFE")
        self.assertEqual(result["recommended_fix"], {})


class TestMechanicsFabricCalibration(unittest.TestCase):
    """Tests for calculate_fabric_calibration in caliper.mechanics."""

    def test_knit_fabric_high_stretch(self):
        # Knits with stretch > 20%
        specs = get_machine("brother_sm3701")
        cal = calculate_fabric_calibration(
            fabric_name="Spandex Jersey Knit",
            gsm=200,
            stretch_pct=45,
            seam_type="standard",
            machine_specs=specs,
        )
        self.assertEqual(cal["needle_size_eu"], 75)
        self.assertEqual(cal["needle_size_us"], 11)
        self.assertIn("Ballpoint/Stretch", cal["needle_recommendation"])
        self.assertEqual(cal["stitch_type"], "Stretch Zig-zag")
        self.assertIn("Walking foot", cal["presser_foot"])
        # Knit tension should be relaxed below nominal default 4.0
        self.assertLess(cal["tension_dial_value"], 4.0)
        self.assertTrue(cal["safety_audit"]["is_safe"])

    def test_heavy_denim(self):
        # Denim > 350 GSM
        specs = get_machine("singer_hd_4423")
        cal = calculate_fabric_calibration(
            fabric_name="14oz Raw Denim",
            gsm=400,
            stretch_pct=0,
            seam_type="standard",
            machine_specs=specs,
        )
        self.assertEqual(cal["needle_size_eu"], 100)
        self.assertEqual(cal["needle_size_us"], 16)
        self.assertIn("Jeans", cal["needle_recommendation"])
        self.assertEqual(cal["stitch_type"], "Straight")
        self.assertGreaterEqual(cal["stitch_length_mm"], 3.0)
        # Denim tension should be higher than nominal 4.0 to seat stitches
        self.assertGreater(cal["tension_dial_value"], 4.0)
        self.assertIn("Walking foot", cal["presser_foot"])
        self.assertTrue(cal["safety_audit"]["is_safe"])

    def test_light_silk_woven(self):
        # Silk / light woven < 120 GSM
        specs = get_machine("janome_hd1000")
        cal = calculate_fabric_calibration(
            fabric_name="Silk Georgette",
            gsm=60,
            stretch_pct=0,
            seam_type="standard",
            machine_specs=specs,
        )
        self.assertEqual(cal["needle_size_eu"], 60)
        self.assertIn("Microtex", cal["needle_recommendation"])
        self.assertEqual(cal["stitch_type"], "Straight")
        self.assertEqual(cal["stitch_length_mm"], 2.0)
        # Tension should be lower to avoid puckering
        self.assertLess(cal["tension_dial_value"], 4.0)
        self.assertTrue(cal["safety_audit"]["is_safe"])

    def test_tension_scaling_different_machines(self):
        # Brother SM3701 has 0-9 dial (span 9)
        m_sm3701 = get_machine("brother_sm3701")
        # Brother PQ1500SL has 1-8 dial (span 7)
        m_pq1500 = get_machine("brother_pq1500sl")

        cal_std = calculate_fabric_calibration("14oz Heavy Canvas", 420, 0, machine_specs=m_sm3701)
        cal_semi = calculate_fabric_calibration("14oz Heavy Canvas", 420, 0, machine_specs=m_pq1500)

        # Both should be clamped within their respective ranges
        self.assertGreaterEqual(cal_std["tension_dial_value"], 0)
        self.assertLessEqual(cal_std["tension_dial_value"], 9)

        self.assertGreaterEqual(cal_semi["tension_dial_value"], 1)
        self.assertLessEqual(cal_semi["tension_dial_value"], 8)

    def test_leather_and_specialty_fabrics(self):
        cal = calculate_fabric_calibration("Lambskin Leather", 280, 0)
        self.assertEqual(cal["needle_type"], "Leather")
        self.assertEqual(cal["presser_foot"], "Teflon foot")


class TestMechanicsDefectDiagnostics(unittest.TestCase):
    """Tests for diagnose_stitch_defect in caliper.mechanics."""

    def test_bird_nesting_diagnostic(self):
        diag = diagnose_stitch_defect("huge bird-nesting clump under fabric")
        self.assertEqual(diag["defect_category"], "bird-nesting")
        self.assertIn("Upper thread tension too loose", diag["root_cause"])
        self.assertIn("presser foot was not raised during threading", diag["root_cause"])
        self.assertIn("presser foot UP", diag["corrective_action"])
        self.assertIn("+1.0 to +1.5", diag["corrective_action"])

        # Alternate symptom keywords
        diag2 = diagnose_stitch_defect("looping underside")
        self.assertEqual(diag2["defect_category"], "bird-nesting")

        diag3 = diagnose_stitch_defect("tangled bobbin thread")
        self.assertEqual(diag3["defect_category"], "bird-nesting")

    def test_skipped_stitches_diagnostic(self):
        diag = diagnose_stitch_defect("skipped stitches on activewear leggings")
        self.assertEqual(diag["defect_category"], "skipped-stitches")
        self.assertIn("Needle blunt or wrong needle type for stretch fabric", diag["root_cause"])
        self.assertIn("Ballpoint/Stretch", diag["corrective_action"])
        self.assertIn("flat side to back", diag["corrective_action"])

    def test_seam_puckering_diagnostic(self):
        diag = diagnose_stitch_defect("severe seam puckering on rayon blouse")
        self.assertEqual(diag["defect_category"], "seam-puckering")
        self.assertIn("Upper tension too tight", diag["root_cause"])
        self.assertIn("reduce upper tension by -1.0", diag["corrective_action"].lower())
        self.assertIn("65/9 or 70/10", diag["corrective_action"])

    def test_needle_breakage_diagnostic(self):
        diag = diagnose_stitch_defect("needle breakage when sewing hem on jeans")
        self.assertEqual(diag["defect_category"], "needle-breakage")
        self.assertIn("Fabric too thick for fine needle", diag["root_cause"])
        self.assertIn("switch to 100/16 jeans needle", diag["corrective_action"].lower())
        self.assertIn("feed dogs advance material naturally", diag["corrective_action"].lower())


if __name__ == "__main__":
    unittest.main()
