from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from src_model.config import (
    default_lgbm_params_v1,
    default_rf_params_v1,
    default_ridge_params_v1,
    default_xgb_params_v1,
    random_seed,
    target_col,
    test_path_v1,
    train_path_v1,
)
from src_model.feature_engineering_v1 import build_preprocessor
from src_model.utils import save_model, set_seed, setup_logging

logger = logging.getLogger(__name__)

class MedianBaseline(BaseEstimator, RegressorMixin):
    """
    Global median of training targets (naïve baseline).
    """
    def __init__(self):
        self.median_ = None
    def fit(self, X, y):
        self.median_ = float(np.median(np.asarray(y, dtype = float)))
        return self
    def predict(self, X):
        if self.median_ is None:
            raise RuntimeError('MedianBaseline is not fitted.')
        n = X.shape[0] if hasattr(X, 'shape') else len(X)
        return np.full(n, self.median_, dtype = float)

def load_model_ready_data(train_csv: str = train_path_v1, test_csv: str = test_path_v1):
    """
    Load train_v1.csv / test_v1.csv produced by run_feature_engineering().
    """
    train = pd.read_csv(train_csv, low_memory = False)
    test = pd.read_csv(test_csv, low_memory = False)
    y_train = train[target_col]
    y_test = test[target_col]
    X_train = train.drop(columns = [target_col])
    X_test = test.drop(columns = [target_col])
    return X_train, X_test, y_train, y_test

def get_model_zoo() :
    """
    Unfitted estimators for v1 comparison.
    """
    models: Dict[str, Any] = {
        'median_baseline_v1': MedianBaseline(),
        'linear_regression_v1': LinearRegression(),
        'ridge_v1': Ridge(**default_ridge_params_v1),
        'random_forest_v1': RandomForestRegressor(**default_rf_params_v1),
        'xgboost_v1': XGBRegressor(**default_xgb_params_v1),
        'lightgbm_v1': LGBMRegressor(**default_lgbm_params_v1)
    }
    return models

def build_pipeline(estimator: Any, X_sample: pd.DataFrame):
    """
    Preprocessor (fit on train only) + model.
    """
    return Pipeline(
        steps = [
            ('preprocessor', build_preprocessor(X_sample)),
            ('model', estimator)
        ]
    )

def train_single_model(name: str, estimator: Any, X_train: pd.DataFrame, y_train: pd.Series, save: bool = True):
    """
    Fit one pipeline; optionally save to model/{name}.joblib.
    """
    set_seed(random_seed)
    pipe = build_pipeline(clone(estimator), X_train)
    logger.info('Training %s ...', name)
    t0 = time.perf_counter()
    pipe.fit(X_train, y_train)
    elapsed = time.perf_counter() - t0
    logger.info('Finished %s in %.1f s', name, elapsed)
    info: Dict[str, Any] = {
        'name': name,
        'train_time_sec': round(elapsed, 2),
        'n_train_samples': int(len(X_train))
    }
    if save:
        path = save_model(pipe, name)
        info['model_path'] = path
    return pipe, info

def train_all_models(X_train: Optional[pd.DataFrame] = None,
                     y_train: Optional[pd.Series] = None,
                     model_names: Optional[List[str]] = None,
                     save: bool = True):
    """
    Train the v1 model zoo (or a subset of names).
    Returns
    -------
    {
      'models': {name: fitted Pipeline, ...},
      'infos':  {name: info_dict, ...}
    }
    """
    setup_logging()
    if X_train is None or y_train is None:
        X_train, _, y_train, _ = load_model_ready_data()
    zoo = get_model_zoo()
    if model_names is not None:
        zoo = {k: v for k, v in zoo.items() if k in model_names}
    fitted: Dict[str, Any] = {}
    infos: Dict[str, Any] = {}
    for name, est in zoo.items():
        try:
            pipe, info = train_single_model(name, est, X_train, y_train, save = save)
            fitted[name] = pipe
            infos[name] = info
        except Exception as e:
            logger.exception('Failed to train %s: %s', name, e)
            infos[name] = {'name': name, 'error': str(e)}
    return {'models': fitted, 'infos': infos}

if __name__ == '__main__':
    result = train_all_models()
    print('Trained:', list(result['models'].keys()))
    for name, info in result['infos'].items():
        print(name, info)
