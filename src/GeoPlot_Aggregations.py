from __future__ import annotations
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, '..', 'figures')

def _save(fig, name: str, path: str = output_path, dpi: int = 150):
    if path is None:
        path = output_path + '\\' + f'{name}.png'
    else:
        path = path + '\\' + f'{name}.png'
    fig.savefig(path, dpi = dpi, bbox_inches = 'tight')
    plt.close(fig)
    print(f'Saved: {path}')
    return path

def plot_pps_by_mrt_band(band_df: pd.DataFrame, name = 'pps_by_mrt_band', subfolder = None):
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.barplot(data = band_df, x = 'mrt_band', y = 'median_pps', ax = ax, color = 'steelblue')
    ax.set_title('Median Price per sqm by Distance to Nearest MRT/LRT')
    ax.set_xlabel('Distance to MRT')
    ax.set_ylabel('Median PPS (SGD)')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_price_by_mrt_band(band_df: pd.DataFrame, name = 'price_by_mrt_band', subfolder = None):
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.barplot(data = band_df, x = 'mrt_band', y = 'median_price', ax = ax, color = 'darkorange')
    ax.set_title('Median Resale Price by Distance to Nearest MRT/LRT')
    ax.set_xlabel('Distance to MRT')
    ax.set_ylabel('Median Price (SGD)')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_to_mrt_vs_pps_scatter(df: pd.DataFrame, sample_n: int = 8000, name = 'scatter_to_mrt_vs_pps', subfolder = None):
    d = df.dropna(subset = ['to_mrt', 'price_per_sqm']).copy()
    if len(d) > sample_n:
        d = d.sample(sample_n, random_state = 2026)
    fig, ax = plt.subplots(figsize = (8, 5))
    ax.scatter(d['to_mrt'], d['price_per_sqm'], alpha = 0.15, s = 8)
    ax.set_title('Price per sqm vs Distance to MRT')
    ax.set_xlabel('to_mrt (metres)')
    ax.set_ylabel('price_per_sqm (SGD)')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_top_stations_by_volume(station_df: pd.DataFrame, top_n: int = 15, name = 'top_stations_by_volume', subfolder = None):
    d = station_df.head(top_n)
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = d, y = 'nearest_mrt', x = 'transactions', orient = 'h', ax = ax, color = 'teal')
    ax.set_title(f'Top {top_n} Nearest-MRT Stations by Transaction Volume')
    ax.set_xlabel('Transactions')
    ax.set_ylabel('')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_top_stations_by_pps(station_df: pd.DataFrame, top_n: int = 15, name = 'top_stations_by_pps', subfolder = None):
    d = station_df.sort_values('median_pps', ascending = False).head(top_n)
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = d, y = 'nearest_mrt', x = 'median_pps', orient = 'h', ax = ax, color = 'slateblue')
    ax.set_title(f'Top {top_n} Stations by Median PPS')
    ax.set_xlabel('Median PPS (SGD)')
    ax.set_ylabel('')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_pps_by_city_band(band_df: pd.DataFrame, name = 'pps_by_city_band', subfolder = None):
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.barplot(data = band_df, x = 'city_band', y = 'median_pps', ax = ax, color = 'crimson')
    ax.set_title('Median Price per sqm by Distance to City Centre (Raffles Place)')
    ax.set_xlabel('Distance to city')
    ax.set_ylabel('Median PPS (SGD)')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_to_city_vs_pps_scatter(df: pd.DataFrame, sample_n: int = 8000, name = 'scatter_to_city_vs_pps', subfolder = None):
    d = df.dropna(subset = ['to_city', 'price_per_sqm']).copy()
    if len(d) > sample_n:
        d = d.sample(sample_n, random_state = 2026)
    fig, ax = plt.subplots(figsize = (8, 5))
    ax.scatter(d['to_city'] / 1000.0, d['price_per_sqm'], alpha = 0.15, s = 8, color = 'crimson')
    ax.set_title('Price per sqm vs Distance to City Centre')
    ax.set_xlabel('to_city (km)')
    ax.set_ylabel('price_per_sqm (SGD)')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_top_subzones_by_pps(zone_df: pd.DataFrame, top_n: int = 15, name = 'top_subzones_by_pps', subfolder = None):
    d = zone_df.head(top_n)
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = d, y = 'subzone', x = 'median_pps', orient = 'h', ax = ax, color = 'seagreen')
    ax.set_title(f'Top {top_n} Subzones by Median PPS')
    ax.set_xlabel('Median PPS (SGD)')
    ax.set_ylabel('')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_bottom_subzones_by_pps(zone_df: pd.DataFrame, top_n: int = 15, name = 'bottom_subzones_by_pps', subfolder = None):
    d = zone_df.sort_values('median_pps', ascending = True).head(top_n)
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = d, y = 'subzone', x = 'median_pps', orient = 'h', ax = ax, color = 'gray')
    ax.set_title(f'Lowest {top_n} Subzones by Median PPS')
    ax.set_xlabel('Median PPS (SGD)')
    ax.set_ylabel('')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_joint_mrt_city_heatmap(joint_df: pd.DataFrame, value_col: str = 'mean_pps', name = 'heatmap_mrt_city_pps', subfolder = None):
    pivot = joint_df.pivot(index = 'city_band', columns = 'mrt_band', values = value_col)
    fig, ax = plt.subplots(figsize = (10, 5))
    sns.heatmap(pivot, annot = True, fmt = '.2f', cmap = 'YlOrRd', ax = ax)
    ax.set_title('Mean PPS by City Band × MRT Band')
    ax.set_xlabel('MRT band')
    ax.set_ylabel('City band')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_boxplot_pps_by_mrt_band(df: pd.DataFrame, sample_n: int = 20000, name = 'boxplot_pps_by_mrt_band', subfolder = None):
    from src.GeoAnalysis_Aggregations import add_geo_bands
    d = add_geo_bands(df).dropna(subset = ['mrt_band', 'price_per_sqm'])
    if len(d) > sample_n:
        d = d.sample(sample_n, random_state = 2026)
    fig, ax = plt.subplots(figsize = (10, 5))
    sns.boxplot(data = d, x = 'mrt_band', y = 'price_per_sqm', ax = ax)
    ax.set_title('PPS Distribution by MRT Distance Band')
    ax.set_xlabel('Distance to MRT')
    ax.set_ylabel('price_per_sqm')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save(fig, name, subfolder)
