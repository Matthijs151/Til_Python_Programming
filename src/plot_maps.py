"""Maps of the Netherlands per municipality:
1. charge points (2025),
2. charge points per 1,000 inhabitants (2025),
3. electric passenger cars (FEV) per 1,000 inhabitants (2025),
4. growth of the number of charge points, 2023-2025,
5. growth of the number of electric passenger cars, 2023-2025.

Needs data/population_2025.csv (from src/download_population.py).
Run from the repository root:  python src/plot_maps.py
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

# Charge points at the end of December; EVs and inhabitants on 1 January.
CHARGE_POINTS_COLUMN = "aantal laadpunten per gemeente|December {year}"
EV_COLUMN = "Aantal personenauto's FEV van natuurlijke personen en gekoppelde rechtspersonen"

# Names in the charge point file that differ from the CBS border names.
CBS_NAMES = {
    "Beek": "Beek (L.)",
    "Den Haag": "'s-Gravenhage",
    "Hengelo": "Hengelo (O.)",
    "Laren": "Laren (NH.)",
    "Middelburg": "Middelburg (Z.)",
    "Rijswijk": "Rijswijk (ZH.)",
    "Stein": "Stein (L.)",
}

# One hue, very light -> very dark in even steps: a higher value is darker.
COLORS = ["#e1f4ff", "#aacffd", "#79a9e9", "#5183ce", "#315fab", "#183c84", "#041b5c"]
# The same steps in green, so the growth maps stand apart from the other maps.
GROWTH_COLORS = ["#e0fae4", "#aadab1", "#78b982", "#4c9658", "#237432", "#005110", "#003100"]
NO_DATA_COLOR = "#d6d5d0"
INK, INK_MUTED, SOURCE_GREY = "#0b0b0b", "#52514e", "#8a8984"
LABEL_X_M = 45_000    # RD x-coordinate (metres) where the labels end, in the North Sea
LABEL_GAP_M = 14_000  # minimum vertical distance between labels
# With very few EVs in 2023 the growth is meaningless (Vlieland: 0 -> 3).
MIN_EVS_2023 = 25


def name_key(name: str) -> str:
    """The EV file strips spaces ('AaenHunze') and adds '(gemeente)' to three names
    ('Utrecht (gemeente)'), so compare names without those."""
    return "".join(str(name).replace("(gemeente)", "").split()).lower()


def load() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DATA_DIR / "municipal_borders_2025.geojson")
    gdf = gdf[["statcode", "statnaam", "geometry"]]
    gdf["key"] = gdf["statnaam"].map(name_key)

    population = pd.read_csv(DATA_DIR / "population_2025.csv")

    charge_points = pd.read_csv(DATA_DIR / "charge_points_2023-2025.csv", sep=";")
    charge_points = pd.DataFrame({
        "key": charge_points["Gemeenten"].replace(CBS_NAMES).map(name_key),
        "charge_points": charge_points[CHARGE_POINTS_COLUMN.format(year=2025)],
        "charge_points_2023": charge_points[CHARGE_POINTS_COLUMN.format(year=2023)],
    })

    gdf = (gdf.merge(population, on="statcode", validate="one_to_one")
              .merge(charge_points, on="key", validate="one_to_one")
              .merge(load_evs(2025, "evs"), on="key", validate="one_to_one")
              .merge(load_evs(2023, "evs_2023"), on="key", validate="one_to_one"))
    assert len(gdf) == 342, f"only {len(gdf)} of 342 municipalities matched"

    gdf["charge_points_per_1000"] = gdf["charge_points"] / gdf["inhabitants"] * 1000
    gdf["evs_per_1000"] = gdf["evs"] / gdf["inhabitants"] * 1000
    # Growth as a fraction (0.67 = +67%).
    gdf["charge_points_growth"] = gdf["charge_points"] / gdf["charge_points_2023"] - 1
    gdf["evs_growth"] = (gdf["evs"] / gdf["evs_2023"] - 1).where(
        gdf["evs_2023"] >= MIN_EVS_2023)
    return gdf


def load_evs(year: int, column: str) -> pd.DataFrame:
    evs = pd.read_csv(DATA_DIR / f"personenautos_fev_{year}.csv", dtype=str)
    evs.columns = [" ".join(c.split()) for c in evs.columns]  # headers contain line breaks
    evs = evs.dropna(subset=["Gemeentenaam"])
    return pd.DataFrame({
        "key": evs["Gemeentenaam"].map(name_key),
        # Values use a space as thousands separator ("1 678").
        column: pd.to_numeric(evs[EV_COLUMN].str.replace(r"\s", "", regex=True)),
    })


def plot_map(gdf, column, bins, bin_labels, legend_title, title, label_by, label_n,
             label_format, source, filename, no_data_label=None, palette=COLORS):
    """Choropleth of `column` in classes; names the `label_n` largest `label_by`.
    Municipalities without a value are grey, explained by `no_data_label`."""
    classes = pd.cut(gdf[column], bins, labels=False, right=False)
    colors = classes.map(dict(enumerate(palette))).fillna(NO_DATA_COLOR)
    fig, ax = plt.subplots(figsize=(8, 9))
    # White borders act as a thin gap between neighbouring municipalities.
    gdf.plot(ax=ax, color=colors, edgecolor="white", linewidth=0.3)

    top = gdf.nlargest(label_n, label_by)
    add_sea_labels(ax, top, [f"{r['statnaam']} ({r[column]:{label_format}})"
                             for _, r in top.iterrows()])

    handles = [Patch(facecolor=c, label=l) for c, l in zip(palette, bin_labels)]
    if no_data_label:
        handles.append(Patch(facecolor=NO_DATA_COLOR, label=no_data_label))
    legend = ax.legend(handles=handles, title=legend_title, loc="upper left",
                       frameon=False, fontsize=9, title_fontsize=9, labelcolor=INK_MUTED)
    legend.get_title().set_color(INK_MUTED)

    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.text(0.01, 0.01, source, fontsize=8, color=SOURCE_GREY)
    fig.tight_layout(rect=(0.03, 0.04, 1, 1))

    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / filename, dpi=200)
    plt.close(fig)
    print(f"Saved figure to {FIG_DIR / filename}")


def add_sea_labels(ax, rows, texts):
    """Label municipalities in the North Sea (west of the coast) with a thin line.
    The large municipalities are in the dense Randstad, so labels on the map itself
    would cover the colours and overlap each other."""
    rows = rows.copy()
    points = rows.geometry.representative_point()
    rows["x"], rows["y"], rows["text"] = points.x, points.y, texts
    # Stack from north to south; at a similar height the municipality nearer the coast
    # gets the upper label, so the leader lines don't cross.
    rows["order"] = rows["y"] - 0.3 * rows["x"]
    rows = rows.sort_values("order", ascending=False)
    label_y = rows["y"].iloc[0] + LABEL_GAP_M
    for _, row in rows.iterrows():
        label_y = min(label_y - LABEL_GAP_M, row["y"])
        ax.annotate(row["text"], xy=(row["x"], row["y"]), xytext=(LABEL_X_M, label_y),
                    fontsize=8, color=INK, ha="right", va="center",
                    arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=0.6,
                                    shrinkA=3, shrinkB=0),
                    path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])


def main() -> None:
    gdf = load()
    charge_source = "Source: charge points per municipality, December 2025"
    cbs_source = "CBS population on 1 January 2025; CBS municipal borders 2025."

    total = gdf["charge_points"].sum()
    plot_map(gdf, "charge_points",
             bins=[0, 1000, 2000, 3000, 5000, 10_000, 20_000, float("inf")],
             bin_labels=["fewer than 1,000", "1,000–2,000", "2,000–3,000", "3,000–5,000",
                         "5,000–10,000", "10,000–20,000", "20,000 or more"],
             legend_title="Charge points",
             title=f"Charge points per municipality, December 2025\n"
                   f"Netherlands total: {total:,.0f}",
             label_by="charge_points", label_n=5, label_format=",.0f",
             source=f"{charge_source}; CBS municipal borders 2025.",
             filename="charge_points_map.png")

    national = total / gdf["inhabitants"].sum() * 1000
    plot_map(gdf, "charge_points_per_1000",
             bins=[0, 50, 60, 70, 80, 90, 100, float("inf")],
             bin_labels=["fewer than 50", "50–60", "60–70", "70–80", "80–90", "90–100",
                         "100 or more"],
             legend_title="Charge points\nper 1,000 inhabitants",
             title=f"Charge points per 1,000 inhabitants, 2025\n"
                   f"Netherlands overall: {national:.0f}",
             label_by="inhabitants", label_n=4, label_format=".0f",
             source=f"{charge_source};\n{cbs_source}",
             filename="charge_points_per_1000_inhabitants_map.png")

    national = gdf["evs"].sum() / gdf["inhabitants"].sum() * 1000
    plot_map(gdf, "evs_per_1000",
             bins=[0, 12, 15, 18, 21, 25, 30, float("inf")],
             bin_labels=["fewer than 12", "12–15", "15–18", "18–21", "21–25", "25–30",
                         "30 or more"],
             legend_title="Electric cars\nper 1,000 inhabitants",
             title=f"Electric passenger cars per 1,000 inhabitants, 1 January 2025\n"
                   f"Netherlands overall: {national:.0f}",
             label_by="inhabitants", label_n=4, label_format=".0f",
             source="Source: CBS, FEV passenger cars of private persons (lease and company "
                    f"cars not included);\n{cbs_source}",
             filename="evs_per_1000_inhabitants_map.png")

    national = gdf["charge_points"].sum() / gdf["charge_points_2023"].sum() - 1
    plot_map(gdf, "charge_points_growth",
             bins=[0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, float("inf")],
             bin_labels=["less than +50%", "+50–60%", "+60–70%", "+70–80%", "+80–90%",
                         "+90–100%", "+100% or more (doubled)"],
             legend_title="Growth in charge points\nDecember 2023 → December 2025",
             title="Growth in charge points per municipality, 2023–2025\n"
                   f"Netherlands overall: {national:+.0%}",
             label_by="inhabitants", label_n=4, label_format="+.0%",
             source="Source: charge points per municipality, December 2023 and December "
                    "2025; CBS municipal borders 2025.",
             filename="charge_points_growth_map.png", palette=GROWTH_COLORS)

    reliable = gdf["evs_growth"].notna()
    national = gdf.loc[reliable, "evs"].sum() / gdf.loc[reliable, "evs_2023"].sum() - 1
    plot_map(gdf, "evs_growth",
             bins=[0, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, float("inf")],
             bin_labels=["less than +60%", "+60–70%", "+70–80%", "+80–90%", "+90–100%",
                         "+100–110%", "+110% or more"],
             legend_title="Growth in electric cars\n1 January 2023 → 1 January 2025",
             title="Growth in electric passenger cars per municipality, 2023–2025\n"
                   f"Netherlands overall: {national:+.0%}",
             label_by="inhabitants", label_n=4, label_format="+.0%",
             no_data_label=f"fewer than {MIN_EVS_2023} electric\ncars in 2023",
             source="Source: CBS, FEV passenger cars of private persons (lease and company "
                    "cars not included),\n1 January 2023 and 2025; CBS municipal borders 2025.",
             filename="evs_growth_map.png", palette=GROWTH_COLORS)


if __name__ == "__main__":
    main()
