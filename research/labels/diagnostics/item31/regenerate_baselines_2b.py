"""Item 31, stage 2b, step 7 — regenerate the class-B suite artefacts under the new defaults.

Run ONLY after DESIGN §11.3's prediction was committed (ba16572). Each artefact is
produced by exactly the call its test makes, so the test compares like with
like:

* tests/baselines/baseline_default.csv   — test_regression_baseline._run_and_dict(series, x)
* tests/baselines/baseline_smoothing.csv — the same with use_filter=False,
                                           use_smoothing=10, use_smoothing_twice=False
* tests/expected_default.csv             — determine_periods(series_pd, export_dict=…)
* tests/expected_no_filter.csv           — the same with use_filter=False

The 2.0.0 versions of the two baselines were `git mv`'d to *_2_0_0.csv first and
are NOT regenerated: they pin the explicit 2.0.0 path (cross-version).
Also asserts that the 2.0.0 table, passed explicitly, still reproduces the kept
*_2_0_0.csv files, before writing anything.

Run: python -P research/labels/diagnostics/item31/regenerate_baselines_2b.py
"""

from __future__ import annotations

import sys
import tempfile
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

REPO = core.REPO
TESTS = REPO / "tests"
sys.path.insert(0, str(TESTS))
from legacy_defaults import ALL_2_0_0  # noqa: E402

dp = core.dp


def run_and_dict(series, x, **kwargs) -> pd.DataFrame:
    """test_regression_baseline._run_and_dict, verbatim in effect."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        df = dp.determine_periods(series, x=x, **kwargs)
    d = dp.periods_to_dict(df)
    rows = [(ph, str(st), str(en)) for ph, (st, en) in d.items()]
    return pd.DataFrame(rows, columns=["phase", "start", "end"])


def main() -> None:
    core.assert_environment()
    from cyclophaser import example_file
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    series, x = track["min_max_zeta_850"], track.index
    smoothing = dict(use_filter=False, use_smoothing=10, use_smoothing_twice=False)

    # cross-version guard first: the kept 2.0.0 files are still the 2.0.0 path
    for name, kw in (("baseline_default_2_0_0", {}), ("baseline_smoothing_2_0_0", smoothing)):
        got = run_and_dict(series, x, **{**ALL_2_0_0, **kw})
        want = pd.read_csv(TESTS / "baselines" / f"{name}.csv")
        pd.testing.assert_frame_equal(got.reset_index(drop=True), want.reset_index(drop=True))
        print(f"{name}.csv reproduced by the explicit 2.0.0 table: OK")

    for name, kw in (("baseline_default", {}), ("baseline_smoothing", smoothing)):
        out = TESTS / "baselines" / f"{name}.csv"
        run_and_dict(series, x, **kw).to_csv(out, index=False)
        print(f"wrote {out.relative_to(REPO)}")

    test_track = pd.read_csv(TESTS / "test.csv", parse_dates=[0], delimiter=";", index_col=[0])
    series_pd = pd.Series(test_track["min_max_zeta_850"].tolist(), index=test_track.index.tolist())
    for name, kw in (("expected_default", {}), ("expected_no_filter", {"use_filter": False})):
        with tempfile.TemporaryDirectory() as tmp, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stem = Path(tmp) / name
            dp.determine_periods(series_pd, export_dict=str(stem), **kw)
            text = Path(f"{stem}.csv").read_text()
        (TESTS / f"{name}.csv").write_text(text)
        print(f"wrote tests/{name}.csv")


if __name__ == "__main__":
    main()
