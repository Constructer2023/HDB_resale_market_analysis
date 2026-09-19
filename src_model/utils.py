from __future__ import annotations
import json
import logging
import os
import random
from typing import Any, Optional, Sequence
import joblib
import numpy as np
import torch
from src_model.config import model_dir, random_seed

logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO):
    logging.basicConfig(
        level = level,
        format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
    )

def save_json(obj: Any, path: str):
    path = str(path)
    with open(path, 'w', encoding = 'utf-8') as f:
        json.dump(obj, f, indent = 2, default = str)

def load_json(path: str):
    with open(path, 'r', encoding = 'utf-8') as f:
        return json.load(f)

def save_model(model: Any, name: str, subdir: Optional[str] = None):
    base = os.path.join(model_dir, subdir) if subdir else model_dir
    path = os.path.join(base, f'{name}.joblib')
    joblib.dump(model, path)
    logger.info('Saved model -> %s', path)
    return path

def load_model(name: str, subdir: Optional[str] = None):
    base = os.path.join(model_dir, subdir) if subdir else model_dir
    path = os.path.join(base, f'{name}.joblib')
    if not os.path.exists(path):
        raise FileNotFoundError(f'Model not found: {path}')
    return joblib.load(path)

def list_saved_models_v2():
    if not os.path.isdir(model_dir):
        return []
    names = []
    for f in os.listdir(model_dir):
        if f.endswith('_v2.joblib'):
            names.append(f[:-7])
    return sorted(names)

def force_categorical_v2(df, cols: set | list):
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].astype('string').astype('category')
    return out

def set_seed(seed: int = random_seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

def rmse(y_true: Sequence[float], y_pred: Sequence[float]):
    y_true = np.asarray(y_true, dtype = float)
    y_pred = np.asarray(y_pred, dtype = float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def mae(y_true: Sequence[float], y_pred: Sequence[float]):
    y_true = np.asarray(y_true, dtype = float)
    y_pred = np.asarray(y_pred, dtype = float)
    return float(np.mean(np.abs(y_true - y_pred)))

def mape(y_true: Sequence[float], y_pred: Sequence[float]):
    y_true = np.asarray(y_true, dtype = float)
    y_pred = np.asarray(y_pred, dtype = float)
    mask = y_true != 0
    if not np.any(mask):
        return float('nan')
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

def r2_score(y_true: Sequence[float], y_pred: Sequence[float]):
    y_true = np.asarray(y_true, dtype = float)
    y_pred = np.asarray(y_pred, dtype = float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

def regression_metrics(y_true: Sequence[float], y_pred: Sequence[float]):
    return {
        'rmse': rmse(y_true, y_pred),
        'mae': mae(y_true, y_pred),
        'mape': mape(y_true, y_pred),
        'r2': r2_score(y_true, y_pred),
    }
