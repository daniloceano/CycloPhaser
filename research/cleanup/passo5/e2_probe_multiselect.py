"""Passo 5, E2 — where the Benchmark failures under streamlit 1.58 come from (no ids printed).
Run with the python of each environment, from the repository root; run at 79862a0 (before the fixes)
for the classification. Steps: render; set raw ids; set the formatted labels (what the tests did);
the preset buttons Train then Test."""
import warnings; warnings.simplefilter("ignore")
import streamlit, sys
from streamlit.testing.v1 import AppTest
print("streamlit", streamlit.__version__)
def app():
    at = AppTest.from_file(str(__import__('pathlib').Path(__file__).resolve().parents[3] / 'tools/calibration_app/app.py'), default_timeout=300); at.run(); return at
def ms(at): return next(w for w in at.multiselect if w.key == "bench_ids_widget")
at = app(); print("render exceptions:", len(at.exception))
w = ms(at)
try:
    print("read options/value in the harness: ok", len(w.options), "options")
except Exception as e:
    print("reading the widget in the harness raised", type(e).__name__)
raw = [o.split(" ")[0] for o in w.options[:2]]
at2 = app(); ms(at2).set_value(raw).run(); print("set raw ids -> app exceptions:", len(at2.exception))
at3 = app()
try:
    ms(at3).set_value(list(ms(at3).options[:2])).run(); print("set formatted labels (what the test does) -> app exceptions:", len(at3.exception))
except Exception as e:
    import traceback; tb = traceback.extract_tb(e.__traceback__); print("set formatted labels (what the test does) -> raised", type(e).__name__, "in", [f"{f.filename.split(chr(47))[-1]}:{f.lineno}" for f in tb][-3:])
at4 = app(); next(b for b in at4.button if b.key == "bench_pick_train").click().run(); print("click Train -> app exceptions:", len(at4.exception), "| n selected (session):", len(at4.session_state["bench_selected_ids"]) if "bench_selected_ids" in at4.session_state else "?")
next(b for b in at4.button if b.key == "bench_pick_test").click().run(); print("then click Test -> app exceptions:", len(at4.exception), "| n selected (session):", len(at4.session_state["bench_selected_ids"]) if "bench_selected_ids" in at4.session_state else "?")
