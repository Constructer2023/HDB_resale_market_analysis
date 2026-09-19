from __future__ import annotations
import json
from functools import lru_cache
from typing import Any
import joblib
import numpy as np
import pandas as pd
from .location_lookup import project_root, lookup_location, remaining_lease_to_months

model_dir = project_root / 'model'
model_based_dir = project_root / 'data' / 'model_based'
feature_meta_path = model_based_dir / 'feature_meta_v2.json'
comparison_path = model_based_dir / 'model_comparison_v2.csv'
forbidden = {'resale_price', 'price_per_sqm', 'status', 'search_val'}

class PredictionError(ValueError):
    pass

@lru_cache(maxsize = 1)
def load_feature_meta():
    with open(feature_meta_path, encoding = 'utf-8') as f:
        meta = json.load(f)
    return meta

def feature_columns():
    return list(load_feature_meta()['feature_columns'])

def _read_comparison():
    return pd.read_csv(comparison_path)

def choose_model_name(preferred: str | None = None):
    cmp = _read_comparison()
    ok = cmp.dropna(subset = ['rmse']).sort_values('rmse')
    if preferred:
        hit = ok[ok['model'].astype(str).str.contains(preferred, case = False)]
        if not hit.empty:
            return str(hit.iloc[0]['model'])
    if not ok.empty:
        return str(ok.iloc[0]['model'])
    if preferred:
        stem = preferred if preferred.endswith('_v2') else f'{preferred}_v2'
        if (model_dir / f'{stem}.joblib').exists():
            return stem
    if model_dir.exists():
        jobs = sorted(p.stem for p in model_dir.glob('*_v2.joblib'))
        for key in ('xgboost', 'lightgbm', 'random_forest', 'ridge'):
            for j in jobs:
                if key in j:
                    return j
        if jobs:
            return jobs[0]
    raise FileNotFoundError(
        f'No v2 model found in {model_dir}. Train v2 models first.'
    )

def model_metrics(model_name: str | None = None):
    name = model_name or choose_model_name()
    cmp = _read_comparison()
    out: dict[str, Any] = {'model': name, 'mae': None, 'rmse': None, 'r2': None, 'mape': None}
    if cmp is None or 'model' not in cmp.columns:
        return out
    names = cmp['model'].astype(str)
    mask = names.eq(name) | names.eq(name.replace('_v2', '')) | names.eq(f'{name}_v2')
    row = cmp.loc[mask]
    if row.empty:
        return out
    r = row.iloc[0]
    for k in ('mae', 'rmse', 'r2', 'mape'):
        if k in r.index and pd.notna(r[k]):
            out[k] = float(r[k])
    out['model'] = str(r.get('model', name))
    return out

@lru_cache(maxsize = 4)
def load_pipeline(model_name: str):
    stem = model_name if model_name.endswith('_v2') else f'{model_name}_v2'
    path = model_dir / f'{stem}.joblib'
    if not path.exists():
        alt = model_dir / f'{model_name}.joblib'
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError(f'Pipeline not found: {path}')
    return joblib.load(path)

def validate_inputs(payload: dict[str, Any]):
    errors: list[str] = []
    required = ['st', 'blk', 'trx_year', 'trx_month', 'flat_type', 'floor_area_sqm']
    for k in required:
        if payload.get(k) in (None, ''):
            errors.append(f'Missing required field: {k}')
    area = payload.get('floor_area_sqm')
    if area not in (None, ''):
        try:
            a = float(area)
            if not (a > 0):
                errors.append('floor_area_sqm must be > 0.')
            if a > 400:
                errors.append('floor_area_sqm looks too large (> 400).')
        except (TypeError, ValueError):
            errors.append('floor_area_sqm must be numeric.')
    year = payload.get('trx_year')
    month = payload.get('trx_month')
    try:
        y = int(year)
        if y < 2017 or y > 2030:
            errors.append('trx_year is out of supported range (2017–2030).')
    except (TypeError, ValueError):
        if year not in (None, ''):
            errors.append('trx_year must be an integer.')
    try:
        m = int(month)
        if m < 1 or m > 12:
            errors.append('trx_month must be 1–12.')
    except (TypeError, ValueError):
        if month not in (None, ''):
            errors.append('trx_month must be an integer 1–12.')
    lease = payload.get('remaining_lease_month', payload.get('remaining_lease'))
    if lease not in (None, ''):
        try:
            months = remaining_lease_to_months(lease)
            if months > 99 * 12:
                errors.append('remaining lease cannot exceed 99 years.')
        except ValueError as e:
            errors.append(str(e))
    return errors

def _coerce_for_column(col: str, value: Any):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    cat_hints = ('zone_id', 'blk', 'st', 'postal', 'nearest_mrt', 'subzone', 'flat_type', 'flat_model', 'storey_range')
    if col in cat_hints:
        return str(value).strip()
    if col in ('trx_year', 'trx_month', 'storey_lower', 'storey_midpoint', 'storey_upper',
               'remaining_lease_month', 'lease_commence', 'flat_year'
        ):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value).strip()

def build_feature_frame(payload: dict[str, Any], location: dict[str, Any] | None = None):
    cols = feature_columns()
    merged: dict[str, Any] = {}
    if location:
        merged.update(location)
    merged.update({k: v for k, v in payload.items() if v is not None})
    if 'trx_year' in cols and 'trx_year' in merged:
        merged['trx_year'] = int(merged['trx_year'])
    if 'trx_month' in cols and 'trx_month' in merged:
        merged['trx_month'] = int(merged['trx_month'])
    storey_label = payload.get('storey_range') or payload.get('storey')
    if 'storey_range' in cols:
        merged['storey_range'] = str(storey_label).strip()
    lease_raw = payload.get('remaining_lease_month', payload.get('remaining_lease'))
    if lease_raw not in (None, '') and 'remaining_lease_month' in cols:
        merged['remaining_lease_month'] = remaining_lease_to_months(lease_raw)
    row = {}
    for col in cols:
        if col in forbidden:
            continue
        row[col] = _coerce_for_column(col, merged.get(col, np.nan))
    return pd.DataFrame([row], columns = cols)

def estimate_price(payload: dict[str, Any], model_name: str | None = None):
    errors = validate_inputs(payload)
    if errors:
        raise PredictionError('; '.join(errors))
    location = lookup_location(payload['st'], payload['blk'])
    X = build_feature_frame(payload, location)
    name = choose_model_name(model_name)
    pipe = load_pipeline(name)
    pred = float(np.asarray(pipe.predict(X)).ravel()[0])
    if not np.isfinite(pred) or pred <= 0:
        raise PredictionError('Model returned a non-positive or invalid price.')
    metrics = model_metrics(name)
    mae = metrics.get('mae')
    lo = pred - mae if mae is not None else None
    hi = pred + mae if mae is not None else None
    return {
        'estimated_price': pred,
        'range_low': max(lo, 0) if lo is not None else None,
        'range_high': hi,
        'mae': mae,
        'rmse': metrics.get('rmse'),
        'r2': metrics.get('r2'),
        'model': metrics.get('model', name),
        'features': X.iloc[0].to_dict(),
        'location': location,
        'feature_columns': feature_columns()
    }
