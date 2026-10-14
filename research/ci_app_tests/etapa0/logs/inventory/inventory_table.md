| arquivo | tipo | app (não-browser) | browser | tempo app (s) | importorskip | pulo no enxuto |
|---|---|---|---|---|---|---|
| `tests/test_app_distance_removed.py` | AppTest | 16 | 0 | 1.8 | streamlit | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_app_navigation_apptest.py` | AppTest | 10 | 0 | 7.0 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_app_passo5_fixes.py` | AppTest | 1 | 0 | 0.4 | streamlit | 1× AppTest drives the calibration app; the CI installs only the wheel, pytest and pyyaml |
| `tests/test_calibrate_i2_apptest.py` | AppTest | 13 | 0 | 5.5 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_calibrate_i3_apptest.py` | AppTest | 14 | 0 | 21.3 | pandas, streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_compare_apptest.py` | AppTest | 30 | 0 | 51.7 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_inspector_apptest.py` | AppTest | 2 | 0 | 1.2 | streamlit | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_label_apptest.py` | AppTest | 16 | 0 | 10.7 | streamlit | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_sidebar_coverage.py` | AppTest | 38 | 0 | 20.8 | streamlit | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_sidebar_defaults.py` | AppTest | 5 | 0 | 2.6 | streamlit | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_track_upload_apptest.py` | AppTest | 8 | 0 | 7.3 | streamlit | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_validate_apptest.py` | AppTest | 28 | 0 | 44.4 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_app_pages_browser.py` | browser | 0 | 9 | 0.0 | streamlit, yaml | 1× module: playwright is not installed (browser tests |
| `tests/test_compare_browser.py` | browser | 0 | 3 | 0.0 | streamlit, yaml | 1× module: playwright is not installed (browser tests |
| `tests/test_label_browser.py` | browser | 0 | 29 | 0.0 | streamlit | 1× module: playwright is not installed (browser tests |
| `tests/test_validate_browser.py` | browser | 0 | 3 | 0.0 | streamlit, yaml | 1× module: playwright is not installed (browser tests |
| `tests/test_compare_core.py` | core (streamlit/plotly, no AppTest) | 8 | 0 | 0.0 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_layer_inspector.py` | core (streamlit/plotly, no AppTest) | 4 | 0 | 0.6 | plotly | 4× could not import 'plotly': No module named 'plotly' |
| `tests/test_manual_labels.py` | core (streamlit/plotly, no AppTest) | 15 | 0 | 0.1 | streamlit, yaml | 15× the labelling tab is calibration-app code |
| `tests/test_phase_colors.py` | core (streamlit/plotly, no AppTest) | 1 | 0 | 0.0 | streamlit | 1× could not import 'streamlit': No module named 'streamlit' |
| `tests/test_phase_figures.py` | core (streamlit/plotly, no AppTest) | 4 | 0 | 0.6 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
| `tests/test_validate_core.py` | core (streamlit/plotly, no AppTest) | 13 | 0 | 2.1 | streamlit, yaml | 1× module: could not import 'streamlit': No module named 'streamlit |
