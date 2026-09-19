# Model Card — HDB Resale Price Prediction (v2)

- **Generated:** 15-09-2026 01:52
- **Model:** `xgboost_v2`
- **Version:** v2
- **Target:** `resale_price`

## Intended use

Estimate HDB resale transaction prices from property, time, location,
and (in v2) MRT-related features. For analysis and benchmarking, not
a formal valuation product.

## Data & split

- Train years: **2017–2025**
- Test year: **2026** (temporal holdout)
- n_train: 221758
- n_test: 17507

## Target leakage controls

- Never use `price_per_sqm` as a feature (derived from price and area).
- v2 also drops: `['flat_year', 'price_per_sqm', 'resale_price', 'search_val', 'status']`

## Test metrics

| Metric | Value |
|--------|-------|
| RMSE | 38,711 |
| MAE | 27,237 |
| MAPE (%) | 4.17 |
| R² | 0.9673 |

## Train metrics (reference)

- train RMSE: 24770.5117708482
- train MAE: 18161.564758610737
- train R²: 0.9823882901053395

## Residual summary (test)

- mean residual: 276
- median residual: -2,176
- median abs error: 19,705

## Features

- Count: 21
- List: `['trx_date', 'trx_year', 'trx_month', 'lease_commence', 'remaining_lease_month', 'flat_type', 'flat_model', 'st', 'blk', 'storey_midpoint', 'floor_area_sqm', 'lat', 'lon', 'postal', 'subzone', 'zone_id', 'nearest_mrt', 'mrt_lat', 'mrt_lon', 'to_mrt', 'to_city']`

## Limitations

- Temporal shift: 2026 test may differ from 2017–2025 train regime.
- MRT features (v2) assume station/exit geography; construction timing not modelled.
- High-cardinality categoricals (`blk`, `postal`) are capped in one-hot encoding.
- Does not include unit-level condition, orientation, or renovation quality.

## Ethical / practical notes

- Predictions are statistical estimates only.
- Avoid using as sole input for financial or legal decisions.

## Additional notes

Figures: model_actual_vs_predicted, model_residual_distribution, model_error_by_town/flat_type/price_band, model_over_time, model_feature_importance under ./figures/.
