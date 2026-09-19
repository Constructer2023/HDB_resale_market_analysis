import pandas as pd
import os

def load_transactions(path: str | None = None):
    # Keep manual path selection
    if path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(script_dir, '..', 'data', 'processed', 'resale_transactions.csv')
    else:
        data_path = path

    df = pd.read_csv(data_path, header = 0)

    if 'trx_date' in df.columns:
        df['trx_date'] = pd.to_datetime(df['trx_date'])

    for col in ['trx_year', 'trx_month', 'lease_commence', 'flat_year', 'remaining_lease_month',
                'storey_lower', 'storey_midpoint', 'storey_upper']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors = 'coerce') # Invalid columns set to NaN

    for col in ['resale_price', 'price_per_sqm', 'floor_area_sqm']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors = 'coerce')

    return df


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '..', 'data', 'processed', 'resale_transactions.csv')
    df = load_transactions(data_path)
    print(df.info())
