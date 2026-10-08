"""Illustrate the number of charging locations per municipality:
a map (choropleth) of the Netherlands and a bar chart of the top municipalities.

Needs the output of src/chargers_per_municipality.py.
Run from the repository root:  python src/plot_chargers_per_municipality.py
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

BORDERS_FILE = DATA_DIR / "municipal_borders_2025.geojson"
TOP_N = 15
LABEL_N = 5  # name the largest municipalities on the map
LABEL_X_M = 45_000   # RD x-coordinate (metres) where the map labels end, in the North Sea
LABEL_GAP_M = 14_000  # minimum vertical distance between map labels

# The counts are very skewed (median 13, max 468), so we use classes instead of a
# continuous scale. One hue, light -> dark: more chargers is darker.
BINS = [0, 5, 10, 20, 40, 100, 200, float("inf")]
BIN_LABELS = ["0–5", "6–10", "11–20", "21–40", "41–100", "101–200", "more than 200"]
COLORS = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e5e4e0"


def load(snapshot_csv: Path) -> gpd.GeoDataFrame:
    counts = pd.read_csv(snapshot_csv)
    borders = gpd.read_file(BORDERS_FILE)[["statcode", "geometry"]]
    return borders.merge(counts, on="statcode", how="left")


def plot_map(gdf: gpd.GeoDataFrame, snapshot: str) -> None:
    gdf = gdf.copy()
    gdf["class"] = pd.cut(gdf["locations"], BINS, labels=False, include_lowest=True)
    gdf["color"] = gdf["class"].map(dict(enumerate(COLORS)))

    fig, ax = plt.subplots(figsize=(8, 9))
    # White borders act as a thin gap between neighbouring municipalities.
    gdf.plot(ax=ax, color=gdf["color"], edgecolor="white", linewidth=0.3)

    # The largest municipalities are in the dense Randstad, so their labels go in the
    # North Sea (west of the coast) with a thin line, spaced so they don't overlap.
    top = gdf.nlargest(LABEL_N, "locations").copy()
    points = top.geometry.representative_point()
    top["x"], top["y"] = points.x, points.y
    # Stack from north to south; at a similar height the municipality nearer the coast
    # gets the upper label, so the leader lines don't cross.
    top["order"] = top["y"] - 0.3 * top["x"]
    top = top.sort_values("order", ascending=False)
    label_y = top["y"].iloc[0] + LABEL_GAP_M
    for _, row in top.iterrows():
        label_y = min(label_y - LABEL_GAP_M, row["y"])
        ax.annotate(f"{row['Gemeentenaam']} ({row['locations']})",
                    xy=(row["x"], row["y"]), xytext=(LABEL_X_M, label_y),
                    fontsize=8, color=INK, ha="right", va="center",
                    arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=0.6,
                                    shrinkA=3, shrinkB=0),
                    path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])

    handles = [Patch(facecolor=c, edgecolor="none", label=l)
               for c, l in zip(COLORS, BIN_LABELS)]
    legend = ax.legend(handles=handles, title="Charging locations", loc="upper left",
                       frameon=False, fontsize=9, title_fontsize=9)
    legend.get_title().set_color(INK_MUTED)
    for text in legend.get_texts():
        text.set_color(INK_MUTED)

    ax.set_title("Charging locations per municipality",
                 loc="left", fontsize=12, color=INK)
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.text(0.01, 0.01,
             f"Source: Open Charge Map (snapshot {snapshot}), CBS municipal borders 2025. "
             "OCM covers only part of all Dutch chargers.",
             fontsize=8, color="#8a8984")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    save(fig, "chargers_per_municipality_map.png")


def plot_top(gdf: gpd.GeoDataFrame, snapshot: str) -> None:
    top = gdf.nlargest(TOP_N, "locations").iloc[::-1]  # largest bar on top
    fig, ax = plt.subplots(figsize=(9, 6))

    ax.barh(top["Gemeentenaam"], top["locations"], color="#2a78d6", height=0.6)
    for i, (_, row) in enumerate(top.iterrows()):
        label = (f"  {row['locations']}  ({row['connectors']} connectors, "
                 f"{row['fast_connectors']} fast)")
        ax.text(row["locations"], i, label, va="center", fontsize=9, color=INK_MUTED)

    ax.set_title(f"Top {TOP_N} municipalities by number of charging locations",
                 loc="left", fontsize=12, color=INK)
    ax.set_xlabel("Charging locations", color=INK_MUTED)
    ax.set_xlim(0, top["locations"].max() * 1.45)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#b5b4ae")
    ax.tick_params(colors=INK_MUTED, length=0)
    fig.text(0.01, 0.01,
             f"Source: Open Charge Map (snapshot {snapshot}), CBS municipal borders 2025. "
             "Fast = at least 50 kW.",
             fontsize=8, color="#8a8984")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    save(fig, "chargers_per_municipality_top15.png")


def save(fig: plt.Figure, filename: str) -> None:
    FIG_DIR.mkdir(exist_ok=True)
    out = FIG_DIR / filename
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"Saved figure to {out}")


def main() -> None:
    snapshot_csv = sorted(DATA_DIR.glob("chargers_per_municipality_*.csv"))[-1]
    snapshot = snapshot_csv.stem.removeprefix("chargers_per_municipality_")
    gdf = load(snapshot_csv)
    plot_map(gdf, snapshot)
    plot_top(gdf, snapshot)


if __name__ == "__main__":
    main()
