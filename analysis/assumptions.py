"""Evidence register and single source of truth for analytical inputs.

Every substantive business, statistical, and scenario input is a
``TaggedValue``. Public facts are separated from case assumptions, proposed
decision thresholds, and calculated values so a reviewer can audit what is
known versus modelled before reading any result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


PUBLIC_FACT = "PUBLIC_FACT"
CASE_ASSUMPTION = "CASE_ASSUMPTION"
PROPOSED_TARGET = "PROPOSED_TARGET"
CALCULATED = "CALCULATED"


@dataclass(frozen=True)
class TaggedValue:
    value: Any
    label: str
    source: str = ""
    note: str = ""


PUBLIC = {
    "us_90day_active_members_q1fy26": TaggedValue(
        35_500_000,
        PUBLIC_FACT,
        "https://investor.starbucks.com/news/financial-releases/news-details/2026/Starbucks-Unveils-Reimagined-Loyalty-Program-to-Deliver-More-Meaningful-Value-Personalization-and-Engagement-for-Members/default.aspx",
        "Newest member count located in public materials as of 11 Aug 2026.",
    ),
    "rewards_share_us_company_operated_revenue_fy25": TaggedValue(
        0.60,
        PUBLIC_FACT,
        "https://investor.starbucks.com/news/financial-releases/news-details/2026/Starbucks-Is-Back-Turning-Momentum-Into-Long-Term-Sustainable-Growth/default.aspx",
        "Published as nearly 60%.",
    ),
    "us_comp_sales_q3fy26": TaggedValue(
        0.079,
        PUBLIC_FACT,
        "https://investor.starbucks.com/news/financial-releases/news-details/2026/Starbucks-Reports-Q3-Fiscal-Year-2026-Results/default.aspx",
    ),
    "us_comp_transactions_q3fy26": TaggedValue(
        0.042,
        PUBLIC_FACT,
        "https://investor.starbucks.com/news/financial-releases/news-details/2026/Starbucks-Reports-Q3-Fiscal-Year-2026-Results/default.aspx",
    ),
    "program_relaunch_date": TaggedValue(
        "2026-03-10",
        PUBLIC_FACT,
        "https://about.starbucks.com/press/2026/reimagined-starbucks-rewards-loyalty-program-launches-with-new-member-benefits/",
    ),
    "green_star_expiry_months": TaggedValue(
        6,
        PUBLIC_FACT,
        "https://about.starbucks.com/starbucks-rewards-faq/",
        "Green Stars may be extended one month indefinitely through qualifying activity.",
    ),
    "green_stars_earned_per_dollar": TaggedValue(
        1.0,
        PUBLIC_FACT,
        "https://about.starbucks.com/press/2026/starbucks-unveils-reimagined-loyalty-program-to-deliver-more-meaningful-value-personalization-and-engagement-to-members/",
    ),
}


A = {
    "baseline_transactions_per_30_days": TaggedValue(
        1.5,
        CASE_ASSUMPTION,
        note="Low-frequency Green-member baseline.",
    ),
    "days_per_model_month": TaggedValue(
        30,
        CASE_ASSUMPTION,
        note="Used only to convert the 30-day baseline into a 12-week window.",
    ),
    "analysis_window_days": TaggedValue(84, CASE_ASSUMPTION, note="12 weeks."),
    "average_ticket": TaggedValue(8.50, CASE_ASSUMPTION),
    "contribution_margin_rate": TaggedValue(0.25, CASE_ASSUMPTION),
    "star_accounting_value": TaggedValue(
        0.05,
        CASE_ASSUMPTION,
        note="Sensitivity range is bounded by the published redemption ladder.",
    ),
    "message_cost": TaggedValue(0.015, CASE_ASSUMPTION, note="Per outbound message."),
    "messages_per_member": TaggedValue(6, CASE_ASSUMPTION),
    "pilot_members_per_arm": TaggedValue(10_000, PROPOSED_TARGET),
    "pilot_arms": TaggedValue(3, PROPOSED_TARGET),
    "power": TaggedValue(0.80, PROPOSED_TARGET),
    "familywise_alpha": TaggedValue(0.05, PROPOSED_TARGET),
    "primary_comparisons": TaggedValue(2, PROPOSED_TARGET),
    "relative_mde": TaggedValue(0.05, PROPOSED_TARGET),
    "discount_value": TaggedValue(2.00, CASE_ASSUMPTION),
    "simulation_dispersion_k": TaggedValue(
        2.0,
        CASE_ASSUMPTION,
        note="Negative-binomial dispersion used to generate member-level outcomes.",
    ),
    "simulation_ci_level": TaggedValue(0.95, PROPOSED_TARGET),
    "simulation_seed": TaggedValue(
        20_260_310,
        CALCULATED,
        note="Program relaunch date encoded as YYYYMMDD.",
    ),
    "simulation_scenario_seed_stride": TaggedValue(10_000, CASE_ASSUMPTION),
}


TARGETS = {
    "minimum_profitable_lift": TaggedValue(0.05, PROPOSED_TARGET),
    "max_margin_decline": TaggedValue(-0.02, PROPOSED_TARGET),
    "max_optout_rate": TaggedValue(0.05, PROPOSED_TARGET),
    "max_privacy_complaint_rate": TaggedValue(0.005, PROPOSED_TARGET),
}


POWER_DISPERSION_GRID = TaggedValue((5, 3, 2, 1), CASE_ASSUMPTION)
PILOT_SIZE_GRID = TaggedValue((30_000, 60_000, 100_000, 150_000), CASE_ASSUMPTION)
BREAKAGE_RESCUE_GRID = TaggedValue((0, 0.05, 0.10, 0.15, 0.20, 0.30), CASE_ASSUMPTION)
DISCOUNT_ACTIVATION_GRID = TaggedValue((0.05, 0.10, 0.20), CASE_ASSUMPTION)
DISCOUNT_LIFT_GRID = TaggedValue((0.05, 0.10), CASE_ASSUMPTION)


REDEMPTION_LADDER = {
    "customisation": TaggedValue(
        (25, 1.00), PUBLIC_FACT, "https://about.starbucks.com/starbucks-rewards-faq/"
    ),
    "discount": TaggedValue(
        (60, 2.00), PUBLIC_FACT, "https://about.starbucks.com/starbucks-rewards-faq/"
    ),
    "drink_or_food": TaggedValue(
        (100, 6.00), PUBLIC_FACT, "https://about.starbucks.com/starbucks-rewards-faq/"
    ),
    "premium_reward": TaggedValue(
        (200, 10.00), PUBLIC_FACT, "https://about.starbucks.com/starbucks-rewards-faq/"
    ),
    "merchandise_300": TaggedValue(
        (300, 16.00), PUBLIC_FACT, "https://about.starbucks.com/starbucks-rewards-faq/"
    ),
    "merchandise_400": TaggedValue(
        (400, 20.00), PUBLIC_FACT, "https://about.starbucks.com/starbucks-rewards-faq/"
    ),
}


SIMULATION_SCENARIOS = {
    "A_personalisation_works": {
        "breakage_reduction": TaggedValue(0.11, CASE_ASSUMPTION),
        "arms": {
            "A_holdout": {
                "transactions": TaggedValue(4.2040, CASE_ASSUMPTION),
                "activation": TaggedValue(0.0000, CASE_ASSUMPTION),
                "optout": TaggedValue(0.0037, CASE_ASSUMPTION),
            },
            "B_generic": {
                "transactions": TaggedValue(4.2767, CASE_ASSUMPTION),
                "activation": TaggedValue(0.0635, CASE_ASSUMPTION),
                "optout": TaggedValue(0.0125, CASE_ASSUMPTION),
            },
            "C_personalised": {
                "transactions": TaggedValue(4.5008, CASE_ASSUMPTION),
                "activation": TaggedValue(0.0999, CASE_ASSUMPTION),
                "optout": TaggedValue(0.0143, CASE_ASSUMPTION),
            },
        },
        "verdict": "SCALE — incremental, profitable, and within guardrails",
    },
    "B_engagement_without_behaviour": {
        "breakage_reduction": TaggedValue(0.21, CASE_ASSUMPTION),
        "arms": {
            "A_holdout": {
                "transactions": TaggedValue(4.2040, CASE_ASSUMPTION),
                "activation": TaggedValue(0.0000, CASE_ASSUMPTION),
                "optout": TaggedValue(0.0037, CASE_ASSUMPTION),
            },
            "B_generic": {
                "transactions": TaggedValue(4.2057, CASE_ASSUMPTION),
                "activation": TaggedValue(0.0738, CASE_ASSUMPTION),
                "optout": TaggedValue(0.0150, CASE_ASSUMPTION),
            },
            "C_personalised": {
                "transactions": TaggedValue(4.2853, CASE_ASSUMPTION),
                "activation": TaggedValue(0.1704, CASE_ASSUMPTION),
                "optout": TaggedValue(0.0246, CASE_ASSUMPTION),
            },
        },
        "verdict": "DO NOT SCALE — no incremental transaction effect vs holdout",
    },
}


def baseline_txn_per_window() -> float:
    return (
        A["baseline_transactions_per_30_days"].value
        * A["analysis_window_days"].value
        / A["days_per_model_month"].value
    )


def contribution_margin_per_txn() -> float:
    return A["average_ticket"].value * A["contribution_margin_rate"].value


def corrected_alpha() -> float:
    return A["familywise_alpha"].value / A["primary_comparisons"].value


def star_value_range() -> tuple[float, float]:
    values = [reward / stars for stars, reward in (item.value for item in REDEMPTION_LADDER.values())]
    return min(values), max(values)


def _tagged_rows(group: str, values: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, item in values.items():
        path = f"{prefix}.{name}" if prefix else name
        if isinstance(item, TaggedValue):
            rows.append({"group": group, "name": path, **asdict(item)})
        elif isinstance(item, dict):
            rows.extend(_tagged_rows(group, item, path))
    return rows


def assumption_register() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for group, values in (
        ("public", PUBLIC),
        ("assumption", A),
        ("target", TARGETS),
        ("redemption", REDEMPTION_LADDER),
        ("simulation", SIMULATION_SCENARIOS),
    ):
        rows.extend(_tagged_rows(group, values))
    for name, item in (
        ("power_dispersion_grid", POWER_DISPERSION_GRID),
        ("pilot_size_grid", PILOT_SIZE_GRID),
        ("breakage_rescue_grid", BREAKAGE_RESCUE_GRID),
        ("discount_activation_grid", DISCOUNT_ACTIVATION_GRID),
        ("discount_lift_grid", DISCOUNT_LIFT_GRID),
    ):
        rows.append({"group": "sensitivity", "name": name, **asdict(item)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(assumption_register().to_string(index=False))
