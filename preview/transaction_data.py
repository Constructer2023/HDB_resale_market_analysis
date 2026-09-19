import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, '..', 'data', 'raw', 'Resale_Flat_Prices_based_on_Registration_Date_from_Jan2017_onwards.csv')
df = pd.read_csv(data_path, header = 0)

print(f'df.shape: {df.shape}')
print(f'df preview: {df.head()}')
print(f'df infos: {df.info()}')

print(df.describe(include = 'all'))

print(f'Total NA values count: {df.isna().sum()}')
print(f'Duplicate records count: {df.duplicated().sum()}')

for col in df.columns:
    print(f'\n===== {col} =====')
    print(f'The unique values in this column: {df[col].nunique()}')
    print(f'The 10 most frequent values occur: {df[col].value_counts().head(10)}')
