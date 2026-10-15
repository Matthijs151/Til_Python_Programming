"""Download the population per municipality on 1 January 2025 (CBS table 03759ned)
and save it in data/."""
from pathlib import Path

import pandas as pd
import requests

YEAR = 2025
url = "https://opendata.cbs.nl/ODataApi/odata/03759ned/TypedDataSet"
params = {
    # Totals for sex, age and marital status; only municipalities (codes 'GM....').
    "$filter": "Geslacht eq 'T001038' and Leeftijd eq '10000' and "
               f"BurgerlijkeStaat eq 'T001019' and Perioden eq '{YEAR}JJ00' and "
               "substringof('GM', RegioS)",
    "$select": "RegioS,BevolkingOp1Januari_1",
}

response = requests.get(url, params=params, timeout=120)
response.raise_for_status()

# The table also lists former municipalities, which have no population in 2025.
df = pd.DataFrame(response.json()["value"]).dropna()
df = pd.DataFrame({"statcode": df["RegioS"].str.strip(),
                   "inhabitants": df["BevolkingOp1Januari_1"].astype(int)})

out = Path("data") / f"population_{YEAR}.csv"
df.to_csv(out, index=False)
print(f"Saved {len(df)} municipalities ({df['inhabitants'].sum():,} inhabitants) to {out}")
