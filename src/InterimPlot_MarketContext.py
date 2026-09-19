from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, '..', 'figures')

def _save(fig, name: str, path: str | None = output_path, dpi: int = 150):
    if path is None:
        path = output_path + '\\' + f'{name}.png'
    else:
        path = path + '\\' + f'{name}.png'
    fig.savefig(path, dpi = dpi, bbox_inches = 'tight')
    plt.close(fig)
    print(f'Saved: {path}')
    return path

def plot_rpi_trend(rpi: pd.DataFrame, name = 'rpi_trend', subfolder = None):
    fig, ax = plt.subplots(figsize = (11, 5))
    ax.plot(rpi['quarter_start'], rpi['rpi'], marker = 'o', markersize = 3)
    ax.set_title('HDB Resale Price Index (Official)')
    ax.set_xlabel('Quarters(Year display in x axis)')
    ax.set_ylabel('Index')
    ax.grid(True, alpha = 0.3)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_trx_median_vs_rpi(cmp: pd.DataFrame, name = 'medianprice_vs_rpi', subfolder = None):
    """
    cmp = compare_trx_vs_rpi(...)
    """
    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax2 = ax1.twinx()
    ax1.plot(cmp['quarter_start'], cmp['median_price'],
             color = 'tab:blue', marker = 'o', label = 'Trx Median Price')
    ax2.plot(cmp['quarter_start'], cmp['rpi'],
             color = 'tab:red', marker = 's', label = 'Official RPI')
    ax1.set_xlabel('Quarters(Year display in x axis)')
    ax1.set_ylabel('Median Resale Price (SGD)', color = 'tab:blue')
    ax2.set_ylabel('Resale Price Index', color = 'tab:red')
    ax1.set_title('Actual Transaction Median Price vs Official Resale Price Index')
    ax1.grid(False)
    ax2.grid(False)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc = 'upper left')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_volume_vs_applications(cmp: pd.DataFrame, name = 'actualvolume_vs_applications', subfolder = None):
    """
    cmp = compare_volume_vs_applications(...)
    """
    fig, ax1 = plt.subplots(figsize = (11, 5))
    ax2 = ax1.twinx()
    ax1.bar(cmp['quarter_start'], cmp['volume'],
            width = 60, alpha = 0.6, label = 'Actual Transactions')
    ax2.plot(cmp['quarter_start'], cmp['num'],
             color = 'tab:red', marker = 'o', label = 'Resale Applications')
    ax1.set_ylabel('Actual Transactions')
    lim = ax2.get_ylim()
    ax1.set_ylim(lim)
    ax2.set_ylabel('Resale Applications')
    ax1.set_title('Quarterly Transaction Volume vs Resale Applications')
    ax1.grid(False)
    ax2.grid(False)
    fig.legend(loc = 'upper left', bbox_to_anchor = (0.1, 0.9))
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_conversion_rate(cmp: pd.DataFrame, name = 'conversion_rate', subfolder = None):
    fig, ax = plt.subplots(figsize = (11, 4))
    cmp = cmp[(cmp['conversion_pct'] >= 0) & (cmp['conversion_pct'] <= 1000)].copy()
    ax.plot(cmp['quarter_start'], cmp['conversion_pct'], marker = 'o')
    ax.set_title('Conversion Rate: Actual Transactions / Applications (%)')
    ax.set_ylabel('Conversion %')
    ax.grid(True, alpha = 0.3)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_pps_by_flat_type(pps: pd.DataFrame, year_from = 2020, name = 'pps_by_flat_type_2020onwards', subfolder = None):
    """
    pps = quarterly_pps_by_flat_type(...)
    """
    data = pps[pps['quarter_start'].dt.year >= year_from].copy()
    fig, ax = plt.subplots(figsize = (12, 6))
    for ft, g in data.groupby("flat_type"):
        ax.plot(g['quarter_start'], g['mean_pps'], marker = 'o', markersize = 3, label = ft)
    ax.set_title(f'Mean Price per sqm by Flat Type (from {year_from})')
    ax.set_ylabel('Mean PPS (SGD)')
    ax.legend(bbox_to_anchor = (1.02, 1), loc = 'upper left')
    ax.grid(True, alpha = 0.3)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_actual_vs_official_scatter(cmp: pd.DataFrame, name = 'actualscatter_vs_officialscatter', subfolder = None):
    """
    cmp = actual_vs_official_median(...)
    """
    fig, ax = plt.subplots(figsize = (7, 7))
    ax.scatter(cmp['median_resale_price'], cmp['actual_median_price'], alpha = 0.4, s = 20)
    max_val = max(cmp['median_resale_price'].max(), cmp['actual_median_price'].max())
    ax.plot([0, max_val], [0, max_val], "r--", label = 'y = x')
    ax.set_xlabel('Official Median Price')
    ax.set_ylabel('Actual Transaction Median Price')
    ax.set_title('Actual vs Official Median Price\n(by Town × Flat Type × Quarter)')
    ax.legend()
    ax.grid(True, alpha = 0.3)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_diff_by_flat_type(cmp: pd.DataFrame, name = 'diff_by_flat_type', subfolder = None):
    g = (
        cmp.groupby('flat_type', as_index = False).agg(
            avg_diff = ('diff', 'mean'), avg_diff_pct = ('diff_pct', 'mean')
        ).sort_values('avg_diff')
    )
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.barplot(data = g, x = 'flat_type', y = 'avg_diff', ax = ax)
    ax.axhline(0, color = 'black', lw = 1)
    ax.set_title('Average Difference: Actual Median − Official Median')
    ax.set_ylabel('Difference (SGD)')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_annual_applications(annual: pd.DataFrame, name = 'annual_applications_2017_2025', subfolder = None):
    fig, ax = plt.subplots(figsize = (9, 5))
    ax.bar(annual['trx_year'], annual['total_applications'], color = 'steelblue', width = 0.4)
    ax.set_title('Annual Resale Applications')
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Applications')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_annual_applications_by_type(by_type: pd.DataFrame, name = 'annual_applications_by_flat_type', subfolder = None):
    pivot = by_type.pivot(index = 'trx_year', columns = 'flat_type', values = 'applications')
    fig, ax = plt.subplots(figsize = (11, 6))
    pivot.plot(kind = 'bar', stacked = True, ax = ax)
    ax.set_title('Annual Resale Applications by Flat Type')
    ax.set_xlabel('Year')
    ax.set_ylabel('Applications')
    ax.legend(title = 'Flat Type', bbox_to_anchor = (1.02, 1), loc = 'upper left')
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_applications_resale_vs_rental(reg: pd.DataFrame, name = 'resale_vs_rental_applications', subfolder = None):
    """
    reg = load_applications_registered()
    """
    pivot = reg.pivot(index = 'year', columns = 'type', values = 'num')
    fig, ax = plt.subplots(figsize = (10, 5))
    pivot.plot(ax = ax, marker = 'o')
    ax.set_title('Applications Registered: Resale vs Rental')
    ax.set_ylabel('Applications')
    ax.grid(True, alpha = 0.3)
    fig.tight_layout()
    return _save(fig, name, subfolder)

def plot_latest_official_median_by_town(official: pd.DataFrame, top_n = 15, name = 'latest_median_price_by_town', subfolder = None):
    latest = official['trx_date'].max()
    data = (
        official[official['trx_date'] == latest].dropna(
            subset = ['median_resale_price']
        ).groupby(
            'town', as_index = False)['median_resale_price'].mean().sort_values(
            'median_resale_price', ascending = False
        ).head(top_n)
    )
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = data, y = 'town', x = 'median_resale_price', orient = 'h', ax = ax)
    ax.set_title(f'Official Median Price by Town (latest quarter: {latest})')
    ax.set_xlabel('Average Median Price (SGD)')
    fig.tight_layout()
    return _save(fig, name, subfolder)
