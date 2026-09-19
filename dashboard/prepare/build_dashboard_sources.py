from __future__ import annotations
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category = FutureWarning)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA = PROJECT_ROOT / 'data'
AID = DATA / 'aid'
PROCESSED = DATA / 'processed'
MODEL_BASED = DATA / 'model_based'
SOURCE_OUT = PROJECT_ROOT / 'dashboard' / 'source'

def _first_existing(*candidates: Path):
    for p in candidates:
        if p is not None and p.exists():
            return p
    return None


def _col(df: pd.DataFrame, *names: str):
    lower_map = {c.lower(): c for c in df.columns}
    for n in names:
        if n in df.columns:
            return n
        if n.lower() in lower_map:
            return lower_map[n.lower()]
    return None


def _ensure_year_month(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    y = _col(df, 'trx_year', 'year')
    m = _col(df, 'trx_month', 'month')
    d = _col(df, 'trx_date', 'month')  # sometimes month is YYYY-MM

    if y is None and d is not None:
        dt = pd.to_datetime(df[d], errors = 'coerce')
        df['trx_year'] = dt.dt.year
        df['trx_month'] = dt.dt.month
        df['trx_date'] = dt
    else:
        if y is not None and y != 'trx_year':
            df['trx_year'] = pd.to_numeric(df[y], errors = 'coerce')
        if m is not None:
            if df[m].dtype == object and df[m].astype(str).str.contains('-').any():
                dt = pd.to_datetime(df[m], errors = 'coerce')
                df['trx_year'] = df.get('trx_year', dt.dt.year)
                df['trx_month'] = dt.dt.month
                if 'trx_date' not in df.columns:
                    df['trx_date'] = dt
            else:
                df['trx_month'] = pd.to_numeric(df[m], errors = 'coerce')
    if 'trx_year' in df.columns and 'trx_month' in df.columns:
        df['year_month'] = (
            df['trx_year'].astype('Int64').astype(str)
            + '-'
            + df['trx_month'].astype('Int64').astype(str).str.zfill(2)
        )
    return df

def load_transactions() -> pd.DataFrame:
    path = _first_existing(
        AID / 'resale_trx_geo.csv',
        AID / 'resale_transactions_geo.csv',
        PROCESSED / 'resale_transactions_geo.csv',
        PROCESSED / 'resale_transactions.csv'
    )
    if path is None:
        raise FileNotFoundError(
            'No transaction file found. Expected one of:\n'
            f'  {AID / 'resale_trx_geo.csv'}\n'
            f'  {PROCESSED / 'resale_transactions_geo.csv'}\n'
            f'  {PROCESSED / 'resale_transactions.csv'}'
        )
    print(f'[load] transactions <- {path}')
    df = pd.read_csv(path, low_memory = False)
    df = _ensure_year_month(df)
    rename = {}
    for src, dst in [
        ('block', 'blk'),
        ('street_name', 'st'),
        ('street', 'st')
    ]:
        c = _col(df, src)
        if c and dst not in df.columns:
            rename[c] = dst
    if rename:
        df = df.rename(columns = rename)
    price = _col(df, 'resale_price')
    area = _col(df, 'floor_area_sqm')
    if price and area and _col(df, 'price_per_sqm') is None:
        df['price_per_sqm'] = pd.to_numeric(df[price], errors = 'coerce') / pd.to_numeric(
            df[area], errors = 'coerce'
        ).replace(0, np.nan)
    print(f'[load] shape={df.shape}')
    return df

FACT_COLS_PREFERRED = [
    'trx_date',
    'trx_year',
    'trx_month',
    'year_month',
    'subzone',
    'zone_id',
    'blk',
    'st',
    'flat_type',
    'flat_model',
    'floor_area_sqm',
    'storey_midpoint',
    'storey_lower',
    'storey_upper',
    'lease_commence',
    'remaining_lease_month',
    'flat_year',
    'resale_price',
    'price_per_sqm',
    'lat',
    'lon',
    'to_city',
    'to_mrt',
    'nearest_mrt',
    'postal'
]

def build_fact(df: pd.DataFrame):
    cols = [c for c in FACT_COLS_PREFERRED if c in df.columns]
    fact = df[cols].copy()
    for c in ['resale_price', 'price_per_sqm', 'floor_area_sqm', 'to_city', 'to_mrt', 'lat', 'lon']:
        if c in fact.columns:
            fact[c] = pd.to_numeric(fact[c], errors = 'coerce')
    if 'resale_price' in fact.columns:
        fact = fact.dropna(subset = ['resale_price'])
    print(f'[fact] rows = {len(fact)} cols = {len(fact.columns)}')
    return fact

def build_monthly_summary(df: pd.DataFrame):
    need = ['trx_year', 'trx_month', 'resale_price']
    for c in need:
        if c not in df.columns:
            raise ValueError(f'monthly summary needs column: {c}')
    gcols = ['trx_year', 'trx_month']
    if 'year_month' in df.columns:
        gcols = ['trx_year', 'trx_month', 'year_month']
    agg = {
        'resale_price': ['count', 'mean', 'median', 'min', 'max']
    }
    if 'price_per_sqm' in df.columns:
        agg['price_per_sqm'] = ['mean', 'median']
    if 'floor_area_sqm' in df.columns:
        agg['floor_area_sqm'] = ['mean', 'median']
    g = df.groupby(gcols, dropna = False).agg(agg)
    g.columns = ['_'.join(c).strip('_') for c in g.columns.to_flat_index()]
    g = g.reset_index().rename(
        columns = {
            'resale_price_count': 'trx_volume',
            'resale_price_mean': 'mean_price',
            'resale_price_median': 'median_price',
            'resale_price_min': 'min_price',
            'resale_price_max': 'max_price',
            'price_per_sqm_mean': 'mean_pps',
            'price_per_sqm_median': 'median_pps',
            'floor_area_sqm_mean': 'mean_area',
            'floor_area_sqm_median': 'median_area'
        }
    )
    g = g.sort_values(['trx_year', 'trx_month']).reset_index(drop = True)
    print(f'[monthly] rows={len(g)}')
    return g

def build_subzone_summary(df: pd.DataFrame):
    key = _col(df, 'subzone')
    if key is None:
        print('[subzone] no subzone column — writing empty placeholder')
        return pd.DataFrame(
            columns = [
                'subzone',
                'lat',
                'lon'
                'zone_id',
                'trx_volume',
                'mean_price',
                'median_price',
                'mean_pps',
                'median_pps',
                'avg_to_city',
                'avg_to_mrt'
            ]
        )
    gcols = [key]
    zid = _col(df, 'zone_id')
    if zid:
        gcols.append(zid)
    work = df.copy()
    work['_price'] = pd.to_numeric(work[_col(work, 'resale_price')], errors = 'coerce')
    pps_c = _col(work, 'price_per_sqm')
    if pps_c:
        work['_pps'] = pd.to_numeric(work[pps_c], errors = 'coerce')
    city_c = _col(work, 'to_city')
    mrt_c = _col(work, 'to_mrt')
    rows = []
    for keys, part in work.groupby(gcols, dropna = False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = {gcols[i]: keys[i] for i in range(len(gcols))}
        rec['trx_volume'] = len(part)
        rec['mean_price'] = part['_price'].mean()
        rec['median_price'] = part['_price'].median()
        rec['lat'] = part['lat'].median()
        rec['lon'] = part['lon'].median()
        if '_pps' in part.columns:
            rec['mean_pps'] = part['_pps'].mean()
            rec['median_pps'] = part['_pps'].median()
        if city_c:
            rec['avg_to_city'] = pd.to_numeric(part[city_c], errors = 'coerce').mean()
        if mrt_c:
            rec['avg_to_mrt'] = pd.to_numeric(part[mrt_c], errors = 'coerce').mean()
        rows.append(rec)
    out = pd.DataFrame(rows)
    if 'subzone' not in out.columns and key in out.columns:
        out = out.rename(columns = {key: 'subzone'})
    if zid and zid in out.columns and 'zone_id' not in out.columns:
        out = out.rename(columns = {zid: 'zone_id'})
    out = out.sort_values('trx_volume', ascending = False).reset_index(drop = True)
    print(f'[subzone] rows = {len(out)}')
    return out

def build_model_metrics():
    frames = []
    for path, ver in [
        (MODEL_BASED / 'model_comparison_v1.csv', 'v1'),
        (MODEL_BASED / 'model_comparison_v2.csv', 'v2'),
        (MODEL_BASED / 'model_comparison.csv', 'v1'),
    ]:
        if path.exists():
            print(f'[metrics] load {path}')
            m = pd.read_csv(path)
            if 'version' not in m.columns:
                m['version'] = ver
            frames.append(m)
    if not frames:
        print('[metrics] no comparison CSV found — placeholder')
        return pd.DataFrame(
            columns=['model', 'rmse', 'mae', 'mape', 'r2', 'n_test', 'version']
        )
    out = pd.concat(frames, ignore_index = True)
    prefer = ['model', 'version', 'rmse', 'mae', 'mape', 'r2', 'n_test', 'n_train']
    cols = [c for c in prefer if c in out.columns] + [
        c for c in out.columns if c not in prefer
    ]
    out = out[cols]
    if 'rmse' in out.columns:
        out = out.sort_values(['version', 'rmse'], na_position = 'last').reset_index(drop = True)
    print(f'[metrics] rows = {len(out)}')
    return out

def build_model_predictions():
    path = _first_existing(
        MODEL_BASED / 'prediction_v2.csv',
        MODEL_BASED / 'prediction_v1.csv'
    )
    if path is None:
        print('[predictions] no prediction_test*.csv — placeholder')
        return pd.DataFrame(
            columns = [
                'actual',
                'predicted',
                'residual',
                'abs_error',
                'pct_error',
                'version',
                'flat_type',
                'town',
                'subzone'
            ]
        )
    print(f'[predictions] load {path}')
    df = pd.read_csv(path, low_memory = False)
    for c in ['actual', 'predicted']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors = 'coerce')
    if 'residual' not in df.columns and {'actual', 'predicted'} <= set(df.columns):
        df['residual'] = df['actual'] - df['predicted']
    if 'abs_error' not in df.columns and 'residual' in df.columns:
        df['abs_error'] = df['residual'].abs()
    if 'version' not in df.columns:
        df['version'] = 'v2' if 'v2' in path.name else 'v1'
    print(f'[predictions] rows = {len(df)}')
    return df

def main() -> None:
    print('PROJECT_ROOT:', PROJECT_ROOT)
    SOURCE_OUT.mkdir(parents = True, exist_ok = True)
    trx = load_transactions()
    fact = build_fact(trx)
    monthly = build_monthly_summary(trx)
    subzone = build_subzone_summary(trx)
    metrics = build_model_metrics()
    preds = build_model_predictions()
    paths = {
        'fact_transactions_dashboard.csv': fact,
        'monthly_market_summary.csv': monthly,
        'subzone_summary.csv': subzone,
        'model_metrics.csv': metrics,
        'model_test_predictions.csv': preds
    }
    for name, frame in paths.items():
        out = SOURCE_OUT / name
        frame.to_csv(out, index = False)
        print(f'[write] {out}  ({len(frame)} rows, {frame.shape[1]} cols)')
    print('\nDone. Point Power BI at:', SOURCE_OUT)


if __name__ == '__main__':
    main()
