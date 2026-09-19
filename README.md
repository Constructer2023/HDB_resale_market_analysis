# HDB Resale Market Analysis

End-to-end study of Singapore **HDB resale** registrations (2017 onward): market structure, location, official context series, out-of-time price models, a Power BI explorer, and a Streamlit price calculator.

**Train on 2017–2025, test on 2026.**  
**Never use `price_per_sqm` as a feature** (it is `resale_price / floor_area_sqm`).

The long-form article is in `report/`. This file is the single entry point for the repository.

---

## Contents

1. [Overview](#overview)
2. [Repository layout](#repository-layout)
3. [Requirements](#requirements)
4. [Data](#data)
5. [Pipeline](#pipeline)
6. [SQL](#sql)
7. [Geography](#geography)
8. [Machine learning](#machine-learning)
9. [Power BI dashboard](#power-bi-dashboard)
10. [Price calculator](#price-calculator)
11. [Modelling rules](#modelling-rules)
12. [Notebook order](#notebook-order)
13. [Disclaimer](#disclaimer)

---

## Overview

| Layer | Question | Where |
|--------|----------|--------|
| Data + SQL | What does the tape look like? | `data/`, `sql/`, `notebooks/` |
| Geo | Where, how far from MRT / city? | `data/aid/`, geo helpers in `src/` |
| Models | Can 2017–2025 price **2026**? | `src_model/`, `model/`, `data/model_based/` |
| Dashboard | Interactive market + model QA | `dashboard/` |
| Calculator | Indicative price from street + block | `app/` |

Two model generations:

- **v1** — no MRT / raw coordinates (safer on a changing rail map).
- **v2** — full geocode cache; used by the calculator.

---

## Repository layout

```
HDB_resale_market_analysis/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── aid/
│   └── model_based/
├── sql/
├── src/
├── src_model/
├── model/
├── notebooks/
├── figures/
├── dashboard/
│   ├── prepare/
│   └── source/
├── app/
│   ├── app.py
│   ├── services/
│   ├── tests/
│   └── .streamlit/
├── report/
└── README.md
```

Python paths resolve from the **project root** (the folder that contains `data/` and `model/`).

---

## Requirements

Python 3.11+ (developed against 3.13).

```
pip install pandas numpy scikit-learn joblib matplotlib seaborn
pip install xgboost lightgbm streamlit pytest shapely requests
```

Optional: MySQL + DataGrip, Power BI Desktop.

---

## Data

### Raw (`data/raw/`)

- Resale flat prices (registration date, Jan 2017 onward)
- Quarterly Resale Price Index
- Resale / rental applications
- Median resale prices for registered applications by town and flat type
- Demand / applications supporting series
- LTA MRT station-exit GeoJSON

Cleaning notebooks write `data/processed/` and `data/aid/`.

### Derived files (do not copy into `app/`)

| File | Role |
|------|------|
| `data/aid/resale_trx_geo.csv` | Transaction tape + geo columns |
| `data/aid/hdb_geocode_cache.csv` | Unique `(blk, st)` to lat/lon, zone, MRT, distances |
| `data/model_based/feature_meta_v2.json` | Source of truth for model columns / order |
| `data/model_based/train_v2.csv` / `test_v2.csv` | Temporal split |
| `data/model_based/model_comparison_v2.csv` | Holdout metrics |
| `model/*_v2.joblib` | Fitted sklearn Pipeline |

---

## Pipeline

1. Clean transactions and auxiliaries (wide RPI to long form; standardise categories; `na` / `-` to missing; derive year, month, quarter, storey bounds, remaining lease months).
2. Load MySQL (optional) and run `sql/` in numeric order.
3. Build the geocode cache once, then stay offline.
4. Train v1 then v2 on the 2026 holdout.
5. Export dashboard CSVs and open Power BI.
6. Run the Streamlit calculator against the same meta + pipeline + cache.

---

## SQL

Create database `hdb_resale`, enable `local_infile`, load processed CSV, then run files in `sql/` (`00_…`, overview, trends, town/type, characteristics, unit price, outliers, geo, auxiliary context). Index `town`, `flat_type`, `trx_year`, `trx_month`.

---

## Geography

Unique `(blk, st)` → OneMap search (token lasts about 3 days) → cache lat/lon and planning area (`subzone`, `zone_id`). Nearest MRT from **LTA GeoJSON** + haversine (live nearest-MRT API was unreliable). City centre: Raffles Place. After `hdb_geocode_cache.csv` exists, **do not call the API**.

`zone_id` is a **category**, not a numeric scale.

---

## Machine learning

From the project root:

```
from src_model.feature_engineering_v2 import run_feature_engineering_v2
from src_model.training_v2 import train_all_models_v2
from src_model.comparing_v2 import run_full_comparison_v2, summary_report_v2

run_feature_engineering_v2()
train_all_models_v2()
print(summary_report_v2(run_full_comparison_v2(retrain=False)))
```

Or notebooks `07` (v1), `08` (v2), `09` (interpretation).

| Item | Rule |
|------|------|
| Split | `trx_year` 2017–2025 train, **2026** test |
| Target | `resale_price` |
| Forbidden | `price_per_sqm`, `status`, `search_val` |
| v2 categoricals | `zone_id`, `blk`, `postal`, `nearest_mrt`, `subzone`, `town`, `flat_type`, `flat_model` |
| Lease | keep **one** of `flat_year` / `remaining_lease_month` |
| Persist | full sklearn Pipeline in `model/*.joblib` |

Baseline is the **training median**. Trees matter only if they beat it on 2026.

---

## Power BI dashboard

```
python dashboard/prepare/build_dashboard_sources.py
```

Point Power BI at `dashboard/source/`.

| Page | Purpose |
|------|---------|
| 1 Market overview | Volume, medians, mix, ranking parameters |
| 2 Location | Azure Map on **subzone centroids**, not every transaction |
| 3 Property drivers | Association only (area, storey, lease, town × type) |
| 4 Market context | RPI, applications vs completed deals |
| 5 Model | MAE / RMSE / R², residuals, disclaimer |

---

## Price calculator

```
streamlit run app/app.py
```

Run from the **project root**. If `from app.services` fails:

PowerShell:

```
$env:PYTHONPATH = (Get-Location).Path
streamlit run app/app.py
```

CMD:

```
set PYTHONPATH=%CD%
streamlit run app/app.py
```

Street then block (outside the form so options refresh). Location fields come from the cache. Predict uses `feature_meta_v2.json` column order + `model/*_v2.joblib`. Output: point price, ± test MAE, model name, comparables.

```
python -m pytest app/tests/test_prediction.py -q
```

Need `app/__init__.py` (may be empty).

---

## Modelling rules

1. No `price_per_sqm` in X.
2. No random train/test split.
3. v1 must not see MRT columns.
4. `zone_id` is categorical.
5. The app must not maintain a second feature list.
6. Predict only if `(blk, st)` is in the geocode cache.

---

## Notebook order

| # | Topic |
|---|--------|
| 01 | Transaction cleaning |
| 02–03 | Market EDA + figures |
| 04 | Auxiliary / official context |
| 05 | Geo enrichment (cache) |
| 06 | Geo EDA |
| 07 | ML v1 |
| 08 | ML v2 |
| 09 | Interpretation, figures, model card |

Exact filenames may differ; follow `notebooks/`.

---

## Disclaimer

Estimates are **indicative market-price predictions** from historical registrations. They are **not** official valuations, bank appraisals, or HDB assessments.

HDB and LTA datasets remain under their publishers’ terms.