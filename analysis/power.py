"""Power and minimum-detectable-effect calculations for count outcomes."""

from __future__ import annotations

import math

import pandas as pd
from scipy.stats import norm

import assumptions


DISPERSION_VALUES = assumptions.POWER_DISPERSION_GRID.value


def negative_binomial_variance(mu: float, dispersion_k: float) -> float:
    return mu + (mu**2 / dispersion_k)


def required_n_per_arm(
    relative_lift: float,
    dispersion_k: float,
    power: float | None = None,
    alpha: float | None = None,
) -> int:
    mu = assumptions.baseline_txn_per_window()
    power = assumptions.A["power"].value if power is None else power
    alpha = assumptions.corrected_alpha() if alpha is None else alpha
    delta = mu * relative_lift
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    variance = negative_binomial_variance(mu, dispersion_k)
    return math.ceil(2 * z**2 * variance / delta**2)


def mde_for_n(
    n_per_arm: int,
    dispersion_k: float,
    power: float | None = None,
    alpha: float | None = None,
) -> float:
    mu = assumptions.baseline_txn_per_window()
    power = assumptions.A["power"].value if power is None else power
    alpha = assumptions.corrected_alpha() if alpha is None else alpha
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    variance = negative_binomial_variance(mu, dispersion_k)
    absolute_delta = math.sqrt(2 * z**2 * variance / n_per_arm)
    return absolute_delta / mu


def requirement_table() -> pd.DataFrame:
    mu = assumptions.baseline_txn_per_window()
    rows = []
    for k in DISPERSION_VALUES:
        n = required_n_per_arm(assumptions.A["relative_mde"].value, k)
        rows.append(
            {
                "dispersion_k": k,
                "sd": round(math.sqrt(negative_binomial_variance(mu, k)), 2),
                "n_per_arm": n,
                "total_3_arms": n * assumptions.A["pilot_arms"].value,
            }
        )
    return pd.DataFrame(rows)


def mde_table() -> pd.DataFrame:
    rows = []
    for total_n in assumptions.PILOT_SIZE_GRID.value:
        per_arm = total_n // assumptions.A["pilot_arms"].value
        row = {"total_N": total_n, "per_arm": per_arm}
        for k in DISPERSION_VALUES:
            row[f"mde_k{k}"] = round(mde_for_n(per_arm, k) * 100, 2)
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(requirement_table().to_string(index=False))
    print()
    print(mde_table().to_string(index=False))
