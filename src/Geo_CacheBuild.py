from __future__ import annotations
import os
import time
import json
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from src.Geo_OneMapClient import OneMapClient
from src.Geo_Distances import haversine_m, nearest_mrt, distance_to_city

script_dir = os.path.dirname(os.path.abspath(__file__))
raw_path = os.path.join(script_dir, '..', 'data', 'raw')
processed_path = os.path.join(script_dir, '..', 'data', 'processed')
aid_path = os.path.join(script_dir, '..', 'data', 'aid')

def build_unique_addresses(trx_data: str):
    """
    extract distinct (blk, st). No town in the key.
    """
    df = pd.read_csv(trx_data)
    u = (
        df[['block', 'street_name']].dropna().astype(str).drop_duplicates().reset_index(drop = True)
    ).rename(columns = {'block': 'blk', 'street_name': 'st'})
    u['search_val'] = u['blk'] + ' ' + u['st']
    out = aid_path + '\\' + 'unique_hdb_addresses.csv'
    u.to_csv(out, index = False)
    print(f'Unique addresses: {len(u)} -> {out}')
    return u

def build_zone_name_to_id(client: OneMapClient, year: int = 2019):
    rows = client.get_names_of_planning_areas(year = year)
    mapping = {}
    for r in rows:
        name = r.get('pln_area_n')
        zid = r.get('id')
        if name is not None and zid is not None:
            mapping[str(name).strip().upper()] = int(zid)
    print(f'Planning area name -> id map: {len(mapping)} entries')
    return mapping

def build_planning_polygons(client: OneMapClient, year: int = 2019):
    """
    get_all_planning_area -> [{'pln_area_n': str, 'geojson': dict | str}, ...]
    return [{subzone, geometry}, ...]
    """
    raw = client.get_all_planning_areas(year = year)
    polys = []
    for item in raw:
        name = item.get('pln_area_n')
        gj = item.get('geojson')
        if name is None or gj is None:
            continue
        if isinstance(gj, str):
            gj = json.loads(gj)
        geom = shape(gj)
        polys.append({'subzone': str(name).strip(), 'geometry': geom})
    print(f'Planning polygons loaded: {len(polys)}')
    return polys

def lookup_subzone(lat: float, lon: float, polys: list[dict]):
    pt = Point(lon, lat)
    for p in polys:
        if p['geometry'].contains(pt):
            return p['subzone']
    return None

def build_geocode_cache(client: OneMapClient, year: int = 2019, sleep_s: float = 0.1):
    """
    one-time geocode + planning area id/name.
    save data/aid/hdb_geocode_cache.csv
    """
    unique = pd.read_csv(aid_path + '\\' + 'unique_hdb_addresses.csv')
    name_to_id = build_zone_name_to_id(client, year = year)
    polys = build_planning_polygons(client, year = year)
    rows = []
    n = len(unique)
    for i, item in unique.iterrows():
        blk, st, q = item['blk'], item['st'], item['search_val']
        row = {
            'blk': blk,
            'st': st,
            'search_val': q,
            'lat': None,
            'lon': None,
            'postal': None,
            'subzone': None,
            'zone_id': None,
            'nearest_mrt': None,
            'mrt_lat': None,
            'mrt_lon': None,
            'to_mrt': None,
            'to_city': None,
            'status': 'ok'
        }
        try:
            res = client.search(q)
            results = res.get('results') or []
            if not results:
                row['status'] = 'not_found'
                res.append(row)
                continue
            hit = results[0]
            lat = float(hit['LATITUDE'])
            lon = float(hit['LONGITUDE'])
            row['lat'] = lat
            row['lon'] = lon
            row['postal'] = hit['POSTAL']
            subzone = lookup_subzone(lat, lon, polys)
            row['subzone'] = subzone
            if subzone:
                row['zone_id'] = name_to_id.get(subzone.upper())
            row['to_city'] = float(distance_to_city(lat, lon))
        except Exception as e:
            row['status'] = f'error: {type(e).__name__}: {e}'
        rows.append(row)
        if sleep_s:
            time.sleep(sleep_s)
        if (i + 1) % 50 == 0 or (i + 1) == n:
            print(f'Geocoded {i + 1}/{n}')
            path = f'{aid_path}\\hdb_geocode_cache_partial_{i + 1}.csv'
            pd.DataFrame(rows).to_csv(path, index = False)
    cache = pd.DataFrame(rows)
    out = f'{aid_path}\\hdb_geocode_cache.csv'
    cache.to_csv(out, index = False)
    print(f'Cache saved -> {out}')
    print(cache['status'].value_counts().to_dict())
    return cache

def build_mrt_from_exit_geojson(geojson_path = None, out_path = None, mode = 'exit'):
    if geojson_path is None:
        geojson_path = f'{raw_path}\\LTAMRTStationExitGEOJSON.geojson'
    if out_path is None:
        out_path = f'{aid_path}\\mrt_stations_cleaned.csv'
    with open(geojson_path, 'r', encoding = 'utf-8') as f:
        gj = json.load(f)
    rows = []
    for item in gj.get('features'):
        props = item.get('properties')
        geom = item.get('geometry') or {}
        coords = geom.get('coordinates')
        lon, lat = float(coords[0]), float(coords[1])
        name = props.get('STATION_NA')
        rows.append({
            'name': name,
            'lat': lat,
            'lon': lon,
            'exit_code': props.get('EXIT_CODE'),
            'objectid': props.get('OBJECTID')
        })
    df = pd.DataFrame(rows).dropna(subset = ['name', 'lat', 'lon'])
    if mode == 'station':
        df = (
            df.groupby(
                'name', as_index = False
            ).agg(
                lat = ('lat', 'mean'), lon=('lon', 'mean')
            )
        )
    else:
        pass
    out_df = df[['name', 'lat', 'lon']].drop_duplicates().reset_index(drop = True)
    out_df.to_csv(out_path, index = False)
    print(f'MRT points: {len(out_df)} -> {out_path}')
    print(f'Unique stations: {out_df['name'].nunique()}')
    return out_df

def attach_mrt_to_cache(cache_path = None, mrt_path = None):
    if cache_path is None:
        cache_path = f'{aid_path}\\hdb_geocode_cache.csv'
    if mrt_path is None:
        mrt_path = f'{aid_path}\\mrt_stations_cleaned.csv'
    cache = pd.read_csv(cache_path)
    mrt = pd.read_csv(mrt_path)
    cache['nearest_mrt'] = None
    cache['mrt_lat'] = np.nan
    cache['mrt_lon'] = np.nan
    cache['to_mrt'] = np.nan
    ok = cache['lat'].notna() & cache['lon'].notna()
    if not ok.any():
        cache.to_csv(cache_path, index = False)
        print('No valid lat/lon in cache')
        return cache
    lat_arr = cache.loc[ok, 'lat'].to_numpy(dtype = float)
    lon_arr = cache.loc[ok, 'lon'].to_numpy(dtype = float)
    dists, names = nearest_mrt(lat_arr, lon_arr, mrt)
    mrt_lat = mrt['lat'].to_numpy(dtype = float)
    mrt_lon = mrt['lon'].to_numpy(dtype = float)
    mrt_name = mrt['name'].to_numpy()
    d_matrix = haversine_m(
        lat_arr[:, None], lon_arr[:, None],
        mrt_lat[None, :], mrt_lon[None, :]
    )
    idx = np.nanargmin(d_matrix, axis = 1)
    cache.loc[ok, 'to_mrt'] = d_matrix[np.arange(len(lat_arr)), idx]
    cache.loc[ok, 'nearest_mrt'] = mrt_name[idx]
    cache.loc[ok, 'mrt_lat'] = mrt_lat[idx]
    cache.loc[ok, 'mrt_lon'] = mrt_lon[idx]
    cache.to_csv(cache_path, index = False)
    print(f'Attached MRT columns -> {cache_path}')
    print(cache[['to_mrt', 'to_city']].describe())
    return cache
