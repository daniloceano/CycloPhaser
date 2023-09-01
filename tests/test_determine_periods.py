from cyclophaser.determine_periods import determine_periods
import pandas as pd

def test_determine_periods_with_options():
    track_file = 'tests/test.csv'

    # Specify options for the determine_periods function
    options = {
        "vorticity_column":'min_zeta_850',
        "plot": 'test_ERA5',
        "plot_steps": 'test_steps_ERA5',
        "export_dict": 'test_ERA5',
        "process_vorticity_args": {
            "use_filter": 'auto',
            "replace_endpoints_with_lowpass": 24,
            "use_smoothing": 'auto',
            "use_smoothing_twice": 'auto',
            "savgol_polynomial": 3,
            "cutoff_low": 168,
            "cutoff_high": 48
        }
    }

    # Call the determine_periods function with options
    result = determine_periods(track_file, **options)

    # Add assertions to verify the expected behavior
    assert isinstance(result, pd.DataFrame)

    options = {
        "plot": False,
        "plot_steps": False,
        "export_dict": None,
        "process_vorticity_args": {
            "use_filter": False
        }
    }
    
    result = determine_periods(track_file, **options)
    # Add assertions to verify the expected behavior
    assert isinstance(result, pd.DataFrame)

    track = pd.read_csv(track_file)
    options = {
        "plot": "test_TRACK",
        "plot_steps": "test_steps_TRACK",
        "export_dict": False,
        "process_vorticity_args": {
            "use_filter": False,
            "use_smoothing_twice": len(track)//4 | 1}
    }

    result = determine_periods(track_file, **options)
    # Add assertions to verify the expected behavior
    assert isinstance(result, pd.DataFrame)
