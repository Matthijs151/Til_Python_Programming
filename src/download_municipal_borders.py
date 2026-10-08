"""Download the 2025 Dutch municipal borders (CBS/PDOK) and save them in data/."""
from pathlib import Path

import requests

YEAR = 2025
url = f"https://service.pdok.nl/cbs/gebiedsindelingen/{YEAR}/wfs/v1_0"
params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "gebiedsindelingen:gemeente_gegeneraliseerd",
    "outputFormat": "application/json",
    "srsName": "EPSG:28992",   # Dutch RD New coordinates (metres)
}

response = requests.get(url, params=params, timeout=120)
response.raise_for_status()

out = Path("data") / f"municipal_borders_{YEAR}.geojson"
out.write_bytes(response.content)
n = len(response.json()["features"])
print(f"Saved {n} municipalities to {out} ({out.stat().st_size / 1e6:.1f} MB)")
