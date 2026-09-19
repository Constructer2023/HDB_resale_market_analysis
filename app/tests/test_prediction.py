from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from app.services.location_lookup import remaining_lease_to_months
from app.services.predictor import PredictionError, build_feature_frame, feature_columns, validate_inputs

project_root = Path(__file__).resolve().parents[2]
meta_path = project_root / 'data' / 'model_based' / 'feature_meta_v2.json'

def test_remaining_lease_years_to_months():
    assert remaining_lease_to_months(61) == 61 * 12

def test_remaining_lease_already_months():
    assert remaining_lease_to_months(732) == 732

def test_remaining_lease_non_positive():
    with pytest.raises(ValueError):
        remaining_lease_to_months(0)

def _valid_payload(**overrides):
    base = {
        'st': 'ANG MO KIO AVE 3',
        'blk': '123',
        'trx_year': 2026,
        'trx_month': 3,
        'flat_type': '4 ROOM',
        'flat_model': 'Improved',
        'floor_area_sqm': 92.0,
        'storey_range': '08',
        'remaining_lease': 60,
    }
    base.update(overrides)
    return base

def test_validate_ok():
    assert validate_inputs(_valid_payload()) == []

def test_validate_missing_street():
    errs = validate_inputs(_valid_payload(st=''))
    assert any('st' in e for e in errs)

def test_validate_floor_area_must_be_positive():
    errs = validate_inputs(_valid_payload(floor_area_sqm=0))
    assert any('floor_area' in e for e in errs)

def test_validate_floor_area_too_large():
    errs = validate_inputs(_valid_payload(floor_area_sqm=500))
    assert any('too large' in e for e in errs)

def test_validate_month_range():
    errs = validate_inputs(_valid_payload(trx_month=13))
    assert any('trx_month' in e for e in errs)

SAMPLE_COLS = [
    'trx_year',
    'trx_month',
    'flat_type',
    'flat_model',
    'floor_area_sqm',
    'storey_lower',
    'storey_midpoint',
    'storey_upper',
    'remaining_lease_month',
    'blk',
    'st',
    'town',
    'subzone',
    'zone_id',
    'lat',
    'lon',
    'to_mrt',
    'to_city',
    'nearest_mrt',
]

def test_build_feature_frame_order_and_no_leakage():
    payload = _valid_payload()
    location = {
        'st': 'ANG MO KIO AVE 3',
        'blk': '123',
        'town': 'ANG MO KIO',
        'subzone': 'ANG MO KIO',
        'zone_id': 1,
        'lat': 1.37,
        'lon': 103.84,
        'to_mrt': 420.0,
        'to_city': 9800.0,
        'nearest_mrt': 'ANG MO KIO',
    }
    with patch('app.services.predictor.feature_columns', return_value=SAMPLE_COLS):
        X = build_feature_frame(payload, location)
    assert list(X.columns) == SAMPLE_COLS
    assert 'price_per_sqm' not in X.columns
    assert 'resale_price' not in X.columns
    assert X.shape == (1, len(SAMPLE_COLS))
    assert int(X.loc[0, 'storey_lower']) == 7
    assert int(X.loc[0, 'storey_upper']) == 9
    assert int(X.loc[0, 'remaining_lease_month']) == 60 * 12
    assert float(X.loc[0, 'to_mrt']) == 420.0
    assert X.loc[0, 'flat_type'] == '4 ROOM'

def test_build_feature_frame_uses_meta_if_present():
    if not meta_path.exists():
        pytest.skip('feature_meta_v2.json not on disk')
    cols = feature_columns()
    assert cols, 'feature_columns must be non-empty'
    assert 'price_per_sqm' not in cols
    assert 'resale_price' not in cols

    payload = _valid_payload()
    location = {
        'st': payload['st'],
        'blk': payload['blk'],
        'lat': 1.37,
        'lon': 103.84,
        'to_mrt': 400.0,
        'to_city': 10000.0,
        'subzone': 'ANG MO KIO',
        'zone_id': 1,
        'nearest_mrt': 'ANG MO KIO',
        'town': 'ANG MO KIO',
    }
    X = build_feature_frame(payload, location)
    assert list(X.columns) == cols

def test_estimate_price_mocked():
    from app.services import predictor as pred
    payload = _valid_payload()
    location = {
        'st': payload['st'],
        'blk': payload['blk'],
        'lat': 1.37,
        'lon': 103.84,
        'to_mrt': 400.0,
        'to_city': 10000.0,
        'subzone': 'ANG MO KIO',
        'zone_id': 1,
        'nearest_mrt': 'ANG MO KIO',
        'town': 'ANG MO KIO',
    }
    class FakePipe:
        def predict(self, X):
            assert list(X.columns) == SAMPLE_COLS
            return np.array([512000.0])
    with (
        patch.object(pred, 'feature_columns', return_value=SAMPLE_COLS),
        patch.object(pred, 'lookup_location', return_value=location),
        patch.object(pred, 'choose_model_name', return_value='xgboost_v2'),
        patch.object(pred, 'load_pipeline', return_value=FakePipe()),
        patch.object(
            pred,
            'model_metrics',
            return_value={'model': 'xgboost_v2', 'mae': 25000.0, 'rmse': 40000.0, 'r2': 0.9},
        ),
    ):
        out = pred.estimate_price(payload)
    assert out['estimated_price'] == 512000.0
    assert out['range_low'] == 487000.0
    assert out['range_high'] == 537000.0
    assert out['model'] == 'xgboost_v2'
    assert out['mae'] == 25000.0

def test_estimate_price_rejects_bad_area():
    with pytest.raises(PredictionError):
        from app.services.predictor import estimate_price
        estimate_price(_valid_payload(floor_area_sqm = -10))
