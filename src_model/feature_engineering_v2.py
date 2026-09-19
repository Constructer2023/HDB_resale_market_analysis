from __future__ import annotations
import logging
import os
from typing import List, Optional, Sequence
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src_model.config import (
    always_drop_v2,
    categorical_cols_v2,
    feature_meta_path_v2,
    forbidden_cols,
    input_path,
    max_categories_v2,
    target_col,
    test_path_v2,
    test_year,
    train_path_v2,
    train_year,
    year_col,
)
from src_model.utils import force_categorical_v2, save_json, setup_logging

logger = logging.getLogger(__name__)

def select_feature_columns(df: pd.DataFrame, target: str = target_col):
    drop = {c.lower() for c in forbidden_cols} | {c.lower() for c in always_drop_v2}
    cols: List[str] = []
    for c in df.columns:
        cl = c.lower()
        if cl == target.lower():
            continue
        if cl in drop:
            logger.debug('Drop feature (v2): %s', c)
            continue
        cols.append(c)
    logger.info('Selected %d feature columns', len(cols))
    return cols

def load_raw_geo(path: Optional[str] = None):
    if path == None:
        path = input_path
    if not os.path.exists(path):
        raise FileNotFoundError(f'Expected geo file not found: {path}')
    logger.info('Loading %s ...', path)
    df = pd.read_csv(path, low_memory = False)
    logger.info('Loaded shape: %s', df.shape)
    return df

def infer_year_column(df: pd.DataFrame):
    for c in [year_col, 'year', 'transaction_year']:
        if c in df.columns:
            return c
    if 'trx_date' in df.columns:
        df[year_col] = pd.to_datetime(df['trx_date'], errors = 'coerce').dt.year
        return year_col
    raise ValueError(
        f"Cannot determine year column. Expected '{year_col}' or trx_date/month."
    )

def _parse_lease_strings(X: pd.DataFrame):
    X = X.copy()
    for col in list(X.columns):
        if col == 'lease_commence':
            X[col].astype(float)
            logger.info('Parsed string column: %s', col)
        elif col == 'remaining_lease_month':
            X[col].astype(float)
            logger.info('Parsed string column: %s', col)
    return X

def prepare_features_v2(df: pd.DataFrame, target: str = target_col, drop_na_target: bool = True):
    df = df.copy()
    ycol = infer_year_column(df)
    if drop_na_target:
        before = len(df)
        df = df.dropna(subset = [target])
        logger.info('Dropped %d rows with missing target', before - len(df))
    df = force_categorical_v2(df, categorical_cols_v2)
    feature_cols = select_feature_columns(df, target = target)
    X = df[feature_cols].copy()
    y = df[target].astype(float)
    years = df[ycol].astype(int)
    X = _parse_lease_strings(X)
    cat_present = [c for c in categorical_cols_v2 if c in X.columns]
    for c in cat_present:
        X[c] = X[c].astype('string').astype('category')
    return X, y, feature_cols, years

def temporal_split(X: pd.DataFrame, y: pd.Series, years: pd.Series,
                   train_years: Sequence[int] | None = None, test_years: int | None = None):
    if train_years is None:
        train_years = train_year
    if test_years is None:
        test_years = test_year
    train_mask = years.isin(list(train_years))
    test_mask = (years == test_years)
    n_train = int(train_mask.sum())
    n_test = int(test_mask.sum())
    logger.info(
        "Temporal split -> train: %d (%s-%s), test: %d (year = %s)",
        n_train,
        min(train_years),
        max(train_years),
        n_test,
        test_years
    )
    if n_train == 0:
        raise ValueError('No training rows after temporal split. Check year column.')
    if n_test == 0:
        logger.warning('No test rows for year %s.', test_years)
    return (
        X.loc[train_mask].reset_index(drop = True),
        X.loc[test_mask].reset_index(drop = True),
        y.loc[train_mask].reset_index(drop = True),
        y.loc[test_mask].reset_index(drop = True),
    )

def build_preprocessor(X: pd.DataFrame, numeric_strategy: str = 'median',
                       categorical_strategy: str = 'most_frequent', max_categories: int | None = None):
    if max_categories is None:
        max_categories = max_categories_v2
    cat_cols = X.select_dtypes(include = ['object', 'category', 'string']).columns.tolist()
    num_cols = [c for c in X.columns if c not in cat_cols]
    logger.info(
        'Preprocessor: %d numeric, %d categorical',
        len(num_cols),
        len(cat_cols)
    )
    numeric_pipe = Pipeline(
        steps = [
            ('imputer', SimpleImputer(strategy = numeric_strategy)),
            ('scaler', StandardScaler())
        ]
    )
    categorical_pipe = Pipeline(
        steps = [
            ('imputer', SimpleImputer(strategy = categorical_strategy)),
            (
                'onehot',
                OneHotEncoder(
                    handle_unknown = 'ignore',
                    sparse_output = False,
                    max_categories = max_categories,
                )
            )
        ]
    )
    return ColumnTransformer(
        transformers = [
            ('num', numeric_pipe, num_cols),
            ('cat', categorical_pipe, cat_cols)
        ],
        remainder = 'drop',
        verbose_feature_names_out = False
    )

def run_feature_engineering_v2(path: Optional[str] = None, save: bool = True):
    setup_logging()
    df = load_raw_geo(path)
    X, y, feature_cols, years = prepare_features_v2(df)
    X_train, X_test, y_train, y_test = temporal_split(X, y, years)
    meta = {
        'feature_columns': feature_cols,
        'n_train': len(X_train),
        'n_test': len(X_test),
        'train_years': list(train_year),
        'test_year': test_year,
        'target': target_col,
        'always_drop_v2': sorted(always_drop_v2),
        'forbidden_cols': sorted(forbidden_cols),
        'max_categories': max_categories_v2
    }
    if save:
        train_out = X_train.copy()
        train_out[target_col] = y_train.values
        test_out = X_test.copy()
        test_out[target_col] = y_test.values
        for c in train_out.select_dtypes(include = ['category']).columns:
            train_out[c] = train_out[c].astype('string')
            test_out[c] = test_out[c].astype('string')
        train_out.to_csv(train_path_v2, index = False)
        test_out.to_csv(test_path_v2, index = False)
        save_json(meta, feature_meta_path_v2)
        logger.info('Saved train -> %s', train_path_v2)
        logger.info('Saved test -> %s', test_path_v2)
        logger.info('Saved meta -> %s', feature_meta_path_v2)
    return {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'feature_columns': feature_cols,
        'meta': meta
    }


if __name__ == '__main__':
    out = run_feature_engineering_v2()
