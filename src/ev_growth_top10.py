"""Find the 10 municipalities whose number of electric passenger cars (FEV) of private
persons and linked businesses grew the most between 2022 and 2025, both in absolute
numbers and in percentage, and plot that growth.

Run from the repository root:  python src/ev_growth_top10.py
"""

import matplotlib.pyplot as plt
import pandas as pd

from plot_maps import (BLUE, EV_COLUMN, FIRST_YEAR, INK, INK_MUTED, LAST_YEAR,
                       MIN_EVS_FIRST_YEAR, SOURCE_GREY, name_key, read_ev_file, save_figure,
                       to_number)

TOP_N = 10
YEARS = list(range(FIRST_YEAR, LAST_YEAR + 1))


def load_year(year: int) -> pd.DataFrame:
    df = read_ev_file(year)
    return pd.DataFrame({
        "key": df["Gemeentenaam"].map(name_key),
        "Gemeentenaam": df["Gemeentenaam"].str.strip(),
        year: to_number(df[EV_COLUMN]),
    })


def main() -> None:
    frames = [load_year(year) for year in YEARS]

    # Use the names from the first year (they keep their spaces) as display names.
    # Inner merge drops municipalities that merged during the period.
    table = frames[0][["key", "Gemeentenaam"]]
    for frame in frames:
        table = table.merge(frame.drop(columns="Gemeentenaam"), on="key", how="inner")
    table = table.set_index("Gemeentenaam").drop(columns="key")

    first, last = FIRST_YEAR, LAST_YEAR
    table["change"] = table[last] - table[first]
    table["change_pct"] = table["change"] / table[first] * 100

    top_abs = table.sort_values("change", ascending=False).head(TOP_N)
    print(f"Top {TOP_N} municipalities by absolute change in electric cars ({first}-{last}):")
    print(top_abs.to_string(float_format="{:.0f}".format))
    plot(top_abs, "change",
         title=f"Top {TOP_N} municipalities by growth in electric cars\n"
               f"of private persons and linked businesses, {first}–{last}",
         xlabel=f"Increase in number of FEV passenger cars ({first} → {last})",
         filename="top10_ev_growth.png")

    # Without a minimum, municipalities with a tiny starting number dominate.
    eligible = table[table[first] >= MIN_EVS_FIRST_YEAR]
    top_pct = eligible.sort_values("change_pct", ascending=False).head(TOP_N)
    print(f"\nTop {TOP_N} municipalities by percentage change "
          f"(at least {MIN_EVS_FIRST_YEAR} cars in {first}):")
    print(top_pct.to_string(float_format="{:.0f}".format))
    plot(top_pct, "change_pct",
         title=f"Top {TOP_N} municipalities by percentage growth in electric cars\n"
               f"of private persons and linked businesses, {first}–{last}",
         xlabel=f"Growth in number of FEV passenger cars, % ({first} → {last})",
         filename="top10_ev_growth_pct.png",
         note=f"Only municipalities with at least {MIN_EVS_FIRST_YEAR} FEV cars in {first}.")


def plot(top: pd.DataFrame, value: str, title: str, xlabel: str, filename: str,
         note: str = "") -> None:
    top = top.iloc[::-1]  # largest bar on top
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.barh(top.index, top[value], color=BLUE, height=0.6)
    for i, (_, row) in enumerate(top.iterrows()):
        if value == "change_pct":
            label = (f"  +{row['change_pct']:.0f}%  "
                     f"({row[FIRST_YEAR]:.0f} → {row[LAST_YEAR]:.0f})")
        else:
            label = f"  +{row['change']:,.0f}  (+{row['change_pct']:.0f}%)".replace(",", " ")
        ax.text(row[value], i, label, va="center", fontsize=9, color=INK_MUTED)

    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.set_xlabel(xlabel, color=INK_MUTED)
    ax.set_xlim(0, top[value].max() * 1.3)
    ax.grid(axis="x", color="#e5e4e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#b5b4ae")
    ax.tick_params(colors=INK_MUTED, length=0)
    source = "Source: CBS, Vertekening personenauto's naar gemeente (1 January)"
    fig.text(0.01, 0.01, f"{source}. {note}" if note else source,
             fontsize=8, color=SOURCE_GREY)

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    save_figure(fig, filename)


if __name__ == "__main__":
    main()
