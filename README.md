# Public charging infrastructure and EV growth in Dutch municipalities

**TIL6022 Python Programming - Group 12**

This project looks at how well public charging infrastructure in Dutch municipalities in 2025 matches
the number and growth of electric passenger cars between 2022 and 2025.

## Repository contents

| Path | Contents |
|------|----------|
| `project.ipynb` | Project notebook (proposal → final report) |
| `project.html` | HTML export of the notebook |
| `data/` | Datasets used that can be shared publicly |
| `src/` | Code that is not in the notebook |
| `figures/` | Visualisations that are not in the notebook |
| `requirements.txt` | Python packages needed to run the project |

## How to run

```bash
git clone https://github.com/Matthijs151/Til_Python_Programming.git
cd Til_Python_Programming
pip install -r requirements.txt
jupyter notebook project.ipynb
```

The scripts in `src/` are run from the repository root:

| Script | What it does |
|--------|--------------|
| `python src/download_municipal_borders.py` | Downloads the 2025 municipal borders (CBS/PDOK) to `data/` |
| `python src/download_population.py` | Downloads the population per municipality on 1 January 2025 (CBS) to `data/` |
| `python src/plot_maps.py` | Maps of public charge points, public charge points and EVs per 1,000 inhabitants, and their growth 2022–2025 |
| `python src/ev_growth_top10.py` | Bar charts of the 10 municipalities with the largest EV growth, 2022–2025 |
| `python src/charging_vs_evs.py` | EVs per public charge point (2022–2025), trend line of charge point growth against EV growth, comparison by population density: the figures for sub-question 3 |

*To be completed for the final report: the steps needed to reproduce the analysis.*

## Authors

- Eline Roozenbeek
- Hendrik Hof
- Anne Jente Tukker
- Matthijs van Rijen
- Donna Smeekes
