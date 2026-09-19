from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from src_model.config import (
    default_lgbm_params_v2,
    default_rf_params_v2,
    default_ridge_params_v2,
    default_xgb_params_v2,
    target_col,
    model_dir,
    test_path_v2,
    train_path_v2,
    categorical_cols_v2,
    random_seed
)
from src_model.utils import set_seed, setup_logging, force_categorical_v2, save_model
from src_model.feature_engineering_v2 import build_preprocessor

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

def load_model_ready_data(train_csv: str = train_path_v2, test_csv: str = test_path_v2):
    """
    Load train_v2.csv / test_v2.csv from run_feature_engineering_v2().
    """
    train = pd.read_csv(train_csv, low_memory = False)
    test = pd.read_csv(test_csv, low_memory = False)
    if target_col not in train.columns or target_col not in test.columns:
        raise KeyError(f"Target '{target_col}' missing in train/test v2 files.")
    y_train = train[target_col]
    y_test = test[target_col]
    X_train = train.drop(columns = [target_col])
    X_test = test.drop(columns = [target_col])
    X_train = force_categorical_v2(X_train, categorical_cols_v2)
    X_test = force_categorical_v2(X_test, categorical_cols_v2)
    return X_train, X_test, y_train, y_test

def get_model_zoo():
    """
    Unfitted estimators for v2 comparison.
    """
    models: Dict[str, Any] = {
        'median_baseline_v2': MedianBaseline(),
        'linear_regression_v2': LinearRegression(),
        'ridge_v2': Ridge(**default_ridge_params_v2),
        'random_forest_v2': RandomForestRegressor(**default_rf_params_v2),
        'xgboost_v2': XGBRegressor(**default_xgb_params_v2),
        'lightgbm_v2': LGBMRegressor(**default_lgbm_params_v2)
    }
    return models

def build_pipeline(estimator: Any, X_sample: pd.DataFrame) -> Pipeline:
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
    logger.info("Finished v2 %s in %.1f s", name, elapsed)
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
    Train the v2 model zoo (or a subset of names).
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
        