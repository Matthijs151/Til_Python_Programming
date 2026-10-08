"""Count the EV charging locations from Open Charge Map per Dutch municipality.

Each charger is a point (latitude/longitude). We place every point inside the
CBS municipality polygon that contains it (a "spatial join") and count per municipality.

Run from the repository root:  python src/chargers_per_municipality.py
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

BORDERS_FILE = DATA_DIR / "municipal_borders_2025.geojson"
FAST_KW = 50          # connectors with at least this power count as fast chargers
MAX_SNAP_M = 1000     # max distance to snap a point that falls just outside every polygon
TOP_N = 15


def load_chargers(path: Path) -> gpd.GeoDataFrame:
    """One row per charging location, with its number of (fast) connectors."""
    records = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for r in records:
        address = r["AddressInfo"]
        # A connection entry can stand for several identical connectors ("Quantity").
        connections = r.get("Connections", [])
        rows.append({
            "ocm_id": r["ID"],
            "title": address.get("Title"),
            "lon": address["Longitude"],
            "lat": address["Latitude"],
            "connectors": sum(c.get("Quantity") or 1 for c in connections),
            "fast_connectors": sum(c.get("Quantity") or 1 for c in connections
                                   if (c.get("PowerKW") or 0) >= FAST_KW),
        })
    df = pd.DataFrame(rows)
    points = gpd.points_from_xy(df["lon"], df["lat"])
    # OCM uses GPS coordinates (WGS84); convert to the Dutch RD New grid of the borders.
    return gpd.GeoDataFrame(df, geometry=points, crs="EPSG:4326").to_crs("EPSG:28992")


def load_borders() -> gpd.GeoDataFrame:
    borders = gpd.read_file(BORDERS_FILE)[["statcode", "statnaam", "geometry"]]
    return borders.to_crs("EPSG:28992")


def assign_municipality(chargers: gpd.GeoDataFrame,
                        borders: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Step 1: the municipality polygon that contains each point.
    joined = gpd.sjoin(chargers, borders, how="left", predicate="within")
    joined = joined.drop(columns="index_right")

    # Step 2: the borders are generalised (simplified), so points on a coast or a
    # border can fall just outside every polygon. Snap those to the nearest one.
    outside = joined["statcode"].isna()
    if outside.any():
        snapped = gpd.sjoin_nearest(chargers[outside.values], borders, how="left",
                                    max_distance=MAX_SNAP_M)
        snapped = snapped[~snapped.index.duplicated()]  # ties: keep the first match
        joined.loc[outside, ["statcode", "statnaam"]] = snapped[["statcode", "statnaam"]]
        print(f"{outside.sum()} locations fell outside the generalised borders; "
              f"{snapped['statcode'].notna().sum()} snapped to a municipality "
              f"within {MAX_SNAP_M} m.")
    return joined


def main() -> None:
    ocm_file = sorted(DATA_DIR.glob("ocm_nl_*.json"))[-1]  # newest download
    chargers = load_chargers(ocm_file)
    borders = load_borders()
    print(f"Loaded {len(chargers)} charging locations from {ocm_file.name} "
          f"and {len(borders)} municipalities.")

    joined = assign_municipality(chargers, borders)
    unmatched = joined[joined["statcode"].isna()]
    if len(unmatched):
        print(f"{len(unmatched)} locations could not be placed in a municipality "
              "(probably outside the Netherlands or wrong coordinates):")
        print(unmatched[["ocm_id", "title", "lat", "lon"]].to_string(index=False))

    counts = (joined.dropna(subset=["statcode"])
              .groupby("statcode")
              .agg(locations=("ocm_id", "count"),
                   connectors=("connectors", "sum"),
                   fast_connectors=("fast_connectors", "sum")))
    # Start from all municipalities so the ones without chargers show up with 0.
    table = (borders[["statcode", "statnaam"]]
             .merge(counts, on="statcode", how="left")
             .fillna({"locations": 0, "connectors": 0, "fast_connectors": 0})
             .astype({"locations": int, "connectors": int, "fast_connectors": int})
             .rename(columns={"statnaam": "Gemeentenaam"})
             .sort_values("locations", ascending=False))

    snapshot = ocm_file.stem.removeprefix("ocm_nl_")
    out = DATA_DIR / f"chargers_per_municipality_{snapshot}.csv"
    table.to_csv(out, index=False)

    print(f"\nTop {TOP_N} municipalities by number of charging locations:")
    print(table.head(TOP_N).to_string(index=False))
    print(f"\n{(table['locations'] == 0).sum()} municipalities have no charging "
          "location in Open Charge Map.")
    print(f"Saved table to {out}")


if __name__ == "__main__":
    main()
