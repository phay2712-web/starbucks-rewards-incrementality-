"""Unit economics for zero-discount and discount campaign alternatives."""

from __future__ import annotations

import math

import pandas as pd

import assumptions


def stars_at_risk(pool: str = "flow") -> float:
    """Return Star exposure under one of two explicitly different interpretations.

    flow: only Stars reaching six months during the 12-week pilot window.
    stock: the member's entire six-month balance is treated as exposed.
    """
    ticket = assumptions.A["average_ticket"].value
    earn_rate = assumptions.PUBLIC["green_stars_earned_per_dollar"].value
    if pool == "flow":
        return assumptions.baseline_txn_per_window() * ticket * earn_rate
    if pool == "stock":
        return (
            assumptions.A["baseline_transactions_per_30_days"].value
            * assumptions.PUBLIC["green_star_expiry_months"].value
            * ticket
            * assumptions.PUBLIC["green_stars_earned_per_dollar"].value
        )
    raise ValueError("pool must be 'flow' or 'stock'")


def message_cost_per_member() -> float:
    return assumptions.A["message_cost"].value * assumptions.A["messages_per_member"].value


def breakage_cost_per_member(breakage_reduction: float, pool: str) -> float:
    return (
        stars_at_risk(pool)
        * assumptions.A["star_accounting_value"].value
        * breakage_reduction
    )


def breakeven_lift(breakage_reduction: float, pool: str = "stock") -> float:
    baseline_margin = (
        assumptions.baseline_txn_per_window()
        * assumptions.contribution_margin_per_txn()
    )
    cost = message_cost_per_member() + breakage_cost_per_member(
        breakage_reduction, pool
    )
    return cost / baseline_margin


def breakeven_table() -> pd.DataFrame:
    rows = []
    for reduction in assumptions.BREAKAGE_RESCUE_GRID.value:
        rows.append(
            {
                "breakage_reduction": f"{reduction:.0%}",
                "breakeven_lift_flow": f"{breakeven_lift(reduction, 'flow'):.2%}",
                "breakeven_lift_stock": f"{breakeven_lift(reduction, 'stock'):.2%}",
            }
        )
    return pd.DataFrame(rows)


def discount_net(
    activation_rate: float,
    transaction_lift: float,
    members: int | None = None,
) -> float:
    members = (
        assumptions.A["pilot_members_per_arm"].value if members is None else members
    )
    baseline_transactions = assumptions.baseline_txn_per_window() * members
    incremental_margin = (
        baseline_transactions
        * transaction_lift
        * assumptions.contribution_margin_per_txn()
    )
    discount_cost = (
        baseline_transactions
        * activation_rate
        * assumptions.A["discount_value"].value
    )
    return incremental_margin - discount_cost


def _round_half_toward_zero(value: float) -> int:
    sign = 1 if value >= 0 else -1
    return sign * math.floor(abs(value) + 0.5 - 1e-9)


def _money(value: float) -> str:
    rounded = _round_half_toward_zero(value)
    sign = "−" if rounded < 0 else ""
    return f"{sign}${abs(rounded):,.0f}"


def discount_comparison() -> pd.DataFrame:
    rows = []
    lift_5, lift_10 = assumptions.DISCOUNT_LIFT_GRID.value
    for activation in assumptions.DISCOUNT_ACTIVATION_GRID.value:
        rows.append(
            {
                "activation_rate": f"{activation:.0%}",
                "net_at_5%_lift": _money(discount_net(activation, lift_5)),
                "net_at_10%_lift": _money(discount_net(activation, lift_10)),
            }
        )
    return pd.DataFrame(rows)


def campaign_net_contribution(
    lift: float,
    breakage_reduction: float,
    pool: str = "stock",
    members: int | None = None,
) -> float:
    members = (
        assumptions.A["pilot_members_per_arm"].value if members is None else members
    )
    incremental_margin = (
        assumptions.baseline_txn_per_window()
        * members
        * lift
        * assumptions.contribution_margin_per_txn()
    )
    total_cost = members * (
        message_cost_per_member()
        + breakage_cost_per_member(breakage_reduction, pool)
    )
    return incremental_margin - total_cost


if __name__ == "__main__":
    print(f"Stars at risk — flow : {stars_at_risk('flow'):.1f}")
    print(f"Stars at risk — stock: {stars_at_risk('stock'):.1f}")
    print()
    print(breakeven_table().to_string(index=False))
    print()
    print(discount_comparison().to_string(index=False))
