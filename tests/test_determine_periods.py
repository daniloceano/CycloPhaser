from cyclophaser.determine_periods import determine_periods
import pandas as pd

def test_determine_periods_with_options():
    # Read the data from the CSV file
    track_file = 'tests/test.csv'
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])
    series = track['min_max_zeta_850'].tolist()
    x = track.index.tolist()

    # Options for ERA5 processing
    options_era5 = {
        "plot": 'test_ERA5',
        "plot_steps": 'test_steps_ERA5',
        "export_dict": 'test_ERA5',
        "use_filter": 'auto',
        "replace_endpoints_with_lowpass": 24,
        "use_smoothing": 'auto',
        "use_smoothing_twice": 'auto',
        "savgol_polynomial": 3,
        "cutoff_low": 168,
        "cutoff_high": 48,
        "threshold_intensification_length": 0.075,
        "threshold_intensification_gap": 0.075,
        "threshold_mature_distance": 0.125,
        "threshold_mature_length": 0.03,
        "threshold_decay_length": 0.075,
        "threshold_decay_gap": 0.075,
        "threshold_incipient_length": 0.4
    }

    # Call the determine_periods function with options for ERA5
    result_era5 = determine_periods(series, x=x, **options_era5)
    assert isinstance(result_era5, pd.DataFrame), "Result should be a DataFrame for ERA5 options."

    # Options for basic processing without filtering
    options_basic = {
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
    
    # Test basic processing
    result_basic = determine_periods(series, x=x, **options_basic)
    assert isinstance(result_basic, pd.DataFrame), "Result should be a DataFrame for basic options."

    # Options for processing with the TRACK algorithm
    options_track = {
        "plot": "test_TRACK",
        "plot_steps": "test_steps_TRACK",
        "export_dict": False,
        "use_filter": False,
        "use_smoothing_twice": len(track) // 4 | 1,
        "threshold_intensification_length": 0.075,
        "threshold_intensification_gap": 0.075,
        "threshold_mature_distance": 0.125,
        "threshold_mature_length": 0.03,
        "threshold_decay_length": 0.075,
        "threshold_decay_gap": 0.075,
        "threshold_incipient_length": 0.4
    }

    # Test with TRACK algorithm options
    result_track = determine_periods(series, x=x, **options_track)
    assert isinstance(result_track, pd.DataFrame), "Result should be a DataFrame for TRACK options."