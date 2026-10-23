"""Compare public charge points with electric passenger cars per municipality
(sub-question 3 of the final report):
1. EVs per public charge point at the end of 2024 and its change since the end of 2022
   (maps),
2. trend line of the increase in charge points against the increase in EVs, both per
   1,000 inhabitants, and a map of municipalities with more or fewer new charge points
   than the trend line,
3. EVs per public charge point by population density, end of 2022-2024.

Charge points are counted in December and EVs on 1 January, so the charge points of
December 2022 are compared with the EVs of 1 January 2023, and so on: both describe
the end of 2022.

Prints the tables used in the report and saves the figures in figures/.
Needs data/population_2025.csv (from src/download_population.py).
Run from the repository root:  python src/charging_vs_evs.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plot_maps
from plot_maps import BLUE, COLORS, DATA_DIR, INK, INK_MUTED, MIN_EVS_FIRST_YEAR, SOURCE_GREY

# Years of the charge point counts (December); the EVs are those of 1 January a year later.
YEARS = [2022, 2023, 2024]
FIRST, LAST = YEARS[0], YEARS[-1]
PERIOD = f"end of {FIRST} → end of {LAST}"
# Diverging palettes: blue = enough charge points, red = too few.
CHANGE_COLORS = ["#2166ac", "#67a9cf", "#d1e5f0", "#fddbc7", "#f4a582", "#d6604d", "#b2182b"]
TREND_COLORS = ["#b2182b", "#f4a582", "#f2f2f0", "#92c5de", "#2166ac"]
# Below 0: the municipality has fewer charge points than before.
TREND_BINS = [-np.inf, 0.5, 0.8, 1.25, 2, np.inf]
SOURCE = (f"Source: RVO, public charge points per municipality, December {FIRST}–{LAST}; CBS, "
          f"{plot_maps.EV_DESCRIPTION},\n1 January {FIRST + 1}–{LAST + 1}.")
NO_DATA = f"no charge point data or fewer\nthan {MIN_EVS_FIRST_YEAR} EVs at the end of {FIRST}"
DENSITY_GROUPS = ["least dense 25%", "2nd quarter", "3rd quarter", "most dense 25%"]
# One hue from light to dark: the denser the group, the darker its line.
DENSITY_COLORS = [COLORS[2], COLORS[3], COLORS[5], COLORS[6]]


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """All municipalities, and the analysis set: municipalities with charge point data
    and at least 25 EVs at the end of the first year."""
    gdf = plot_maps.load()[["statnaam", "key", "inhabitants", "geometry"]]
    for year in YEARS:
        gdf = (gdf.merge(plot_maps.load_charge_points(year, f"cp_{year}"), on="key",
                         validate="one_to_one")
                  .merge(plot_maps.load_evs(year + 1, f"evs_{year}"), on="key",
                         validate="one_to_one"))
        gdf[f"evs_per_cp_{year}"] = gdf[f"evs_{year}"] / gdf[f"cp_{year}"]

    density = pd.read_csv(DATA_DIR / "Bevolkingsdichtheid, 2025 ().csv", sep=";",
                          encoding="utf-8-sig")
    density = pd.DataFrame({"key": density["Gemeente"].map(plot_maps.name_key),
                            "density": plot_maps.to_number(density["Inwoners per km² land"])})
    gdf = gdf.merge(density, on="key", how="left", validate="one_to_one")

    gdf["evs_per_cp_change"] = gdf[f"evs_per_cp_{LAST}"] / gdf[f"evs_per_cp_{FIRST}"] - 1
    gdf["ev_growth"] = gdf[f"evs_{LAST}"] / gdf[f"evs_{FIRST}"] - 1
    gdf["cp_growth"] = gdf[f"cp_{LAST}"] / gdf[f"cp_{FIRST}"] - 1
    gdf["ev_increase"] = gdf[f"evs_{LAST}"] - gdf[f"evs_{FIRST}"]
    gdf["cp_increase"] = gdf[f"cp_{LAST}"] - gdf[f"cp_{FIRST}"]
    # Inhabitants on 1 January 2025, the end of the period.
    gdf["ev_increase_per_1000"] = gdf["ev_increase"] / gdf["inhabitants"] * 1000
    gdf["cp_increase_per_1000"] = gdf["cp_increase"] / gdf["inhabitants"] * 1000

    analysis = gdf[gdf[f"cp_{FIRST}"].notna()
                   & (gdf[f"evs_{FIRST}"] >= MIN_EVS_FIRST_YEAR)].copy()
    print(f"{len(gdf)} municipalities, {len(analysis)} in the analysis set")
    return gdf, analysis


def national_totals(gdf: pd.DataFrame) -> pd.DataFrame:
    """EVs and public charge points in the Netherlands at the end of each year, over the
    same municipalities (those with charge point data)."""
    totals = gdf[gdf[f"cp_{LAST}"].notna()].sum(numeric_only=True)
    national = pd.DataFrame(
        {"Electric cars": [totals[f"evs_{year}"] for year in YEARS],
         "Public charge points": [totals[f"cp_{year}"] for year in YEARS]},
        index=pd.Index(YEARS, name="End of year"))
    national["EVs per charge point"] = (national["Electric cars"]
                                        / national["Public charge points"])
    return national


def map_panel(ax, gdf, values, bins, labels, palette, title):
    """Map of `values` (municipalities in the analysis set) in classes."""
    handles = plot_maps.choropleth(ax, gdf, values, bins, labels, palette, NO_DATA)
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=8,
              labelcolor=INK_MUTED, bbox_to_anchor=(-0.12, 1))
    ax.set_title(title, loc="left", fontsize=11, color=INK)


def style_axes(ax):
    ax.grid(color="#e5e4e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#b5b4ae")
    ax.tick_params(which="both", colors=INK_MUTED)


def save(fig, filename: str, source: str = SOURCE) -> None:
    fig.text(0.01, 0.01, source, fontsize=7, color=SOURCE_GREY)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    # A tight bounding box keeps titles and legends that stick out of the axes.
    plot_maps.save_figure(fig, filename, bbox_inches="tight")


def extremes(analysis: pd.DataFrame, column: str, columns: dict[str, str],
             high: str, low: str, n: int = 5) -> pd.DataFrame:
    """The `n` municipalities with the highest and the lowest `column`, with `columns`
    selected and renamed for display."""
    table = pd.concat({high: analysis.nlargest(n, column),
                       low: analysis.nsmallest(n, column)})
    return table[list(columns)].rename(columns=columns).droplevel(1)


def evs_per_charge_point(gdf: pd.DataFrame,
                         analysis: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Analysis 1: has the number of EVs per public charge point gone up? Returns the
    national totals per year and the municipalities where the ratio changed most."""
    national = national_totals(gdf)
    changed = extremes(analysis, "evs_per_cp_change",
                       {"statnaam": "Municipality",
                        f"evs_per_cp_{FIRST}": f"EVs per CP end {FIRST}",
                        f"evs_per_cp_{LAST}": f"EVs per CP end {LAST}",
                        "evs_per_cp_change": "Change"},
                       high="Charging fell behind most", low="Charging caught up most")

    ratio = national["EVs per charge point"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 7.5))
    map_panel(axes[0], gdf, analysis[f"evs_per_cp_{LAST}"],
              bins=[0, 1.5, 2, 2.5, 3, 4, 5, np.inf],
              labels=["fewer than 1.5", "1.5–2", "2–2.5", "2.5–3", "3–4", "4–5", "5 or more"],
              palette=COLORS,
              title=f"EVs per public charge point, end of {LAST}\n"
                    f"Netherlands overall: {ratio[LAST]:.2f}")
    map_panel(axes[1], gdf, analysis["evs_per_cp_change"],
              bins=[-np.inf, -0.25, -0.1, 0, 0.1, 0.25, 0.5, np.inf],
              labels=["−25% or more (caught up)", "−25 to −10%", "−10 to 0%", "0 to +10%",
                      "+10 to +25%", "+25 to +50%", "+50% or more (fell behind)"],
              palette=CHANGE_COLORS,
              title=f"Change in EVs per public charge point, {PERIOD}\n"
                    f"Netherlands overall: {ratio[FIRST]:.2f} → {ratio[LAST]:.2f}")
    save(fig, "evs_per_charge_point_map.png")
    return national, changed


def trend_line(gdf: pd.DataFrame,
               analysis: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame, pd.Series]:
    """Analysis 2: do municipalities with more EV growth also add more charge points?
    Both increases are per 1,000 inhabitants: in absolute numbers both mainly measure the
    size of a municipality. A trend line (linear regression) gives the expected number of
    new charge points for the EV growth of each municipality. Returns the fit, the
    municipalities furthest from the line and the number of municipalities per class."""
    ev, cp = analysis["ev_increase_per_1000"], analysis["cp_increase_per_1000"]
    slope, intercept = np.polyfit(ev, cp, 1)
    r2 = np.corrcoef(ev, cp)[0, 1] ** 2
    fit = pd.Series({
        "Municipalities": len(analysis),
        "Slope": slope,
        "Intercept": intercept,
        "R² (per 1,000 inhabitants)": r2,
        "R² (absolute numbers)": np.corrcoef(analysis["ev_increase"],
                                             analysis["cp_increase"])[0, 1] ** 2,
        "Expected new CPs per 1,000 inhabitants, lowest": intercept + slope * ev.min(),
        "Expected new CPs per 1,000 inhabitants, highest": intercept + slope * ev.max(),
    })

    # Actual new charge points as a share of the number expected from the trend line.
    analysis["vs_trend"] = cp / (intercept + slope * ev)
    outliers = extremes(analysis, "vs_trend",
                        {"statnaam": "Municipality",
                         "ev_increase_per_1000": "New EVs per 1,000 inh.",
                         "cp_increase_per_1000": "New CPs per 1,000 inh.",
                         "vs_trend": "Actual / expected"},
                        high="Most new charge points", low="Fewest new charge points")
    trend_labels = ["less than half", "50–80%", "about as expected (80–125%)",
                    "125–200%", "more than twice"]
    classes = (pd.cut(analysis["vs_trend"], TREND_BINS, right=False, labels=trend_labels)
               .value_counts(sort=False).rename("Municipalities")
               .rename_axis("New charge points compared with the trend line"))

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(ev, cp, s=16, alpha=0.6, color=BLUE, edgecolor="none")
    line_x = np.array([ev.min(), ev.max()])
    ax.plot(line_x, intercept + slope * line_x, color=INK, linewidth=1,
            label=f"trend line (R² = {r2:.2f})")
    labelled = analysis["vs_trend"].nlargest(3).index.union(
        analysis["vs_trend"].nsmallest(3).index)
    # Labels right of their dot, except when the label just above is also on the right
    # and close by: then left, so the two labels don't overlap.
    close = 0.07 * (cp.max() - cp.min())
    previous_y, previous_right = np.inf, False
    for i in cp[labelled].sort_values(ascending=False).index:
        right = not (previous_right and previous_y - cp[i] < close)
        previous_y, previous_right = cp[i], right
        ax.annotate(analysis.loc[i, "statnaam"], (ev[i], cp[i]), fontsize=8, color=INK_MUTED,
                    xytext=(5 if right else -5, 0), textcoords="offset points",
                    ha="left" if right else "right", va="center")
    ax.set_xlabel(f"New electric cars per 1,000 inhabitants, {PERIOD}", color=INK_MUTED)
    ax.set_ylabel(f"New public charge points per 1,000 inhabitants,\n{PERIOD}",
                  color=INK_MUTED)
    ax.set_title("New public charge points vs new electric cars per 1,000 inhabitants",
                 loc="left", fontsize=12, color=INK)
    ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK_MUTED)
    style_axes(ax)
    save(fig, "charge_point_vs_ev_growth.png")

    fig, ax = plt.subplots(figsize=(8, 9))
    map_panel(ax, gdf, analysis["vs_trend"], bins=TREND_BINS, labels=trend_labels,
              palette=TREND_COLORS,
              title=f"New public charge points, {PERIOD},\ncompared with the trend line "
                    "(actual as a share of the number expected\nfrom EV growth, "
                    "both per 1,000 inhabitants)")
    save(fig, "charge_point_growth_vs_trend_map.png")
    return fit, outliers, classes


def by_density(gdf: pd.DataFrame, analysis: pd.DataFrame) -> pd.DataFrame:
    """Analysis 3: are there fewer EVs per charge point in dense municipalities, where
    fewer people can charge at home? Returns the medians per density group."""
    groups = pd.qcut(analysis["density"], 4, labels=DENSITY_GROUPS)
    table = analysis.groupby(groups, observed=True).agg(**{
        "Municipalities": ("statnaam", "size"),
        "Inhabitants per km²": ("density", "median"),
        "EV growth": ("ev_growth", "median"),
        "CP growth": ("cp_growth", "median"),
        **{f"EVs per CP end {year}": (f"evs_per_cp_{year}", "median") for year in YEARS},
    })
    table.index.name = "Density group"

    fig, ax = plt.subplots(figsize=(8, 5))
    end_values = []
    for (group, row), color in zip(table.iterrows(), DENSITY_COLORS):
        values = row[[f"EVs per CP end {year}" for year in YEARS]].astype(float).values
        ax.plot(YEARS, values, color=color, linewidth=2, marker="o", markersize=5,
                label=f"{group} (~{row['Inhabitants per km²']:,.0f} inh./km²)")
        end_values.append(values[-1])
    national = national_totals(gdf)["EVs per charge point"]
    ax.plot(YEARS, national.values, color=INK, linewidth=1.5, linestyle="--",
            label="Netherlands overall (all municipalities)")
    end_values.append(national[LAST])
    # Values at the end of each line, moved apart where lines end close together.
    label_y = np.inf
    for value in sorted(end_values, reverse=True):
        label_y = min(value, label_y - 0.15)
        ax.annotate(f"{value:.2f}", (LAST, value), xytext=(LAST + 0.06, label_y),
                    va="center", fontsize=8, color=INK_MUTED)
    ax.set_xticks(YEARS, [f"end of {year}" for year in YEARS])
    ax.set_xlim(FIRST - 0.15, LAST + 0.3)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Electric cars per public charge point", color=INK_MUTED)
    ax.set_title("Electric cars per public charge point by population density (median)",
                 loc="left", fontsize=12, color=INK)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK_MUTED, loc="lower left")
    style_axes(ax)
    ax.grid(axis="x", visible=False)
    save(fig, "evs_per_charge_point_by_density.png",
         source=f"{SOURCE}\nCBS, population density {LAST + 1}. "
                f"Each group holds a quarter of the {len(analysis)} municipalities.")
    return table


def main() -> None:
    gdf, analysis = load()
    national, changed = evs_per_charge_point(gdf, analysis)
    kept_pace = (analysis["evs_per_cp_change"] <= 0).sum()
    print(f"\n{national.round(2).to_string()}\n\nCharge points kept pace with EVs (ratio "
          f"did not rise) in {kept_pace} of {len(analysis)} municipalities\n")
    print(changed.round(2).to_string())
    fit, outliers, classes = trend_line(gdf, analysis)
    print(f"\n{fit.round(3).to_string()}\n\n{outliers.round(2).to_string()}\n")
    print(classes.to_string())
    print(f"\n{by_density(gdf, analysis).round(2).to_string()}")


if __name__ == "__main__":
    main()
