"""Download all Dutch charging locations from Open Charge Map and save them in data/."""
import json
import os
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()  # reads OCM_API_KEY from the .env file
api_key = os.getenv("OCM_API_KEY")

params = {
    "output": "json",
    "countrycode": "NL",
    "maxresults": 100000,
    "compact": "true",
    "verbose": "false",
}
response = requests.get("https://api.openchargemap.io/v3/poi/",
                        params=params, headers={"X-API-Key": api_key}, timeout=300)
response.raise_for_status()
data = response.json()

out = Path("data") / f"ocm_nl_{date.today()}.json"
out.write_text(json.dumps(data), encoding="utf-8")
print(f"Saved {len(data)} locations to {out} ({out.stat().st_size / 1e6:.1f} MB)")
