from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

import assumptions  # noqa: E402
import economics  # noqa: E402
import power  # noqa: E402
import simulate  # noqa: E402


class AnalysisTests(unittest.TestCase):
    def test_baseline_and_margin(self) -> None:
        self.assertAlmostEqual(assumptions.baseline_txn_per_window(), 4.2)
        self.assertAlmostEqual(assumptions.contribution_margin_per_txn(), 2.125)

    def test_star_exposure_definitions(self) -> None:
        self.assertAlmostEqual(economics.stars_at_risk("flow"), 35.7)
        self.assertAlmostEqual(economics.stars_at_risk("stock"), 76.5)

    def test_breakeven_at_ten_percent_breakage_rescue(self) -> None:
        self.assertAlmostEqual(economics.breakeven_lift(0.10, "flow"), 0.030084, places=5)
        self.assertAlmostEqual(economics.breakeven_lift(0.10, "stock"), 0.052941, places=5)

    def test_power_requirement(self) -> None:
        expected = {5: 3332, 3: 4346, 2: 5613, 1: 9415}
        for dispersion, n in expected.items():
            self.assertEqual(power.required_n_per_arm(0.05, dispersion), n)

    def test_decision_rule_catches_failure_mode(self) -> None:
        working = simulate.decision_row("A_personalisation_works")
        failure = simulate.decision_row("B_engagement_without_behaviour")
        failure_summary = simulate.scenario_summary(
            "B_engagement_without_behaviour"
        ).query("arm == 'C_personalised'").iloc[0]
        self.assertAlmostEqual(working["net_contribution"], 1193.55, places=2)
        self.assertAlmostEqual(failure["activation_rate"], 0.1704, places=4)
        self.assertAlmostEqual(failure["lift_vs_holdout"], 0.0193, places=4)
        self.assertAlmostEqual(failure["net_contribution"], -7209.975, places=3)
        self.assertLess(failure_summary["ci_low"], 0)
        self.assertGreater(failure_summary["ci_high"], 0)
        self.assertIn("DO NOT SCALE", failure["verdict"])

    def test_all_registered_inputs_have_valid_labels(self) -> None:
        valid_labels = {
            assumptions.PUBLIC_FACT,
            assumptions.CASE_ASSUMPTION,
            assumptions.PROPOSED_TARGET,
            assumptions.CALCULATED,
        }
        register = assumptions.assumption_register()
        self.assertGreater(len(register), 30)
        self.assertTrue(set(register["label"]).issubset(valid_labels))


if __name__ == "__main__":
    unittest.main()
