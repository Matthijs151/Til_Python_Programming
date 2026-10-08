"""Find the 10 municipalities whose number of electric passenger cars (FEV) owned by
natural persons grew the most between 2022 and 2025, both in absolute numbers and
in percentage, and plot that growth.

Run from the repository root:  python src/ev_growth_top10.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

COLUMN = "Aantal personenauto's FEV van natuurlijke personen"
TOP_N = 10
YEARS = [2022, 2023, 2024, 2025]

# Minimum number of cars in the first year to be included in the percentage ranking.
# Without it, municipalities with a tiny starting number dominate
# (e.g. Vlieland 0 -> 3 is infinite growth, Ameland 7 -> 41 is +486%).
MIN_BASE = 25


def name_key(name: str) -> str:
    """Normalise municipality names; the 2025 file has the spaces stripped
    ('AaenHunze' vs 'Aa en Hunze')."""
    return "".join(str(name).split()).lower()


def load_year(year: int) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / f"personenautos_fev_{year}.csv", dtype=str)
    # Some headers contain a line break, so collapse whitespace in column names.
    df.columns = [" ".join(c.split()) for c in df.columns]
    df = df.dropna(subset=["Gemeentenaam"])
    df = df[df["Gemeentenaam"].str.strip() != ""]
    # Values use a space as thousands separator ("1 678").
    values = pd.to_numeric(df[COLUMN].str.replace(r"\s", "", regex=True), errors="coerce")
    return pd.DataFrame({
        "key": df["Gemeentenaam"].map(name_key),
        "Gemeentenaam": df["Gemeentenaam"].str.strip(),
        year: values,
    })


def main() -> None:
    frames = [load_year(year) for year in YEARS]

    # Use the names from the first year (they keep their spaces) as display names.
    # Inner merge drops municipalities that merged during the period.
    table = frames[0][["key", "Gemeentenaam"]]
    for frame in frames:
        table = table.merge(frame.drop(columns="Gemeentenaam"), on="key", how="inner")
    table = table.set_index("Gemeentenaam").drop(columns="key")

    first, last = YEARS[0], YEARS[-1]
    table["change"] = table[last] - table[first]
    table["change_pct"] = table["change"] / table[first] * 100

    top_abs = table.sort_values("change", ascending=False).head(TOP_N)
    print(f"Top {TOP_N} municipalities by absolute change in {COLUMN} ({first}-{last}):")
    print(top_abs.to_string(float_format="{:.0f}".format))
    plot(top_abs, "change",
         title=f"Top {TOP_N} municipalities by growth in electric cars\n"
               f"owned by private persons, {first}–{last}",
         xlabel=f"Increase in number of FEV passenger cars ({first} → {last})",
         filename="top10_ev_growth_natural_persons.png")

    eligible = table[table[first] >= MIN_BASE]
    top_pct = eligible.sort_values("change_pct", ascending=False).head(TOP_N)
    print(f"\nTop {TOP_N} municipalities by percentage change "
          f"(at least {MIN_BASE} cars in {first}):")
    print(top_pct.to_string(float_format="{:.0f}".format))
    plot(top_pct, "change_pct",
         title=f"Top {TOP_N} municipalities by percentage growth in electric cars\n"
               f"owned by private persons, {first}–{last}",
         xlabel=f"Growth in number of FEV passenger cars, % ({first} → {last})",
         filename="top10_ev_growth_pct_natural_persons.png",
         note=f"Only municipalities with at least {MIN_BASE} FEV cars in {first}.")


def plot(top: pd.DataFrame, value: str, title: str, xlabel: str, filename: str,
         note: str = "") -> None:
    first, last = YEARS[0], YEARS[-1]
    top = top.iloc[::-1]  # largest bar on top
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.barh(top.index, top[value], color="#2a78d6", height=0.6)
    for i, (_, row) in enumerate(top.iterrows()):
        if value == "change_pct":
            label = f"  +{row['change_pct']:.0f}%  ({row[first]:.0f} → {row[last]:.0f})"
        else:
            label = f"  +{row['change']:,.0f}  (+{row['change_pct']:.0f}%)".replace(",", " ")
        ax.text(row[value], i, label, va="center", fontsize=9, color="#52514e")

    ax.set_title(title, loc="left", fontsize=12, color="#0b0b0b")
    ax.set_xlabel(xlabel, color="#52514e")
    ax.set_xlim(0, top[value].max() * 1.3)
    ax.grid(axis="x", color="#e5e4e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#b5b4ae")
    ax.tick_params(colors="#52514e", length=0)
    source = "Source: CBS, Vertekening personenauto's naar gemeente (1 January)"
    fig.text(0.01, 0.01, f"{source}. {note}" if note else source,
             fontsize=8, color="#8a8984")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    FIG_DIR.mkdir(exist_ok=True)
    out = FIG_DIR / filename
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"Saved figure to {out}")


if __name__ == "__main__":
    main()
