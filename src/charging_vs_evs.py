"""Compare public charge points with electric passenger cars per municipality
(sub-question 3 of the final report):
1. EVs per public charge point in 2025 and its change since 2022 (maps),
2. trend line of the increase in charge points against the increase in EVs, and a map
   of municipalities with more or fewer new charge points than the trend line,
3. EVs per public charge point by population density.

Prints the tables used in the report and saves the figures in figures/.
Needs data/population_2025.csv (from src/download_population.py).
Run from the repository root:  python src/charging_vs_evs.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

import plot_maps
from plot_maps import DATA_DIR, FIG_DIR, INK, INK_MUTED, NO_DATA_COLOR, SOURCE_GREY

FIRST, LAST = plot_maps.FIRST_YEAR, plot_maps.LAST_YEAR
BLUE, LIGHT_BLUE = "#2a78d6", "#aacffd"
# Diverging palettes: blue = enough charge points, red = too few.
CHANGE_COLORS = ["#2166ac", "#67a9cf", "#d1e5f0", "#fddbc7", "#f4a582", "#d6604d", "#b2182b"]
TREND_COLORS = ["#b2182b", "#f4a582", "#f2f2f0", "#92c5de", "#2166ac"]
SOURCE = (f"Source: RVO, public charge points per municipality, {FIRST} and {LAST}; CBS, FEV "
          f"passenger cars of private persons, 1 January {FIRST} and {LAST}.")
DENSITY_GROUPS = ["least dense 25%", "2nd quarter", "3rd quarter", "most dense 25%"]


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """All municipalities, and the analysis set: municipalities with charge point data
    and at least 25 EVs in 2022."""
    gdf = plot_maps.load()

    density = pd.read_csv(DATA_DIR / "Bevolkingsdichtheid, 2025 ().csv", sep=";",
                          encoding="utf-8-sig")
    density = pd.DataFrame({
        "key": density["Gemeente"].map(plot_maps.name_key),
        # A space is used as thousands separator ("6 901").
        "density": pd.to_numeric(density["Inwoners per km² land"]
                                 .str.replace(r"\s", "", regex=True)),
    })
    gdf = gdf.merge(density, on="key", how="left", validate="one_to_one")

    gdf["evs_per_cp_first"] = gdf["evs_first"] / gdf["charge_points_first"]
    gdf["evs_per_cp"] = gdf["evs"] / gdf["charge_points"]
    gdf["evs_per_cp_change"] = gdf["evs_per_cp"] / gdf["evs_per_cp_first"] - 1
    gdf["ev_increase"] = gdf["evs"] - gdf["evs_first"]
    gdf["cp_increase"] = gdf["charge_points"] - gdf["charge_points_first"]

    analysis = gdf[gdf["charge_points"].notna() & gdf["evs_growth"].notna()].copy()
    print(f"{len(gdf)} municipalities, {len(analysis)} in the analysis set")
    return gdf, analysis


def choropleth(ax, data, column, bins, labels, title, palette, no_data_label):
    """Map of `column` in classes; municipalities without a value are grey."""
    classes = pd.cut(data[column], bins, labels=False, right=False)
    data.plot(ax=ax, color=classes.map(dict(enumerate(palette))).fillna(NO_DATA_COLOR),
              edgecolor="white", linewidth=0.3)
    handles = [Patch(facecolor=c, label=l) for c, l in zip(palette, labels)]
    handles.append(Patch(facecolor=NO_DATA_COLOR, label=no_data_label))
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=8,
              labelcolor=INK_MUTED, bbox_to_anchor=(-0.12, 1))
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.set_axis_off()
    ax.set_aspect("equal")


def style_axes(ax):
    ax.grid(color="#e5e4e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#b5b4ae")
    ax.tick_params(colors=INK_MUTED)


def save(fig, filename: str, source: str = SOURCE) -> None:
    fig.text(0.01, 0.01, source, fontsize=7, color=SOURCE_GREY)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    FIG_DIR.mkdir(exist_ok=True)
    # A tight bounding box keeps titles and legends that stick out of the axes.
    fig.savefig(FIG_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure to {FIG_DIR / filename}")


def evs_per_charge_point(gdf: pd.DataFrame, analysis: pd.DataFrame) -> None:
    """Analysis 1: has the number of EVs per public charge point gone up?"""
    national_first = gdf["evs_first"].sum() / gdf["charge_points_first"].sum()
    with_data = gdf["charge_points"].notna()
    national_last = gdf.loc[with_data, "evs"].sum() / gdf.loc[with_data, "charge_points"].sum()
    kept_pace = (analysis["evs_per_cp_change"] <= 0).sum()
    print(f"\nNetherlands: {national_first:.2f} EVs per public charge point in {FIRST}, "
          f"{national_last:.2f} in {LAST}")
    print(f"Charge points kept pace with EVs (ratio did not rise) in {kept_pace} of "
          f"{len(analysis)} municipalities")

    cols = ["statnaam", "evs", "charge_points", "evs_per_cp_first", "evs_per_cp",
            "evs_per_cp_change"]
    print("\nLargest increase in EVs per charge point (charging fell behind):")
    print(analysis.nlargest(5, "evs_per_cp_change")[cols].round(2).to_string(index=False))
    print("\nLargest decrease in EVs per charge point (charging caught up):")
    print(analysis.nsmallest(5, "evs_per_cp_change")[cols].round(2).to_string(index=False))

    in_analysis = gdf.index.isin(analysis.index)
    no_data = f"no charge point data or\nfewer than 25 EVs in {FIRST}"
    fig, axes = plt.subplots(1, 2, figsize=(13, 7.5))
    choropleth(axes[0], gdf.assign(v=gdf["evs_per_cp"].where(in_analysis)), "v",
               bins=[0, 1, 1.5, 2, 2.5, 3, 4, np.inf],
               labels=["fewer than 1", "1–1.5", "1.5–2", "2–2.5", "2.5–3", "3–4", "4 or more"],
               palette=plot_maps.COLORS, no_data_label=no_data,
               title=f"EVs per public charge point, {LAST}\n"
                     f"Netherlands overall: {national_last:.2f}")
    choropleth(axes[1], gdf.assign(v=gdf["evs_per_cp_change"].where(in_analysis)), "v",
               bins=[-np.inf, -0.25, -0.1, 0, 0.1, 0.25, 0.5, np.inf],
               labels=["−25% or more (caught up)", "−25 to −10%", "−10 to 0%", "0 to +10%",
                       "+10 to +25%", "+25 to +50%", "+50% or more (fell behind)"],
               palette=CHANGE_COLORS, no_data_label=no_data,
               title=f"Change in EVs per public charge point, {FIRST}–{LAST}\n"
                     f"Netherlands overall: {national_first:.2f} → {national_last:.2f}")
    save(fig, "evs_per_charge_point_map.png")


def trend_line(gdf: pd.DataFrame, analysis: pd.DataFrame) -> None:
    """Analysis 2: do municipalities with more EV growth also add more charge points?
    A trend line (linear regression) gives the expected number of new charge points
    for the EV growth of each municipality."""
    # On log scales, because a few large cities have much larger numbers than the rest.
    x, y = np.log(analysis["ev_increase"]), np.log(analysis["cp_increase"])
    slope, intercept = np.polyfit(x, y, 1)
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    print(f"\nTrend line: slope {slope:.2f}, R² = {r2:.2f} (n = {len(analysis)})")

    # Actual new charge points as a share of the number expected from the trend line.
    analysis["vs_trend"] = analysis["cp_increase"] / np.exp(intercept + slope * x)
    cols = ["statnaam", "ev_increase", "cp_increase", "vs_trend"]
    print("\nFewest new charge points compared with the trend line:")
    print(analysis.nsmallest(5, "vs_trend")[cols].round(2).to_string(index=False))
    print("\nMost new charge points compared with the trend line:")
    print(analysis.nlargest(5, "vs_trend")[cols].round(2).to_string(index=False))

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(analysis["ev_increase"], analysis["cp_increase"], s=16, alpha=0.6,
               color=BLUE, edgecolor="none")
    ax.set_xscale("log")
    ax.set_yscale("log")
    line_x = np.logspace(np.log10(analysis["ev_increase"].min()),
                         np.log10(analysis["ev_increase"].max()))
    ax.plot(line_x, np.exp(intercept) * line_x ** slope, color=INK, linewidth=1,
            label=f"trend line (R² = {r2:.2f})")
    outliers = analysis["vs_trend"].nlargest(3).index.union(
        analysis["vs_trend"].nsmallest(3).index)
    for i in outliers:
        ax.annotate(analysis.loc[i, "statnaam"],
                    (analysis.loc[i, "ev_increase"], analysis.loc[i, "cp_increase"]),
                    fontsize=8, color=INK_MUTED, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel(f"Increase in electric cars, {FIRST}–{LAST} (log scale)", color=INK_MUTED)
    ax.set_ylabel(f"Increase in public charge points, {FIRST}–{LAST} (log scale)",
                  color=INK_MUTED)
    ax.set_title("Growth in public charge points vs growth in electric cars per municipality",
                 loc="left", fontsize=12, color=INK)
    ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK_MUTED)
    style_axes(ax)
    save(fig, "charge_point_vs_ev_growth.png")

    fig, ax = plt.subplots(figsize=(8, 9))
    choropleth(ax, gdf.assign(v=analysis["vs_trend"]), "v",
               bins=[0, 0.5, 0.8, 1.25, 2, np.inf],
               labels=["less than half", "50–80%", "about as expected (80–125%)",
                       "125–200%", "more than twice"],
               palette=TREND_COLORS,
               no_data_label=f"no charge point data or\nfewer than 25 EVs in {FIRST}",
               title=f"New public charge points {FIRST}–{LAST} compared with the trend line\n"
                     "(actual as a share of the number expected from EV growth)")
    save(fig, "charge_point_growth_vs_trend_map.png")


def by_density(analysis: pd.DataFrame) -> None:
    """Analysis 3: are there fewer EVs per charge point in dense municipalities, where
    fewer people can charge at home?"""
    groups = pd.qcut(analysis["density"], 4, labels=DENSITY_GROUPS)
    table = analysis.groupby(groups, observed=True).agg(
        municipalities=("statnaam", "size"),
        median_density=("density", "median"),
        ev_growth_pct=("evs_growth", "median"),
        cp_growth_pct=("charge_points_growth", "median"),
        evs_per_cp_first=("evs_per_cp_first", "median"),
        evs_per_cp=("evs_per_cp", "median"),
    )
    table[["ev_growth_pct", "cp_growth_pct"]] *= 100
    print("\nMedians per density group:")
    print(table.round(2).to_string())

    fig, ax = plt.subplots(figsize=(8, 5))
    pos = np.arange(len(table))
    for offset, column, year, color in [(-0.2, "evs_per_cp_first", FIRST, LIGHT_BLUE),
                                        (0.2, "evs_per_cp", LAST, BLUE)]:
        bars = ax.bar(pos + offset, table[column], width=0.4, color=color, label=str(year))
        ax.bar_label(bars, fmt="%.2f", fontsize=8, color=INK_MUTED, padding=2)
    ax.set_xticks(pos, [f"{g}\n(~{d:,.0f} inh./km²)"
                        for g, d in zip(table.index, table["median_density"])], fontsize=9)
    ax.set_ylabel("Electric cars per public charge point (median)", color=INK_MUTED)
    ax.set_title("Electric cars per public charge point by population density",
                 loc="left", fontsize=12, color=INK)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_MUTED)
    style_axes(ax)
    ax.grid(axis="x", visible=False)
    save(fig, "evs_per_charge_point_by_density.png",
         source=f"{SOURCE}\nCBS, population density {LAST}. "
                f"Each group holds a quarter of the {len(analysis)} municipalities.")


def main() -> None:
    gdf, analysis = load()
    evs_per_charge_point(gdf, analysis)
    trend_line(gdf, analysis)
    by_density(analysis)


if __name__ == "__main__":
    main()
