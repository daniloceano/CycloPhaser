from cyclophaser.determine_periods import determine_periods
import pandas as pd

def test_determine_periods_with_options():
    track_file = 'tests/test.csv'
    output_directory = './'

    # Specify options for the determine_periods function
    options = {
        "vorticity_column":'min_zeta_850',
        "plot": 'test',
        "plot_steps": 'test_steps',
        "export_dict": 'test',
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
