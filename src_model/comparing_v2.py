from __future__ import annotations
import logging
import os
from typing import Dict, List, Optional
import pandas as pd
from src_model.config import comparison_path_v2, model_dir
from src_model.testing_v2 import evaluate_all_saved_models, get_feature_importance
from src_model.training_v2 import train_all_models
from src_model.utils import list_saved_models_v2, setup_logging, load_model

logger = logging.getLogger(__name__)

def run_full_comparison(retrain: bool = False, model_names: Optional[List[str]] = None, save: bool = True):
    """
    1) Optionally retrain
    2) Evaluate all saved models on 2026 test
    3) Save model_comparison_v2.csv
    """
    setup_logging()
    if retrain:
        logger.info('Retraining models ...')
        train_all_models(model_names = model_names, save = True)
    logger.info('Evaluating models on test set ...')
    comparison_df = evaluate_all_saved_models(model_names = model_names)
    if save:
        comparison_df.to_csv(comparison_path_v2, index = False)
        logger.info('Comparison v2 saved -> %s', comparison_path_v2)
    cols = [
        c
        for c in ['model', 'rmse', 'mae', 'mape', 'r2', 'n_test']
        if c in comparison_df.columns
    ]
    if cols:
        print('\n=== Model Comparison v2 (sorted by RMSE) ===')
        print(
            comparison_df[cols].to_string(
                index = False,
                float_format = lambda x: f'{x:,.2f}'
            )
        )
    return comparison_df

def collect_feature_importances(model_names: Optional[List[str]] = None, top_n: int = 20):
    """
    Top importances / coefficients for tree or linear models.
    """
    if model_names is None:
        model_names = list_saved_models_v2()
        if not model_names:
            model_names = sorted(f[:-7] for f in os.listdir(model_dir) if f.endswith('_v2.joblib'))
    result: Dict[str, pd.DataFrame] = {}
    for name in model_names:
        try:
            model = load_model(name)
            fi = get_feature_importance(model, top_n = top_n)
            if fi is not None:
                result[name] = fi
                logger.info('FI for %s: %d rows', name, len(fi))
        except Exception as e:
            logger.warning('Could not get FI for %s: %s', name, e)
    return result

def summary_report(comparison_df: Optional[pd.DataFrame] = None):
    if comparison_df is None:
        if not os.path.exists(comparison_path_v2):
            return 'No comparison results. Run run_full_comparison() first.'
        comparison_df = pd.read_csv(comparison_path_v2)
    if comparison_df.empty or 'rmse' not in comparison_df.columns:
        return 'Comparison table is empty or incomplete.'
    ok = comparison_df.dropna(subset = ['rmse']).sort_values('rmse')
    if ok.empty:
        return 'No successful model evaluations.'
    best = ok.iloc[0]
    lines = [
        'HDB Resale Price Prediction – Model Comparison v2',
        '=' * 55,
        f'Best model (lowest RMSE): {best['model']}',
        f'  RMSE : {best['rmse']:,.0f}',
        f'  MAE  : {best['mae']:,.0f}',
        f'  MAPE : {best['mape']:.2f}%',
        f'  R²   : {best['r2']:.4f}',
        '',
        'All models (RMSE ascending):'
    ]
    for _, row in ok.iterrows():
        lines.append(
            f'  - {str(row['model']):<20} '
            f'RMSE = {row['rmse']:>10,.0f}  R² = {row['r2']:.4f}'
        )
    return '\n'.join(lines)


if __name__ == '__main__':
    df = run_full_comparison(retrain = False)
    print(summary_report(df))
