import os

this_path = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(this_path, '..', 'data')
aid_data_dir = os.path.join(data_dir, 'aid')
model_based_dir = os.path.join(data_dir, 'model_based')
model_dir = os.path.join(data_dir, '..', 'model')
figures_dir = os.path.join(this_path, '..', 'figures')
report_dir = os.path.join(this_path, '..', 'report')
input_path = f'{aid_data_dir}\\resale_trx_geo.csv'
train_path_v1 = f'{model_based_dir}\\train_v1.csv'
test_path_v1 = f'{model_based_dir}\\test_v1.csv'
feature_meta_path_v1 = f'{model_based_dir}\\feature_meta_v1.json'
comparison_path_v1 = f'{model_based_dir}\\model_comparison_v1.csv'
prediction_v1_path = f'{model_based_dir}\\prediction_v1.csv'
train_path_v2 = f'{model_based_dir}\\train_v2.csv'
test_path_v2 = f'{model_based_dir}\\test_v2.csv'
feature_meta_path_v2 = f'{model_based_dir}\\feature_meta_v2.json'
comparison_path_v2 = f'{model_based_dir}\\model_comparison_v2.csv'
prediction_v2_path = f'{model_based_dir}\\prediction_v2.csv'
model_card_path = f'{report_dir}\\model_card.md'
target_col = 'resale_price'
year_col = 'trx_year'
forbidden_cols = {'resale_price', 'price_per_sqm'}
always_drop_v1 = {
    'blk', 'st', 'postal', 'search_val',
    'lat', 'lon', 'mrt_lat', 'mrt_lon',
    'to_mrt', 'to_mrt_km', 'nearest_mrt', 'mrt_band'
}
always_drop_v2 = {
    'status', 'search_val', 'flat_year'
}
categorical_cols_v2 = {
    'zone_id', 'blk', 'st', 'postal', 'nearest_mrt',
    'subzone', 'flat_type', 'flat_model'
}
numerical_cols_v2 = {
    'lat', 'lon', 'mrt_lat', 'mrt_lon',
    'to_mrt', 'to_city', 'floor_area_sqm',
    'storey_midpoint', 'remaining_lease_month',
    'trx_year', 'trx_month', 'lease_commence'
}
train_year = list(range(2017, 2026))
test_year = 2026
random_seed = 2026
default_rf_params_v1 = {
    'n_estimators': 200,
    'max_depth': 16,
    'min_samples_leaf': 5,
    'n_jobs': -1,
    'random_state': random_seed
}
default_rf_params_v2 = {
    'n_estimators': 300,
    'max_depth': 18,
    'min_samples_leaf': 3,
    'n_jobs': -1,
    'random_state': random_seed
}
default_xgb_params_v1 = {
    'n_estimators': 300,
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': random_seed,
    'n_jobs': -1,
    'verbosity': 0,
}
default_xgb_params_v2 = {
    'n_estimators': 400,
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': random_seed,
    'n_jobs': -1,
    'verbosity': 0,
}
default_lgbm_params_v1 = {
    'n_estimators': 300,
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': random_seed,
    'n_jobs': -1,
    'verbosity': -1
}
default_lgbm_params_v2 = {
    'n_estimators': 400,
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': random_seed,
    'n_jobs': -1,
    'verbosity': -1,
}
default_ridge_params_v1 = {
    'alpha': 1.0,
    'random_state': random_seed,
}
default_ridge_params_v2 = {
    'alpha': 1.0,
    'random_state': random_seed,
}
max_categories_v2 = 40
