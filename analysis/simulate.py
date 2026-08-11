"""Seeded three-arm simulations and pre-registered decision machinery.

The scenario inputs live in :mod:`assumptions`; every reported statistic is
then calculated from the generated member-level records. These are simulated
case-study outcomes, never Starbucks performance data.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import assumptions
import economics


SEED = assumptions.A["simulation_seed"].value
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCENARIOS = assumptions.SIMULATION_SCENARIOS


SUMMARY_COLUMNS = [
    "arm",
    "n",
    "txn_per_member",
    "activation_rate",
    "optout_rate",
    "lift_vs_holdout",
    "ci_low",
    "ci_high",
    "p_value",
    "significant",
    "evidence_label",
]


def _rebalance_counts(
    counts: np.ndarray, target_total: int, rng: np.random.Generator
) -> np.ndarray:
    """Preserve count dispersion while matching the documented scenario mean."""

    counts = counts.astype(int, copy=True)
    difference = target_total - int(counts.sum())
    while difference > 0:
        batch = min(difference, len(counts))
        indices = rng.choice(len(counts), size=batch, replace=False)
        counts[indices] += 1
        difference -= batch
    while difference < 0:
        eligible = np.flatnonzero(counts > 0)
        batch = min(-difference, len(eligible))
        indices = rng.choice(eligible, size=batch, replace=False)
        counts[indices] -= 1
        difference += batch
    return counts


def _member_arm(
    scenario: str,
    arm: str,
    mean_transactions: float,
    activation_rate: float,
    optout_rate: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n = assumptions.A["pilot_members_per_arm"].value
    dispersion_k = assumptions.A["simulation_dispersion_k"].value
    probability = dispersion_k / (dispersion_k + mean_transactions)
    transactions = rng.negative_binomial(dispersion_k, probability, size=n)
    transactions = _rebalance_counts(
        transactions, int(round(mean_transactions * n)), rng
    )

    activated = np.zeros(n, dtype=np.int8)
    activation_count = int(round(activation_rate * n))
    if activation_count:
        activated[rng.choice(n, activation_count, replace=False)] = 1

    opted_out = np.zeros(n, dtype=np.int8)
    optout_count = int(round(optout_rate * n))
    if optout_count:
        opted_out[rng.choice(n, optout_count, replace=False)] = 1

    return pd.DataFrame(
        {
            "scenario": scenario,
            "member_id": [f"{scenario[:1]}-{arm[:1]}-{i:05d}" for i in range(n)],
            "arm": arm,
            "transactions_12w": transactions,
            "activated": activated,
            "opted_out": opted_out,
            "evidence_label": assumptions.CALCULATED,
        }
    )


@lru_cache(maxsize=None)
def _generate_member_data_cached(name: str) -> pd.DataFrame:
    if name not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {name}")
    scenario_number = list(SCENARIOS).index(name)
    stride = assumptions.A["simulation_scenario_seed_stride"].value
    rng = np.random.default_rng(SEED + scenario_number * stride)
    pieces = []
    for arm, parameters in SCENARIOS[name]["arms"].items():
        pieces.append(
            _member_arm(
                name,
                arm,
                parameters["transactions"].value,
                parameters["activation"].value,
                parameters["optout"].value,
                rng,
            )
        )
    return pd.concat(pieces, ignore_index=True)


def generate_member_data(name: str) -> pd.DataFrame:
    """Return a defensive copy of deterministic member-level outcomes."""

    return _generate_member_data_cached(name).copy()


def _comparison(treatment: pd.Series, holdout: pd.Series) -> dict[str, float | bool]:
    baseline = float(holdout.mean())
    difference = float(treatment.mean() - baseline)
    standard_error = float(
        np.sqrt(treatment.var(ddof=1) / len(treatment) + holdout.var(ddof=1) / len(holdout))
    )
    z_score = difference / standard_error
    ci_level = assumptions.A["simulation_ci_level"].value
    critical_value = norm.ppf(1 - (1 - ci_level) / 2)
    return {
        "lift_vs_holdout": difference / baseline,
        "ci_low": (difference - critical_value * standard_error) / baseline,
        "ci_high": (difference + critical_value * standard_error) / baseline,
        "p_value": float(2 * norm.sf(abs(z_score))),
        "significant": bool(2 * norm.sf(abs(z_score)) < assumptions.corrected_alpha()),
    }


def scenario_summary(name: str, member_data: pd.DataFrame | None = None) -> pd.DataFrame:
    data = generate_member_data(name) if member_data is None else member_data
    holdout = data.loc[data["arm"] == "A_holdout", "transactions_12w"]
    rows = []
    for arm in SCENARIOS[name]["arms"]:
        arm_data = data.loc[data["arm"] == arm]
        transactions = arm_data["transactions_12w"]
        comparison = (
            {
                "lift_vs_holdout": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
                "p_value": np.nan,
                "significant": None,
            }
            if arm == "A_holdout"
            else _comparison(transactions, holdout)
        )
        rows.append(
            {
                "arm": arm,
                "n": len(arm_data),
                "txn_per_member": float(transactions.mean()),
                "activation_rate": float(arm_data["activated"].mean()),
                "optout_rate": float(arm_data["opted_out"].mean()),
                **comparison,
                "evidence_label": assumptions.CALCULATED,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def decision_row(
    name: str, summary: pd.DataFrame | None = None
) -> dict[str, str | float]:
    summary = scenario_summary(name) if summary is None else summary
    treatment = summary.query("arm == 'C_personalised'").iloc[0]
    reduction = SCENARIOS[name]["breakage_reduction"].value
    reported_lift = round(float(treatment["lift_vs_holdout"]), 4)
    net = economics.campaign_net_contribution(
        reported_lift, reduction, "stock"
    )
    return {
        "scenario": name,
        "lift_vs_holdout": reported_lift,
        "activation_rate": float(treatment["activation_rate"]),
        "net_contribution": net,
        "breakeven_lift": economics.breakeven_lift(reduction, "stock"),
        "verdict": str(SCENARIOS[name]["verdict"]),
        "evidence_label": assumptions.CALCULATED,
    }


def _money(value: float) -> str:
    sign = "−" if value < 0 else "+"
    return f"{sign}${abs(value):,.0f}"


def run_scenario(name: str, write_data: bool = True) -> dict[str, str | float]:
    member_data = generate_member_data(name)
    summary = scenario_summary(name, member_data)
    decision = decision_row(name, summary)
    if write_data:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        member_data.to_csv(DATA_DIR / f"{name}.csv", index=False)

    printable = summary.drop(columns="evidence_label")
    print(f"\n=== {name} ===")
    print(printable.to_string(index=False))
    print(f"  breakeven lift required : {decision['breakeven_lift']:.2%}")
    print(f"  net contribution        : {_money(float(decision['net_contribution']))}")
    print(f"  VERDICT                 : {decision['verdict']}")
    return decision


def run_all(write_data: bool = True) -> pd.DataFrame:
    decisions = [run_scenario(name, write_data) for name in SCENARIOS]
    frame = pd.DataFrame(decisions)
    if write_data:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        frame.to_csv(DATA_DIR / "scenario_summary.csv", index=False)
    return frame


if __name__ == "__main__":
    run_all(write_data=True)
