from __future__ import annotations
import sys
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import services.comparables
from services.location_lookup import (
    list_blocks,
    list_streets,
    lookup_location,
    storey_options,
    unique_values
)
from services.predictor import (
    PredictionError,
    estimate_price,
    model_metrics,
    validate_inputs
)

st.set_page_config(
    page_title = 'HDB Resale Price Estimator',
    page_icon = '🏠',
    layout = 'wide'
)

DISCLAIMER = (
    'Estimates are indicative market-price predictions based on historical '
    'transactions, not official valuations. They are not a formal appraisal '
    'and should not be the sole basis for financial or legal decisions.'
)

@st.cache_data(show_spinner = False)
def _streets():
    return list_streets()

@st.cache_data(show_spinner = False)
def _blocks(street: str):
    return list_blocks(street)

@st.cache_data(show_spinner = False)
def _opts(col: str):
    return unique_values(col)

@st.cache_data(show_spinner = False)
def _storeys():
    op = storey_options()
    op = [int(i) for i in op]
    mx, mn = max(op), min(op)
    res = list(range(mn, mx + 1))
    return res

def _money(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '—'
    return f'S${float(v):,.0f}'

def main():
    st.title('HDB resale price estimator')
    st.caption('v2 model · location features filled from the local geocode cache')
    st.info(DISCLAIMER)
    try:
        streets = _streets()
        types = _opts('flat_type')
        models = _opts('flat_model')
        storeys = _storeys()
        metrics = model_metrics()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()
    today = date.today()
    st.subheader('1. Location')
    c1, c2 = st.columns(2)
    with c1:
        st_sel = st.selectbox(
            'Street (st)',
            options = streets,
            index = None,
            placeholder = 'Select a street',
        )
    with c2:
        blocks = _blocks(st_sel) if st_sel else []
        blk_sel = st.selectbox(
            'Block (blk)',
            options = blocks,
            index = None,
            placeholder = 'Select a block',
            disabled = not bool(st_sel),
        )
    loc = None
    loc_error = None
    if st_sel and blk_sel:
        try:
            loc = lookup_location(st_sel, blk_sel)
        except KeyError as e:
            loc_error = str(e)
    if loc_error:
        st.error(loc_error)
    elif loc:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric('Subzone', loc.get('subzone') or '—')
        m2.metric('Nearest MRT', loc.get('nearest_mrt') or '—')
        to_mrt = loc.get('to_mrt')
        to_city = loc.get('to_city')
        m3.metric('to_mrt (m)', f'{float(to_mrt):,.0f}' if to_mrt is not None else '—')
        m4.metric('to_city (m)', f'{float(to_city):,.0f}' if to_city is not None else '—')
        with st.expander('All auto-filled location features'):
            st.json(
                {
                    k: loc.get(k)
                    for k in (
                        'subzone',
                        'zone_id',
                        'postal',
                        'lat',
                        'lon',
                        'nearest_mrt',
                        'mrt_lat',
                        'mrt_lon',
                        'to_mrt',
                        'to_city'
                    )
                    if k in loc
                }
            )
    st.subheader('2. Property')
    with st.form('estimate_form'):
        r1, r2, r3 = st.columns(3)
        with r1:
            trx_year = st.number_input(
                'Expected year',
                min_value = 2017,
                max_value = 2030,
                value = min(max(today.year, 2017), 2030),
                step = 1,
            )
        with r2:
            trx_month = st.selectbox(
                'Expected month',
                options = list(range(1, 13)),
                index = today.month - 1,
                format_func = lambda m: f'{m:02d}',
            )
        with r3:
            floor_area = st.number_input(
                'Floor area (sqm)',
                min_value = 0.0,
                max_value = 400.0,
                value = 90.0,
                step = 1.0,
            )
        r4, r5, r6 = st.columns(3)
        with r4:
            flat_type = st.selectbox(
                'Flat type',
                options = types,
                index = None,
                placeholder = 'Select flat type',
            )
        with r5:
            flat_model = st.selectbox(
                'Flat model',
                options = models,
                index = None,
                placeholder = 'Select flat model (optional)',
            )
        with r6:
            storey = st.selectbox(
                'Storey range',
                options = storeys,
                index = None,
                placeholder = 'e.g. 07 TO 09',
            )
        remaining_lease_years = st.number_input(
            'Remaining lease (years)',
            min_value = 0.0,
            max_value = 99.0,
            value = 60.0,
            step = 0.5,
            help = 'Converted to remaining_lease_month for the model.',
        )
        submitted = st.form_submit_button('Estimate Price', type = 'primary')
    if not submitted:
        return
    payload = {
        'st': st_sel,
        'blk': blk_sel,
        'trx_year': int(trx_year),
        'trx_month': int(trx_month),
        'flat_type': flat_type,
        'flat_model': flat_model,
        'floor_area_sqm': float(floor_area),
        'storey_range': storey,
        'remaining_lease': float(remaining_lease_years),
    }
    errs = validate_inputs(payload)
    if loc is None and not errs:
        errs.append('Select a valid street and block so location features can be filled.')
    if errs:
        for e in errs:
            st.error(e)
        return
    try:
        result = estimate_price(payload)
    except (PredictionError, FileNotFoundError, KeyError) as e:
        st.error(str(e))
        return
    st.divider()
    st.subheader('Estimate')
    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Estimated price', _money(result['estimated_price']))
    if result['range_low'] is not None and result['range_high'] is not None:
        k2.metric(
            'Indicative range (± MAE)',
            f'{_money(result['range_low'])} – {_money(result['range_high'])}',
        )
    else:
        k2.metric('Indicative range', 'MAE not available')
    k3.metric('Model MAE', _money(result['mae']) if result['mae'] is not None else '—')
    k4.metric('Chosen model', str(result['model']))
    if result.get('rmse') is not None or result.get('r2') is not None:
        st.caption(
            f'Test RMSE: {_money(result.get('rmse'))} · '
            f'R²: {result['r2']:.4f}' if result.get('r2') is not None else
            f'Test RMSE: {_money(result.get('rmse'))}'
        )
    st.caption(
        f'Range uses test-set MAE from model_comparison_v2 '
        f'(currently {metrics.get('model', result['model'])}). '
        'It is not a prediction interval.'
    )
    try:
        comps = services.comparables.find_comparables(
            street = st_sel,
            block = blk_sel,
            flat_type = flat_type,
            floor_area_sqm = float(floor_area),
        )
        summary = services.comparables.comparables_summary(comps)
        st.subheader('Nearby recorded transactions')
        if summary['n'] == 0:
            st.write('No comparables found for this address / type.')
        else:
            st.caption(
                f'{summary['n']} comparables · '
                f'median {_money(summary['median_price'])} · '
                f'range {_money(summary['min_price'])} – {_money(summary['max_price'])}'
            )
            st.dataframe(comps, use_container_width = True, hide_index = True)
    except FileNotFoundError:
        pass
    with st.expander('Feature row sent to the model'):
        st.dataframe(
            pd.DataFrame([result['features']]),
            use_container_width = True,
            hide_index = True,
        )
        st.caption(
            'Column order matches feature_meta_v2.json. '
            'price_per_sqm is never used as a feature.'
        )


if __name__ == '__main__':
    main()
