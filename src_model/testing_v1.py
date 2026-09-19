from __future__ import annotations
import logging
from typing import Any, List, Optional, Sequence
import numpy as np
import pandas as pd
from src_model.config import model_dir
from src_model.training_v1 import load_model_ready_data
from src_model.utils import load_model, regression_metrics, setup_logging

logger = logging.getLogger(__name__)

def evaluate_predictions(y_true: Sequence[float], y_pred: Sequence[float], prefix: str = ''):
    metrics = regression_metrics(y_true, y_pred)
    if prefix:
        metrics = {f'{prefix}{k}': v for k, v in metrics.items()}
    return metrics

def evaluate_model(model: Any, X: pd.DataFrame, y: pd.Series, prefix: str = ''):
    y_pred = model.predict(X)
    return evaluate_predictions(y, y_pred, prefix = prefix)

def evaluate_on_test(model_name: str, X_test: Optional[pd.DataFrame] = None, y_test: Optional[pd.Series] = None):
    """
    Load model/{model_name}.joblib and score on the 2026 test set.
    """
    setup_logging()
    if X_test is None or y_test is None:
        _, X_test, _, y_test = load_model_ready_data()
    model = load_model(model_name)
    metrics = evaluate_model(model, X_test, y_test)
    metrics['model'] = model_name
    metrics['n_test'] = int(len(y_test))
    logger.info(
        '%s | RMSE = %.0f  MAE = %.0f  MAPE = %.2f%%  R2 = %.4f',
        model_name,
        metrics['rmse'],
        metrics['mae'],
        metrics['mape'],
        metrics['r2']
    )
    return metrics

def evaluate_on_train(model_name: str, X_train: Optional[pd.DataFrame] = None, y_train: Optional[pd.Series] = None):
    """
    Optional: train-set metrics (for overfit check).
    """
    setup_logging()
    if X_train is None or y_train is None:
        X_train, _, y_train, _ = load_model_ready_data()
    model = load_model(model_name)
    metrics = evaluate_model(model, X_train, y_train, prefix = 'train_')
    metrics['model'] = model_name
    metrics['n_train'] = int(len(y_train))
    return metrics

def evaluate_all_saved_models(model_names: Optional[List[str]] = None,
                              X_test: Optional[pd.DataFrame] = None,
                              y_test: Optional[pd.Series] = None):
    """
    Evaluate every saved .joblib in model/ (or a given list) on the test set.
    Returns a DataFrame sorted by RMSE ascending.
    """
    setup_logging()
    if X_test is None or y_test is None:
        _, X_test, _, y_test = load_model_ready_data()
    if model_names is None:
        import os
        model_names = sorted(f[:-7] for f in os.listdir(model_dir) if f.endswith('_v1.joblib'))
    rows = []
    for name in model_names:
        try:
            m = evaluate_on_test(name, X_test, y_test)
            rows.append(m)
        except Exception as e:
            logger.warning('Could not evaluate %s: %s', name, e)
            rows.append({'model': name, 'error': str(e)})
    df = pd.DataFrame(rows)
    if 'rmse' in df.columns:
        df = df.sort_values('rmse').reset_index(drop = True)
    return df

def get_feature_importance(model: Any, top_n: int = 30):
    """
    Feature importances / coefficients from a fitted Pipeline.
    """
    est = model
    feature_names = None
    if hasattr(model, 'named_steps'):
        est = model.named_steps.get('model', model)
        pre = model.named_steps.get('preprocessor')
        if pre is not None and hasattr(pre, 'get_feature_names_out'):
            try:
                feature_names = list(pre.get_feature_names_out())
            except Exception:
                feature_names = None
    if hasattr(est, 'feature_importances_'):
        imp = np.asarray(est.feature_importances_, dtype = float)
        if feature_names is None or len(feature_names) != len(imp):
            feature_names = [f'f{i}' for i in range(len(imp))]
        return (
            pd.DataFrame(
                {'feature': feature_names, 'importance': imp}
            ).sort_values(
                'importance', ascending = False
            ).head(top_n).reset_index(drop = True)
        )
    if hasattr(est, 'coef_'):
        coef = np.ravel(est.coef_).astype(float)
        if feature_names is None or len(feature_names) != len(coef):
            feature_names = [f'f{i}' for i in range(len(coef))]
        return (
            pd.DataFrame(
                {'feature': feature_names, 'coefficient': coef}
            ).assign(
                abs_coef = lambda d: d['coefficient'].abs()
            ).sort_values(
                'abs_coef', ascending = False
            ).head(top_n).drop(columns = ['abs_coef']).reset_index(drop = True)
        )
    logger.info('Model has no feature_importances_ or coef_.')
    return None

def predict_test(model_name: str, X_test: Optional[pd.DataFrame] = None):
    """
    Return test predictions for residual / plot analysis.
    """
    if X_test is None:
        _, X_test, _, _ = load_model_ready_data()
    model = load_model(model_name)
    return np.asarray(model.predict(X_test), dtype = float)

if __name__ == '__main__':
    df = evaluate_all_saved_models()
    print(df)
