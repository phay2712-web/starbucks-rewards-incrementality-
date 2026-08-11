"""Generate every figure used by the README and GitHub Pages site."""

from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import assumptions
import economics
import power
import simulate


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "figures"
DOCS_FIGURE_DIR = ROOT / "docs" / "figures"

GREEN = "#006241"
DARK = "#1E3932"
GOLD = "#CBA258"
MINT = "#D4E9E2"
CORAL = "#C84B31"
GRAY = "#6B7280"


def _money(value: float, include_plus: bool = False) -> str:
    sign = "−" if value < 0 else ("+" if include_plus else "")
    return f"{sign}${abs(value):,.0f}"


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": DARK,
            "axes.titlecolor": DARK,
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": "#E5E7EB",
            "grid.linewidth": 0.8,
        }
    )


def _save(fig: plt.Figure, name: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    shutil.copy2(path, DOCS_FIGURE_DIR / name)
    plt.close(fig)


def power_curve() -> None:
    totals = np.linspace(9_000, 150_000, 300)
    arms = assumptions.A["pilot_arms"].value
    n_per_arm = assumptions.A["pilot_members_per_arm"].value
    proposed_total = n_per_arm * arms
    decision_mde = assumptions.A["relative_mde"].value * 100
    severe_dispersion = power.DISPERSION_VALUES[-1]
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    colors = [GREEN, "#27896A", GOLD, CORAL]
    for k, color in zip(power.DISPERSION_VALUES, colors):
        mde = [power.mde_for_n(max(1, int(total / arms)), k) * 100 for total in totals]
        ax.plot(totals, mde, label=f"dispersion k={k}", color=color, linewidth=2.2)
    ax.axhline(
        decision_mde,
        color=DARK,
        linestyle="--",
        linewidth=1.2,
        label=f"{decision_mde:.0f}% decision MDE",
    )
    ax.axvline(proposed_total, color=GRAY, linestyle=":", linewidth=1.2)
    severe_mde = power.mde_for_n(n_per_arm, severe_dispersion) * 100
    ax.scatter([proposed_total], [severe_mde], color=CORAL, zorder=5)
    ax.annotate(
        f"{proposed_total:,.0f} total remains sufficient\nat severe dispersion (k={severe_dispersion})",
        xy=(proposed_total, severe_mde),
        xytext=(50_000, 7.2),
        arrowprops={"arrowstyle": "->", "color": GRAY},
        color=DARK,
    )
    ax.set_title("Pilot size should follow the decision, not a round number", loc="left", fontsize=15)
    ax.set_xlabel("Total members across three arms")
    ax.set_ylabel("Minimum detectable relative lift (%)")
    ax.set_ylim(0, 11)
    ax.grid(axis="y")
    ax.legend(frameon=False, ncol=2)
    _save(fig, "01_power_curve.png")


def breakeven() -> None:
    reductions = np.linspace(0, 0.30, 121)
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    for pool, color, label in (
        ("flow", GREEN, "flow: Stars reaching six months in-window (~36)"),
        ("stock", CORAL, "stock: full six-month balance (~76)"),
    ):
        y = [economics.breakeven_lift(value, pool) * 100 for value in reductions]
        ax.plot(reductions * 100, y, color=color, linewidth=2.8, label=label)
    rescue_rate = 0.10
    flow_lift = economics.breakeven_lift(rescue_rate, "flow") * 100
    stock_lift = economics.breakeven_lift(rescue_rate, "stock") * 100
    ax.scatter([rescue_rate * 100], [flow_lift], color=GREEN, zorder=5)
    ax.scatter([rescue_rate * 100], [stock_lift], color=CORAL, zorder=5)
    ax.annotate(f"{flow_lift:.1f}% flow", (10, flow_lift), xytext=(12.5, 2.1), color=GREEN)
    ax.annotate(f"{stock_lift:.1f}% stock", (10, stock_lift), xytext=(12.5, 5.8), color=CORAL)
    ax.set_title("A zero-discount campaign still has a breakage cost", loc="left", fontsize=15)
    ax.set_xlabel("Share of otherwise-expiring Stars rescued (%)")
    ax.set_ylabel("Transaction lift required to break even (%)")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 15)
    ax.grid(axis="y")
    ax.legend(frameon=False)
    _save(fig, "02_breakeven.png")


def discount_economics() -> None:
    activations = np.array(assumptions.DISCOUNT_ACTIVATION_GRID.value) * 100
    lift_5, lift_10 = assumptions.DISCOUNT_LIFT_GRID.value
    net_5 = [economics.discount_net(value / 100, lift_5) for value in activations]
    net_10 = [economics.discount_net(value / 100, lift_10) for value in activations]
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    width = 0.34
    positions = np.arange(len(activations))
    ax.bar(positions - width / 2, net_5, width, label="5% transaction lift", color=GOLD)
    ax.bar(positions + width / 2, net_10, width, label="10% transaction lift", color=GREEN)
    ax.axhline(0, color=DARK, linewidth=1)
    for collection in ax.containers:
        ax.bar_label(
            collection,
            labels=[_money(value) for value in collection.datavalues],
            padding=3,
        )
    ax.set_xticks(positions, [f"{value:.0f}%" for value in activations])
    ax.set_xlabel("Offer activation rate")
    ax.set_ylabel("Net contribution per 10,000 members")
    ax.set_title("A $2-off campaign becomes less profitable as activation rises", loc="left", fontsize=15)
    ax.grid(axis="y")
    ax.legend(frameon=False)
    _save(fig, "03_discount_economics.png")


def simulated_results() -> None:
    names = list(simulate.SCENARIOS)
    labels = ["A — personalisation works", "B — engagement without behaviour"]
    short_labels = ["A — works", "B — engagement only"]
    decisions = [simulate.decision_row(name) for name in names]
    treatments = [
        simulate.scenario_summary(name).query("arm == 'C_personalised'").iloc[0]
        for name in names
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.9), gridspec_kw={"width_ratios": [1.2, 1]})

    ax = axes[0]
    y = np.arange(2)
    lifts = np.array([row["lift_vs_holdout"] for row in treatments]) * 100
    low = lifts - np.array([row["ci_low"] for row in treatments]) * 100
    high = np.array([row["ci_high"] for row in treatments]) * 100 - lifts
    ax.errorbar(lifts, y, xerr=[low, high], fmt="o", color=GREEN, ecolor=GRAY, capsize=5, markersize=8)
    ax.axvline(0, color=DARK, linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Transaction lift vs holdout (%) with 95% CI")
    ax.grid(axis="x")
    ax.set_title("Behaviour", loc="left")

    ax = axes[1]
    nets = [decision["net_contribution"] for decision in decisions]
    colors = [GREEN if value > 0 else CORAL for value in nets]
    bars = ax.bar(short_labels, nets, color=colors, width=0.58)
    ax.axhline(0, color=DARK, linewidth=1)
    ax.bar_label(
        bars,
        labels=[_money(value, include_plus=True) for value in nets],
        padding=4,
        fontweight="bold",
    )
    ax.set_ylabel("Net contribution per 10,000")
    ax.grid(axis="y")
    ax.margins(y=0.14)
    ax.set_title("Economics after breakage", loc="left")

    fig.suptitle("Activation can rise while incremental value falls", x=0.08, ha="left", fontsize=15, fontweight="bold", color=DARK)
    fig.tight_layout()
    _save(fig, "04_simulated_results.png")


def dashboard() -> None:
    names = list(simulate.SCENARIOS)
    labels = ["Works", "Engagement only"]
    decisions = [simulate.decision_row(name) for name in names]
    treatments = [
        simulate.scenario_summary(name).query("arm == 'C_personalised'").iloc[0]
        for name in names
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))

    metrics = [
        ("Activation rate", [row["activation_rate"] * 100 for row in treatments], "%"),
        ("Transaction lift", [row["lift_vs_holdout"] * 100 for row in treatments], "%"),
        ("Net contribution", [row["net_contribution"] for row in decisions], "$"),
    ]
    for ax, (title, values, unit) in zip(axes.flat[:3], metrics):
        colors = [GREEN if (unit != "$" or value >= 0) else CORAL for value in values]
        bars = ax.bar(labels, values, color=colors, width=0.55)
        ax.axhline(0, color=DARK, linewidth=0.8)
        if unit == "$":
            bar_labels = [_money(value, include_plus=True) for value in values]
        else:
            bar_labels = [f"{value:.1f}%" for value in values]
        ax.bar_label(bars, labels=bar_labels, padding=3, fontweight="bold")
        ax.set_title(title, loc="left")
        ax.grid(axis="y")
        ax.margins(y=0.14)

    ax = axes.flat[3]
    ax.axis("off")
    ax.set_title("Pre-registered decision", loc="left", pad=12)
    ax.text(0.02, 0.70, "SCALE", fontsize=19, fontweight="bold", color=GREEN)
    ax.text(0.02, 0.57, "Scenario A clears significance, economics, and guardrails.", wrap=True, color=DARK)
    ax.text(0.02, 0.30, "DO NOT SCALE", fontsize=19, fontweight="bold", color=CORAL)
    ax.text(0.02, 0.17, "Scenario B activates members but does not create incremental transactions.", wrap=True, color=DARK)

    fig.suptitle("The holdout dashboard tells a different story than CTR", x=0.07, ha="left", fontsize=16, fontweight="bold", color=DARK)
    fig.tight_layout()
    _save(fig, "05_dashboard.png")


def build_all() -> None:
    _style()
    power_curve()
    breakeven()
    discount_economics()
    simulated_results()
    dashboard()


if __name__ == "__main__":
    build_all()
