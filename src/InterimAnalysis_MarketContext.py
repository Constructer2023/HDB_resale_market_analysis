import pandas as pd

def quarterly_trx_summary(trx: pd.DataFrame):
    df = trx.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['trx_date']):
        df['trx_date'] = pd.to_datetime(df['trx_date'])
    df['trx_qtr'] = df['trx_date'].dt.quarter
    df['trx_date'] = df['trx_date'].dt.to_period('Q').astype(str)
    g = (
        df.groupby(['trx_year', 'trx_qtr', 'trx_date'], as_index = False).agg(
            volume = ('resale_price', 'size'),
            mean_price = ('resale_price', 'mean'),
            median_price = ('resale_price', 'median'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median')
        )
    )
    g['quarter_start'] = pd.PeriodIndex(g['trx_date'], freq = 'Q').to_timestamp()
    return g.sort_values('quarter_start').reset_index(drop = True)

def quarterly_pps_by_flat_type(trx: pd.DataFrame):
    df = trx.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['trx_date']):
        df['trx_date'] = pd.to_datetime(df['trx_date'])
    df['trx_date'] = df['trx_date'].dt.to_period('Q').astype(str)
    g = (
        df.groupby(['trx_date', 'flat_type'], as_index = False).agg(
            volume = ('resale_price', 'size'),
            mean_price = ('resale_price', 'mean'),
            median_price = ('resale_price', 'median'),
            mean_pps = ('price_per_sqm', 'mean'),
            median_pps = ('price_per_sqm', 'median')
        )
    )
    g['quarter_start'] = pd.PeriodIndex(g['trx_date'], freq = 'Q').to_timestamp()
    return g.sort_values(['quarter_start', 'flat_type']).reset_index(drop = True)

def quarterly_applications_total(apps: pd.DataFrame):
    """
    apps = load_resale_applications()
    """
    g = (
        apps.groupby(['trx_period', 'trx_year', 'trx_qtr'], as_index = False).agg(
            num = ('num', 'sum')
        )
    )
    g.rename(columns = {'trx_period': 'trx_date'}, inplace = True)
    g['quarter_start'] = pd.PeriodIndex(g['trx_date'], freq = 'Q').to_timestamp()
    return g.sort_values('quarter_start').reset_index(drop = True)

def compare_trx_vs_rpi(trx_q: pd.DataFrame, rpi: pd.DataFrame):
    """
    trx_q = quarterly_trx_summary(...)
    rpi = load_resale_price_index()
    """
    m = trx_q.merge(rpi[['trx_date', 'rpi']], on = 'trx_date', how = 'inner')
    m['price_to_index_ratio'] = m['median_price'] / m['rpi']
    return m

def compare_volume_vs_applications(trx_q: pd.DataFrame, apps_q: pd.DataFrame):
    m = trx_q.merge(apps_q[['trx_date', 'num']], on = 'trx_date', how = 'inner')
    m['conversion_pct'] = m['volume'] * 100.0 / m['num']
    return m

def actual_vs_official_median(trx: pd.DataFrame, official: pd.DataFrame, min_count: int = 5):
    """
    Compare actual transaction mean/median price vs official median_resale_prices
    at town + flat_type + quarter grain.
    """
    df = trx.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['trx_date']):
        df['trx_period'] = pd.to_datetime(df['trx_date'])
    df['trx_date'] = df['trx_date'].dt.to_period('Q').astype(str)
    actual = (
        df.groupby(['trx_date', 'town', 'flat_type'], as_index = False).agg(
            actual_volume = ('resale_price', 'size'),
            actual_mean_price = ('resale_price', 'mean'),
            actual_median_price = ('resale_price', 'median')
        )
    )
    m = actual.merge(
        official[['trx_date', 'town', 'flat_type', 'median_resale_price']],
        on = ['trx_date', 'town', 'flat_type'],
        how = 'inner',
    )
    m = m[m['actual_volume'] >= min_count].copy()
    m['diff'] = m['actual_median_price'] - m['median_resale_price']
    m['diff_pct'] = m['diff'] * 100.0 / m['median_resale_price']
    return m

def annual_applications(apps: pd.DataFrame, year_from = 2017, year_to = 2025):
    g = (
        apps[apps['trx_year'].between(year_from, year_to)].groupby(
            'trx_year', as_index = False
        ).agg(
            total_applications = ('num', 'sum')
        )
    )
    return g.sort_values('trx_year')

def annual_applications_by_type(apps: pd.DataFrame, year_from = 2017, year_to = 2025):
    g = (
        apps[apps['trx_year'].between(year_from, year_to)].groupby(
            ['trx_year', 'flat_type'], as_index = False
        ).agg(
            applications = ('num', 'sum')
        )
    )
    return g.sort_values(['trx_year', 'flat_type'])
