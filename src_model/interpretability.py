from __future__ import annotations
import logging
import os
from typing import Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src_model.config import figures_dir

logger = logging.getLogger(__name__)

def _save_fig(fig, name: str):
    path = os.path.join(figures_dir, name if name.endswith('.png') else f'{name}.png')
    fig.savefig(path, dpi = 150, bbox_inches = 'tight')
    plt.close(fig)
    logger.info('Saved figure -> %s', path)
    return path

def extract_feature_importance(model: Any, top_n: int = 30):
    """
    Tree feature_importances_ or linear coef_ from a sklearn Pipeline.
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
            pd.DataFrame({'feature': feature_names, 'importance': imp}).sort_values(
                'importance', ascending = False
            ).head(top_n).reset_index(drop = True)
        )
    if hasattr(est, 'coef_'):
        coef = np.ravel(est.coef_).astype(float)
        if feature_names is None or len(feature_names) != len(coef):
            feature_names = [f'f{i}' for i in range(len(coef))]
        return (
            pd.DataFrame({'feature': feature_names, 'coefficient': coef}).assign(
                importance = lambda d: d['coefficient'].abs()).sort_values(
                'importance', ascending = False
            ).head(top_n).reset_index(drop = True)
        )
    logger.info('No importances/coefficients available.')
    return None

def plot_feature_importance(importance_df: pd.DataFrame, top_n: int = 20, title: str | None = None, name: str = 'model_feature_importance.png'):
    d = importance_df.head(top_n).copy()
    value_col = 'importance' if 'importance' in d.columns else 'coefficient'
    if value_col == 'coefficient':
        d['importance'] = d['coefficient'].abs()
        value_col = 'importance'
    fig, ax = plt.subplots(figsize = (10, 7))
    sns.barplot(data = d, y = 'feature', x = value_col, orient = 'h', ax = ax, color = 'darkorange')
    if title is None:
        ax.set_title('Feature importance')
    else:
        ax.set_title(title)
    ax.set_xlabel(value_col)
    ax.set_ylabel('')
    fig.tight_layout()
    return _save_fig(fig, name)

def run_interpretability(model: Any, top_n: int = 20, model_label: str = 'model'):
    """
    Extract FI table + save standard plot.
    """
    fi = extract_feature_importance(model, top_n = max(top_n, 30))
    out = {'importance_table': fi, 'figure_path': None}
    if fi is not None and len(fi):
        out['figure_path'] = plot_feature_importance(fi, top_n = top_n,
                                                     title = f'{model_label}: feature importance',
                                                     name = 'model_feature_importance.png'
                                                     )
    return out
