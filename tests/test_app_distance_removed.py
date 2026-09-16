"""App-level tests for the removal of `distance` and the `length_scale` guard.

Front B measured `distance` (a minimum separation between surviving same-type
z extrema) over the 47 training series and found it redundant with
`prominence_relative` throughout the calibrated range: 0 extrema removed at
every value up to 14, first phase change only at 20, against a calibrated value
of 5. It was added after v2.0.0 and never published, so it was removed outright
rather than deprecated. See research/inert_params/REPORT_inertia_sweep.md.

Three things are pinned here:

  (a) the sidebar no longer offers the control, the app no longer carries its
      session_state, and an export never writes the key;
  (b) importing a YAML that still carries `distance` (every export from the
      previous build does) applies nothing from it and says so explicitly,
      rather than silently dropping it or calling it an unknown key;
  (c) `length_scale` is NOT removed and NOT disabled. Under
      mature_method="amplitude" it stops scaling the mature window, but it
      still scales the intensification and decay thresholds — measured to
      change the phase output on 3 of the 47 training series — so it carries a
      scoped note instead of the blanket `disabled=True` that
      'Min. mature length' and 'Mature distance' carry.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PY = REPO_ROOT / "tools" / "calibration_app" / "app.py"
INSPECTOR_PY = REPO_ROOT / "tools" / "calibration_app" / "layer_inspector.py"

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


def _app() -> AppTest:
    at = AppTest.from_file(str(APP_PY), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


# ── (a) the control, the state and the export are gone ───────────────────────

class TestDistanceControlRemoved:

    def test_no_distance_widget_label(self):
        at = _app()
        labels = ([c.label for c in at.checkbox]
                  + [n.label for n in at.number_input]
                  + [s.label for s in at.slider])
        offenders = [lab for lab in labels
                     if lab and "distance" in lab.lower()
                     and "mature" not in lab.lower()]
        assert not offenders, f"distance widget still rendered: {offenders}"

    def test_no_distance_session_state(self):
        at = _app()
        keys = [k for k in at.session_state.filtered_state
                if "distance" in k and "mature" not in k]
        assert not keys, f"distance session_state survives: {keys}"

    def test_source_has_no_distance_defaults(self):
        src = APP_PY.read_text()
        assert "extrema_distance_enabled" not in src
        assert "extrema_distance_val" not in src
        assert "_parse_distance" not in src

    def test_package_call_sites_pass_no_distance(self):
        """Neither the app nor the layer inspector may still pass `distance=`."""
        for path in (APP_PY, INSPECTOR_PY):
            src = path.read_text()
            assert not re.search(r"\bdistance\s*=", src), (
                f"{path.name} still passes a distance= keyword")

    def test_export_never_writes_distance(self):
        at = _app()
        build = at.session_state  # touch, then reach the module for _build_yaml
        import importlib.util
        spec = importlib.util.spec_from_file_location("_app_mod", APP_PY)
        assert spec and spec.loader
        src = APP_PY.read_text()
        # _build_yaml's phase_params block must not mention distance at all
        block = src[src.index('"phase_params": {'):]
        block = block[:block.index("},")]
        assert "distance" not in block, "export still writes a distance key"
        del build


# ── (b) importing a YAML that still carries `distance` ───────────────────────

class TestDistanceImportWarning:

    def test_removed_key_map_carries_the_explanation(self):
        src = APP_PY.read_text()
        assert "_REMOVED_PHASE_YAML_KEYS" in src
        assert "distance removido: redundante com prominence_relative" in src
        assert "research/inert_params/REPORT_inertia_sweep.md" in src

    def test_distance_is_not_reported_as_an_unknown_key(self):
        """It is a known, removed key — not a typo — so it must not be `ignored`
        as 'unknown'; it gets its own explained entry instead."""
        src = APP_PY.read_text()
        # the generic unknown-key comprehension must exclude removed keys
        assert "if k not in _REMOVED_PHASE_YAML_KEYS" in src

    def test_reference_config_still_carries_distance(self):
        """The versioned params-9 export is the real-world case this handles."""
        import yaml
        cfg = REPO_ROOT / "research/labels/configs/cyclophaser_params-9.yaml"
        doc = yaml.safe_load(cfg.read_text())
        assert doc["phase_params"]["distance"] == 5, (
            "params-9 is a historical record and must keep distance: 5")


# ── (c) length_scale survives, guarded but ENABLED ───────────────────────────

class TestLengthScaleGuard:

    def test_length_scale_widget_still_exists(self):
        at = _app()
        radios = [r for r in at.radio if r.label and "Threshold scale" in r.label]
        assert radios, "length_scale radio disappeared"
        # .options carries the format_func'd display strings, not the raw values
        assert len(radios[0].options) == 2
        joined = " ".join(radios[0].options).lower()
        assert "global" in joined and "local" in joined

    def test_length_scale_is_not_disabled_under_amplitude(self):
        """Disabling it would present a live control as inert: under
        'amplitude' it still scales the intensification/decay thresholds."""
        at = _app()
        for r in at.radio:
            if r.label and "Mature stage method" in str(r.label):
                r.set_value("amplitude")
                break
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
        radios = [r for r in at.radio if r.label and "Threshold scale" in r.label]
        assert radios, "length_scale radio disappeared under amplitude"
        assert radios[0].disabled is False, (
            "length_scale must stay enabled under mature_method='amplitude'")

    def test_length_scale_help_explains_the_partial_inactivity(self):
        src = APP_PY.read_text()
        assert "_length_scale_mature_active" in src
        assert "Partially inactive" in src
        assert "REMAINS ACTIVE" in src

    def test_mature_only_sliders_are_still_fully_disabled(self):
        """The contrast the note depends on: these two ARE inert under
        'amplitude' and stay `disabled`."""
        at = _app()
        for r in at.radio:
            if r.label and "Mature stage method" in str(r.label):
                r.set_value("amplitude")
                break
        at.run()
        for s in at.slider:
            if s.label in ("Min. mature length", "Mature distance"):
                assert s.disabled is True, f"{s.label} should be disabled"
