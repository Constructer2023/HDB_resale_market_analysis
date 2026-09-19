from __future__ import annotations
import numpy as np
import pandas as pd

# Raffles Place
CITY_LAT = 1.2840
CITY_LON = 103.8515

def haversine_m(lat1, lon1, lat2, lon2):
    """
    Vectorised haversine distance in metres.
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 6371000 * 2 * np.arcsin(np.sqrt(a))

def distance_to_city(lat, lon):
    return haversine_m(lat, lon, CITY_LAT, CITY_LON)

def nearest_mrt(lat: float | np.ndarray, lon: float | np.ndarray, mrt: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    mrt must have columns: lat, lon, name
    Returns (distances_m, nearest_names)
    """
    mrt_lat = mrt['lat'].to_numpy(dtype = float)
    mrt_lon = mrt['lon'].to_numpy(dtype = float)
    names = mrt['name'].to_numpy()
    lat = np.atleast_1d(np.asarray(lat, dtype = float))
    lon = np.atleast_1d(np.asarray(lon, dtype = float))
    d = haversine_m(lat[:, None], lon[:, None], mrt_lat[None, :], mrt_lon[None, :])
    idx = d.argmin(axis = 1)
    return d[np.arange(len(lat)), idx], names[idx]
