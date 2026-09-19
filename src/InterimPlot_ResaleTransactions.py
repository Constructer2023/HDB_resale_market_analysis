from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, '..', 'figures')

def _save(fig, name: str, path: str | None = output_path, dpi: int = 150):
    if path is None:
        path = output_path + '\\' +  f'{name}.png'
    else:
        path = path + '\\' + f'{name}.png'
    fig.savefig(path, dpi = dpi, bbox_inches = 'tight')
    print(f'Saved: {path}')
    plt.close(fig)
    return path

def plot_yearly_volume_price(yearly_df: pd.DataFrame, name = 'yearly_volume_price', path: str | None = None):
    fig, ax1 = plt.subplots(figsize = (10, 5))
    ax2 = ax1.twinx()
    ax1.bar(yearly_df['trx_year'], yearly_df['transactions'],
            alpha = 0.6, label = 'Transactions')
    ax2.plot(yearly_df['trx_year'], yearly_df['median_price'],
             color = 'tab:red', marker = 'o', label = 'Median Price')
    for i in range(len(yearly_df['trx_year'])):
        ax1.text(x = yearly_df['trx_year'][i], y = yearly_df['transactions'][i] + 100,
                 s = yearly_df['transactions'][i], fontsize = 10, ha = 'center', va = 'bottom')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of Transactions')
    ax2.set_ylabel('Median Resale Price (SGD)')
    ax1.set_title('Transaction Volume & Median Price by Year')
    fig.legend(loc = 'upper left', bbox_to_anchor = (0.1, 0.9))
    ax1.grid(False)
    ax2.grid(False)
    fig.tight_layout()
    return _save(fig, name, path)

def plot_monthly_volume_price(monthly_df: pd.DataFrame, name = 'monthly_volume_price', path: str | None = None):
    fig, ax1 = plt.subplots(figsize = (10, 5))
    ax2 = ax1.twinx()
    x_list = []
    t = []
    for i in range(len(monthly_df)):
        x_list.append(str(monthly_df['trx_year'][i]) + '.' + str(monthly_df['trx_month'][i]).rjust(2, '0'))
    x = pd.Series(x_list)
    ax1.bar(x, monthly_df['transactions'], alpha = 0.6, label = 'Transactions')
    ax2.plot(x, monthly_df['median_price'], color = 'tab:red', marker = 'o', label = 'Median Price')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Number of Transactions')
    ax2.set_ylabel('Median Resale Price (SGD)')
    ax1.set_title('Transaction Volume & Median Price by Month')
    fig.legend(loc = 'upper left', bbox_to_anchor = (0.1, 0.9))
    for i in range(len(monthly_df)):
        if i % 12 == 0:
            t.append(True)
        else:
            t.append(False)
    plt.xticks(x[t], x[t], rotation = 45, fontsize = 5)
    ax1.grid(False)
    ax2.grid(False)
    fig.tight_layout()
    return _save(fig, name, path)

def plot_town_ranking(town_df: pd.DataFrame, top_n = 15, by: bool = True, by_col = 'median_price',
                      name = 'town_median_price', path: str | None = None):
    if by:
        data = town_df.head(top_n)
    else:
        data = town_df.tail(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize = (10, 6))
    sns.barplot(data = data, y = 'town', x = by_col, ax = ax, orient = 'h')
    ax.set_title(f'Top {top_n} Towns by {by_col.replace('_', ' ').title()}')
    ax.set_xlabel(by_col.replace('_', ' ').title())
    fig.tight_layout()
    return _save(fig, name, path)

def plot_price_distribution(df: pd.DataFrame, name = 'price_distribution', path: str | None = None):
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.histplot(df['resale_price'], bins = 50, kde = True, ax = ax)
    ax.axvline(df['resale_price'].median(), color = 'red', linestyle = '--', label = 'Median')
    ax.set_title('Resale Price Distribution')
    ax.set_xlabel('Resale Price (SGD)')
    ax.legend()
    fig.tight_layout()
    return _save(fig, name, path)

def plot_band_vs_price(df: pd.DataFrame, band_col: str, value_col = 'price_per_sqm',
                       path: str | None = None, name = None):
    name = name if name is not None else f'{value_col}_vs_{band_col}'
    order = df.groupby(band_col, observed = True)[value_col].median().sort_index().index
    fig, ax = plt.subplots(figsize = (9, 5))
    sns.boxplot(data = df, x = band_col, y = value_col, order = order, ax = ax, width = 0.4)
    ax.set_title(f'{value_col.replace('_', ' ').title()} by {band_col.replace('_', ' ').title()}')
    ax.tick_params(axis = 'x', rotation = 30)
    fig.tight_layout()
    return _save(fig, name, path)
