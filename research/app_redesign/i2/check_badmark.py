"""I2 item 3: does a bad-case mark survive Grid -> Inspector -> Grid, and a trip
to Benchmark and back? One checkout per process (sibling-import clash).

    python research/app_redesign/i2/check_badmark.py <checkout root>

AppTest (public API), developer key on (marking is a developer function since
I2; before I2 the key does not matter). Data: the checkout's own way of loading
the example — the "Try example data" button where it exists, the silent default
otherwise. The page trip is run only where the checkout has pages.
"""
import subprocess
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

root = Path(sys.argv[1]).resolve()
app = root / "tools/calibration_app/app.py"
head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                      capture_output=True, text=True).stdout.strip()
at = AppTest.from_file(str(app), default_timeout=300)
at.secrets["developer_mode"] = True
at.run()
if any(b.key == "btn_example" for b in at.button):
    at.button(key="btn_example").click()
    at.run()
mark = next(c.key for c in at.checkbox if c.key and c.key.startswith("badcase__"))
at.checkbox(key=mark).check()
at.run()
res = {"marked in Grid": mark in at.session_state and at.session_state[mark] is True}
at.radio(key="view_mode").set_value("Inspector")
at.run()
res["still marked in Inspector"] = mark in at.session_state and at.session_state[mark] is True
at.radio(key="view_mode").set_value("Grid")
at.run()
res["still marked back in Grid"] = at.checkbox(key=mark).value
if (root / "tools/calibration_app/app_pages").is_dir():
    at.switch_page("app_pages/benchmark.py").run()
    at.switch_page("app_pages/calibrate.py").run()
    res["still marked after Benchmark -> Calibrate"] = at.checkbox(key=mark).value
print(f"@ {head}{' (working tree)' if subprocess.run(['git','status','--porcelain','--untracked-files=no'], cwd=root, capture_output=True, text=True).stdout.strip() else ''}: "
      + " | ".join(f"{k}={v}" for k, v in res.items()))
