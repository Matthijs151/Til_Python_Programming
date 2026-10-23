# Public charging infrastructure and electric passenger cars in Dutch municipalities, 2022–2025

**TIL6022 Python Programming – Group 12**

Municipalities in the Netherlands are responsible for placing public charging points. This project
combines municipal data on electric passenger cars (CBS) and public charging points (RVO) to answer:

> To what extent has public charging infrastructure in Dutch municipalities kept pace with the growth
> of electric passenger cars between 2022 and 2025?

The analysis maps electric cars and public charging points per municipality, compares their growth
using the number of electric cars per public charging point, tests whether municipalities where the
number of electric cars grew more also added more charging points (per 1,000 inhabitants), and compares
urban and rural municipalities by population density.

The full report, with all code, figures and results, is
[`Group 12 Final report.ipynb`](Group%2012%20Final%20report.ipynb).

## Repository contents

| Path | Contents |
|------|----------|
| `Group 12 Final report.ipynb` | Final report: introduction, data, pipeline, results, conclusion, discussion |
| `Group 12 Project proposal.ipynb`, `.html` | Project proposal and its HTML export |
| `proposal version 2.ipynb` | Revised version of the proposal |
| `src/` | Python code used by the report (see below) |
| `data/` | All datasets used; they are public and included so the analysis runs offline |
| `figures/` | All figures, made by the code in `src/` |
| `requirements.txt` | Python packages needed to run the project |

### Code (`src/`)

| File | What it does |
|------|--------------|
| `plot_maps.py` | Loads, cleans and merges all data per municipality; maps for sub-questions 1 and 2 |
| `charging_vs_evs.py` | Sub-question 3: electric cars per public charging point, trend line and population-density groups |
| `ev_growth_top10.py` | Bar charts of the 10 municipalities with the largest growth in electric cars (not used in the report) |
| `download_population.py` | Downloads the population per municipality on 1 January 2025 (CBS OData API) |
| `download_municipal_borders.py` | Downloads the 2025 municipal borders (CBS via PDOK) |

### Data (`data/`)

| File | Source |
|------|--------|
| `personenautos_fev_2022.csv` … `personenautos_fev_2025.csv` | CBS, *Vertekening personenauto's naar gemeente*: electric passenger cars per municipality on 1 January 2022–2025 |
| `aantallen laadpunten per gemeente - Gemeenten.csv` | RVO, [*Aantallen laadpunten per gemeente*](https://laadinfrastructuur.databank.nl/mosaic/nl-nl/laadinfrastructuur/aantal-laadpunten-voor-licht-vervoer): public charging points per municipality, December 2022–2025 |
| `population_2025.csv` | CBS, table [03759ned](https://opendata.cbs.nl/statline/#/CBS/nl/dataset/03759ned/table): inhabitants per municipality on 1 January 2025 (made by `download_population.py`) |
| `Bevolkingsdichtheid, 2025 ().csv` | CBS: population density per municipality, 2025 |
| `municipal_borders_2025.geojson` | CBS/PDOK, [*CBS gebiedsindelingen 2025*](https://service.pdok.nl/cbs/gebiedsindelingen/2025/wfs/v1_0) (made by `download_municipal_borders.py`) |
| `charge_points_2023-2025.csv` | RVO: all charging points per municipality including private home and work charging points, December 2023–2025; not used, because the project is about public charging points |

## How to reproduce the analysis

Requires Python 3.10 or newer.

```bash
git clone https://github.com/Matthijs151/Til_Python_Programming.git
cd Til_Python_Programming
pip install -r requirements.txt
```

**Option 1 – run the report.** Open `Group 12 Final report.ipynb` in Jupyter or VS Code and run all
cells (*Run All*). The notebook loads the data, runs every analysis, saves the figures in `figures/`
and shows the figures and tables.

```bash
jupyter notebook "Group 12 Final report.ipynb"
```

**Option 2 – run the scripts.** From the repository root:

```bash
python src/plot_maps.py          # data summary and the maps for sub-questions 1 and 2
python src/charging_vs_evs.py    # tables and figures for sub-question 3
```

All data is already in `data/`. To download the population and municipal borders again, run
`python src/download_population.py` and `python src/download_municipal_borders.py` first.

## Authors

- Eline Roozenbeek
- Hendrik Hof
- Anne Jente Tukker
- Matthijs van Rijen
- Donna Smeekes
