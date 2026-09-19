from __future__ import annotations
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .location_lookup import load_transactions_geo, _norm

def find_comparables(street: str, block: str, flat_type: str | None = None,
                     floor_area_sqm: float | None = None, n: int = 8, area_tol: float = 15.0):
    trx = load_transactions_geo()
    st, blk = _norm(street), _norm(block)
    work = trx.copy()
    work['_dt'] = pd.to_datetime(work['trx_date'], errors = 'coerce')
    same_addr = (work.get('st') == st) & (work.get('blk') == blk)
    same_st = work.get('st') == st
    subzone = None
    vals = work.loc[same_addr, 'subzone'].dropna()
    if not vals.empty:
        subzone = vals.iloc[-1]
    same_zone = (
        work['subzone'] == subzone
        if subzone is not None and 'subzone' in work.columns
        else pd.Series(False, index = work.index)
    )
    same_type = (
        work['flat_type'].astype(str).str.strip() == str(flat_type).strip()
        if flat_type and 'flat_type' in work.columns
        else pd.Series(True, index = work.index)
    )
    if floor_area_sqm and 'floor_area_sqm' in work.columns:
        area = pd.to_numeric(work['floor_area_sqm'], errors = 'coerce')
        area_ok = (area - float(floor_area_sqm)).abs() <= area_tol
    else:
        area_ok = pd.Series(True, index = work.index)
    layers = [same_addr & same_type, same_st & same_type & area_ok,
              same_zone & same_type & area_ok, same_st]
    picked = []
    used = pd.Series(False, index = work.index)
    for mask in layers:
        extra = work.loc[mask & ~used].sort_values('_dt', ascending = False)
        if extra.empty:
            continue
        take = extra.head(n - len(picked))
        picked.append(take)
        used.loc[take.index] = True
        if sum(len(p) for p in picked) >= n:
            break
    if not picked:
        return pd.DataFrame()
    out = pd.concat(picked, axis = 0).head(n)
    keep = [c for c in ['trx_date', 'trx_year', 'trx_month', 'blk', 'st', 'subzone',
                        'flat_type', 'flat_model', 'floor_area_sqm', 'storey_range',
                        'storey_midpoint', 'resale_price', 'price_per_sqm', 'remaining_lease_month'
                        ]
                        if c in out.columns
    ]
    return out[keep].reset_index(drop = True)

def comparables_summary(comp: pd.DataFrame):
    if comp is None or comp.empty or 'resale_price' not in comp.columns:
        return {
            'n': 0,
            'median_price': None,
            'mean_price': None,
            'min_price': None,
            'max_price': None,
        }
    p = pd.to_numeric(comp['resale_price'], errors = 'coerce').dropna()
    if p.empty:
        return {
            'n': 0,
            'median_price': None,
            'mean_price': None,
            'min_price': None,
            'max_price': None,
        }
    return {
        'n': int(len(p)),
        'median_price': float(p.median()),
        'mean_price': float(p.mean()),
        'min_price': float(p.min()),
        'max_price': float(p.max()),
    }
