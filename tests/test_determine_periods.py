from cyclophaser.determine_periods import determine_periods
import pandas as pd
import numpy as np
import xarray as xr
import warnings

def load_expected_csv(filepath):
    return pd.read_csv(filepath)

def test_determine_periods_with_options():
    # Suppress specific warning in this test
    warnings.filterwarnings("ignore", message="Detected potential spurious oscillations at the series boundaries.*")
    # Read the data from the CSV file
    track_file = 'tests/test.csv'
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])
    series_list = track['min_max_zeta_850'].tolist()
    x_list = track.index.tolist()
    
    # Convert data to other types
    series_np = np.array(series_list)
    series_pd = pd.Series(series_list, index=x_list)
    series_xr = xr.DataArray(series_list, coords=[x_list], dims="time")

    # Define file paths for the expected output files
    expected_csv_default = 'tests/expected_default.csv'
    expected_csv_no_filter = 'tests/expected_no_filter.csv'
    output_csv_default = 'tests/test_dict_default'
    output_csv_no_filter = 'tests/test_dict_default_no_filter'

    # Test with default parameters and check against expected CSV
    determine_periods(series_pd, export_dict=output_csv_default)
    output_df_default = load_expected_csv(f'{output_csv_default}.csv') 
    expected_df_default = load_expected_csv(expected_csv_default)
    assert output_df_default.equals(expected_df_default), "Default test failed: Output does not match expected"

    # Test with default parameters without filtering and check against expected CSV
    determine_periods(series_pd, use_filter=False, export_dict=output_csv_no_filter)
    output_df_no_filter = load_expected_csv(f'{output_csv_no_filter}.csv')
    expected_df_no_filter = load_expected_csv(expected_csv_no_filter)
    assert output_df_no_filter.equals(expected_df_no_filter), "No-filter test failed: Output does not match expected"

    # Test input types (basic functionality check)
    options = {
        "plot": False,
        "plot_steps": False,
        "export_dict": None,
        "use_filter": False,
        "use_smoothing_twice": False,
        "threshold_intensification_length": 0.075,
        "threshold_intensification_gap": 0.075,
        "threshold_mature_distance": 0.125,
        "threshold_mature_length": 0.03,
        "threshold_decay_length": 0.075,
        "threshold_decay_gap": 0.075,
        "threshold_incipient_length": 0.4
    }

    # List input
    result_list = determine_periods(series_list, x=x_list, **options)
    assert isinstance(result_list, pd.DataFrame), "Result should be a DataFrame for list input."

    # Numpy array input
    result_np = determine_periods(series_np, x=x_list, **options)
    assert isinstance(result_np, pd.DataFrame), "Result should be a DataFrame for numpy array input."

    # Pandas Series input
    result_pd = determine_periods(series_pd, **options)
    assert isinstance(result_pd, pd.DataFrame), "Result should be a DataFrame for pandas Series input."

    # Xarray DataArray input
    result_xr = determine_periods(series_xr, **options)
    assert isinstance(result_xr, pd.DataFrame), "Result should be a DataFrame for xarray DataArray input."

    print("All tests passed.")

# Run the test
if __name__ == "__main__":
    test_determine_periods_with_options()