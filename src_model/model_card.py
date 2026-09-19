from __future__ import annotations
import logging
from datetime import datetime
from src_model.config import (
    model_card_path,
    report_dir,
    train_year,
    test_year,
    forbidden_cols,
    always_drop_v2
)

logger = logging.getLogger(__name__)

def build_model_card_markdown(model_name: str, version: str, test_metrics: dict,
                              train_metrics: dict | None = None, feature_columns: list | None = None,
                              n_train: int | None = None, n_test: int | None = None,
                              notes: str | None = None, error_summary: dict | None = None):
    lines = [
        f'# Model Card — HDB Resale Price Prediction ({version})',
        '',
        f'- **Generated:** {datetime.now().strftime('%d-%m-%Y %H:%M')}',
        f'- **Model:** `{model_name}`',
        f'- **Version:** {version}',
        f'- **Target:** `resale_price`',
        '',
        '## Intended use',
        '',
        'Estimate HDB resale transaction prices from property, time, location,',
        'and (in v2) MRT-related features. For analysis and benchmarking, not',
        'a formal valuation product.',
        '',
        '## Data & split',
        '',
        f'- Train years: **{min(train_year)}–{max(train_year)}**' if version == 'v2'
        else '- Train years: **2017–2025**',
        f'- Test year: **{test_year if version == 'v2' else 2026}** (temporal holdout)',
        f'- n_train: {n_train}',
        f'- n_test: {n_test}',
        '',
        '## Target leakage controls',
        '',
        '- Never use `price_per_sqm` as a feature (derived from price and area).',
        f'- v2 also drops: `{sorted(forbidden_cols | always_drop_v2)}`' if version == 'v2'
        else '- v1 drops MRT-related and raw coordinate features.',
        '',
        '## Test metrics',
        '',
        f'| Metric | Value |',
        f'|--------|-------|',
        f'| RMSE | {test_metrics.get('rmse', float('nan')):,.0f} |',
        f'| MAE | {test_metrics.get('mae', float('nan')):,.0f} |',
        f'| MAPE (%) | {test_metrics.get('mape', float('nan')):.2f} |',
        f'| R² | {test_metrics.get('r2', float('nan')):.4f} |',
        ''
    ]
    if train_metrics:
        lines += [
            '## Train metrics (reference)',
            '',
            f'- train RMSE: {train_metrics.get('train_rmse', train_metrics.get('rmse', 'n/a'))}',
            f'- train MAE: {train_metrics.get('train_mae', train_metrics.get('mae', 'n/a'))}',
            f'- train R²: {train_metrics.get('train_r2', train_metrics.get('r2', 'n/a'))}',
            ''
        ]
    if error_summary:
        lines += [
            '## Residual summary (test)',
            '',
            f'- mean residual: {error_summary.get('mean_residual', float('nan')):,.0f}',
            f'- median residual: {error_summary.get('median_residual', float('nan')):,.0f}',
            f'- median abs error: {error_summary.get('median_ae', float('nan')):,.0f}',
            ''
        ]
    if feature_columns:
        lines += [
            '## Features',
            '',
            f'- Count: {len(feature_columns)}',
            f'- List: `{feature_columns}`',
            ''
        ]
    lines += [
        '## Limitations',
        '',
        '- Temporal shift: 2026 test may differ from 2017–2025 train regime.',
        '- MRT features (v2) assume station/exit geography; construction timing not modelled.',
        '- High-cardinality categoricals (`blk`, `postal`) are capped in one-hot encoding.',
        '- Does not include unit-level condition, orientation, or renovation quality.',
        '',
        '## Ethical / practical notes',
        '',
        '- Predictions are statistical estimates only.',
        '- Avoid using as sole input for financial or legal decisions.',
        ''
    ]
    if notes:
        lines += ['## Additional notes', '', notes, '']
    return '\n'.join(lines)

def write_model_card(model_name: str, version: str, test_metrics: dict,
                     train_metrics: dict | None = None, feature_columns: list | None = None,
                     n_train: int | None = None, n_test: int | None = None,
                     notes: str | None = None, error_summary: dict | None = None,
                     path: str | None = None):
    if path == None:
        path = model_card_path
    else:
        path = path
    md = build_model_card_markdown(
        model_name = model_name,
        version = version,
        test_metrics = test_metrics,
        train_metrics = train_metrics,
        feature_columns = feature_columns,
        n_train = n_train,
        n_test = n_test,
        notes = notes,
        error_summary = error_summary
    )
    with open(path, 'w', encoding = 'utf-8') as f:
        f.write(md)
    logger.info('Wrote model card -> %s', path)
    return path
