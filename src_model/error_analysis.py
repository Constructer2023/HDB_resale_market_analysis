from __future__ import annotations
import logging
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from src_model.config import (
    figures_dir,
    prediction_v1_path,
    prediction_v2_path
)

logger = logging.getLogger(__name__)

def _save_fig(fig, name: str, subdir: str | None = None) -> str:
    base = figures_dir if subdir is None else os.path.join(figures_dir, subdir)
    path = os.path.join(base, name if name.endswith('.png') else f'{name}.png')
    fig.savefig(path, dpi = 150, bbox_inches = 'tight')
    plt.close(fig)
    logger.info('Saved figure -> %s', path)
    return path

def build_prediction_frame(X_test: pd.DataFrame, y_test: pd.Series, y_pred: np.ndarray | pd.Series, version: str = 'v2'):
    """
    Actual, predicted, residual, abs error (+ optional keys from X_test).
    """
    out = X_test.copy()
    out['actual'] = np.asarray(y_test, dtype = float)
    out['predicted'] = np.asarray(y_pred, dtype = float)
    out['residual'] = out['actual'] - out['predicted']
    out['abs_error'] = out['residual'].abs()
    out['pct_error'] = np.where(
        out['actual'] != 0,
        100.0 * out['residual'] / out['actual'],
        np.nan,
    )
    out['version'] = version
    return out

def save_prediction_test(pred_df: pd.DataFrame, version: str = 'v2', path: str | None = None):
    if path is None:
        path = prediction_v2_path if version == 'v2' else prediction_v1_path
    pred_df.to_csv(path, index = False)
    logger.info('Saved predictions -> %s', path)
    return path

def load_prediction_test(version: str = 'v2', path: str | None = None):
    if path is None:
        path = prediction_v2_path if version == 'v2' else prediction_v1_path
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return pd.read_csv(path, low_memory = False)

def add_price_band(df: pd.DataFrame, price_col: str = 'actual'):
    out = df.copy()
    out['price_band'] = pd.cut(
        out[price_col],
        bins = [-np.inf, 300000, 500000, 700000, 900000, 1200000, np.inf],
        labels = ['<300k', '300-500k', '500-700k', '700-900k', '900k-1.2M', '1.2M+']
    )
    return out

def error_summary(pred_df: pd.DataFrame):
    return {
        'n': int(len(pred_df)),
        'rmse': float(np.sqrt(np.mean(pred_df['residual'] ** 2))),
        'mae': float(pred_df['abs_error'].mean()),
        'median_ae': float(pred_df['abs_error'].median()),
        'mean_residual': float(pred_df['residual'].mean()),
        'median_residual': float(pred_df['residual'].median())
    }

def error_by_group(pred_df: pd.DataFrame, group_col: str, min_n: int = 20):
    if group_col not in pred_df.columns:
        raise KeyError(f'Missing column: {group_col}')
    g = (
        pred_df.groupby(group_col, observed = True).agg(
            n = ('abs_error', 'size'),
            mae = ('abs_error', 'mean'),
            median_ae = ('abs_error', 'median'),
            rmse = ('residual', lambda s: float(np.sqrt(np.mean(np.square(s))))),
            mean_residual = ('residual', 'mean')
        ).reset_index()
    )
    return g[g['n'] >= min_n].sort_values('mae', ascending = False)

def plot_actual_vs_predicted(pred_df: pd.DataFrame, title: str | None = None, name: str = 'model_actual_vs_predicted.png'):
    fig, ax = plt.subplots(figsize = (7, 7))
    ax.scatter(pred_df['actual'], pred_df['predicted'], alpha = 0.12, s = 8)
    mn = min(pred_df['actual'].min(), pred_df['predicted'].min())
    mx = max(pred_df['actual'].max(), pred_df['predicted'].max())
    ax.plot([mn, mx], [mn, mx], 'r--', lw = 1)
    ax.set_xlabel('Actual resale_price')
    ax.set_ylabel('Predicted')
    if title == None:
        ax.set_title('Actual vs Predicted')
    else:
        ax.set_title(title)
    fig.tight_layout()
    return _save_fig(fig, name)

def plot_residual_distribution(pred_df: pd.DataFrame, title: str | None = None,
                               name: str = 'model_residual_distribution.png'):
    fig, ax = plt.subplots(figsize = (8, 5))
    ax.hist(pred_df['residual'], bins = 60, color = 'steelblue', edgecolor = 'white')
    ax.axvline(0, color = 'red', ls = '--')
    ax.set_xlabel('Residual (actual - predicted)')
    if title == None:
        ax.set_title('Residual distribution')
    else:
        ax.set_title(title)
    fig.tight_layout()
    return _save_fig(fig, name)

def plot_error_by_category(pred_df: pd.DataFrame, group_col: str, top_n: int = 15,
                           title: str | None = None, name: str = 'model_error_by_',
                           min_n: int = 20):
    g = error_by_group(pred_df, group_col, min_n = min_n).head(top_n)
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = g, y = group_col, x = 'mae', orient = 'h', ax = ax, color = 'salmon')
    ax.set_xlabel('MAE')
    ax.set_ylabel('')
    if title == None:
        ax.set_title(f'MAE by {group_col}')
    else:
        ax.set_title(title)
    fig.tight_layout()
    name = f'{name}{group_col}.png'
    return _save_fig(fig, name)

def plot_error_by_town(pred_df: pd.DataFrame, min_n: int = 30):
    if 'town' in pred_df.columns:
        col = 'town'
    elif 'subzone' in pred_df.columns:
        col = 'subzone'
    else:
        col = None
    if col is None:
        raise KeyError('No \'town\' or \'subzone\' column in prediction frame')
    return plot_error_by_category(pred_df, col, top_n = 20, min_n = min_n)

def plot_error_by_flat_type(pred_df: pd.DataFrame, name: str = 'model_error_by_flat_type.png') -> str:
    if 'flat_type' not in pred_df.columns:
        raise KeyError('No \'flat_type\' column')
    g = error_by_group(pred_df, 'flat_type', min_n = 10)
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.barplot(data = g.sort_values('mae'), x = 'flat_type', y = 'mae', ax = ax, color = 'teal')
    ax.set_title('MAE by flat type')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save_fig(fig, name)

def plot_error_by_price_band(pred_df: pd.DataFrame, name: str = 'model_error_by_price_band.png'):
    d = add_price_band(pred_df)
    g = error_by_group(d, 'price_band', min_n = 50)
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.barplot(data = g, x = 'price_band', y = 'mae', ax = ax, color = 'slateblue')
    ax.set_title('MAE by actual price band')
    ax.tick_params(axis = 'x', rotation = 20)
    fig.tight_layout()
    return _save_fig(fig, name)

def plot_error_over_time(pred_df: pd.DataFrame, time_col: str = 'trx_month', name: str = 'model_error_over_time.png'):
    """
    Prefer trx_month or trx_date; falls back to trx_year.
    For pure 2026 test, monthly grain is most useful if available.
    """
    d = pred_df.copy()
    if time_col not in d.columns:
        if 'trx_date' in d.columns:
            d['_t'] = pd.to_datetime(d['trx_date'], errors = 'coerce')
            time_col = '_t'
        elif 'trx_year' in d.columns:
            time_col = 'trx_year'
        else:
            raise KeyError('No time column for plot_error_over_time')
    g = (
        d.groupby(time_col, observed = True).agg(
            n = ('abs_error', 'size'),
            mae = ('abs_error', 'mean'),
            mean_residual = ('residual', 'mean'),
        ).reset_index().sort_values(time_col)
    )
    fig, ax = plt.subplots(figsize = (11, 5))
    ax.plot(g[time_col].astype(str), g['mae'], marker = 'o', label = 'MAE')
    ax.plot(g[time_col].astype(str), g['mean_residual'], marker = 's', label = 'Mean residual')
    ax.axhline(0, color = 'gray', ls= '--', lw = 1)
    ax.set_title('Error over time (test set)')
    ax.set_xlabel(time_col)
    ax.tick_params(axis = 'x', rotation = 45)
    ax.legend()
    fig.tight_layout()
    return _save_fig(fig, name)

def run_error_analysis_plots(pred_df: pd.DataFrame, model_label: str = 'model'):
    """
    Generate the standard figure set; return paths.
    """
    paths = {}
    paths['actual_vs_pred'] = plot_actual_vs_predicted(pred_df, title = f'{model_label}: actual vs predicted')
    paths['residual_dist'] = plot_residual_distribution(pred_df, title = f'{model_label}: residual distribution')
    paths['error_town'] = plot_error_by_town(pred_df)
    paths['error_flat_type'] = plot_error_by_flat_type(pred_df)
    paths['error_price_band'] = plot_error_by_price_band(pred_df)
    paths['error_time'] = plot_error_over_time(pred_df)
    return paths
