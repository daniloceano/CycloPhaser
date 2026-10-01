#!/usr/bin/env python
"""Passo 4, commit 16d — docstring/comment-only edits in cyclophaser/ (gate (a), second form).

    python research/cleanup/passo4/edit_16d.py

Each edit is an exact replacement asserted to match the stated number of times.
The review of every sweep hit (true / false, against which reference) is in
passo4/sweep_16d_review.md; this script applies only the "false" rows and the
three rst fixes. Log: passo4/edit_16d_log.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FS, DP = "cyclophaser/find_stages.py", "cyclophaser/determine_periods.py"
NOTE = ("thresholds. A default named below is this function's own fallback for\n"
        "            a key absent from args_periods, which only a direct call produces:\n"
        "            get_periods always passes every key, with its own defaults. Including:")
EDITS = [
    # --- find_stages.py: module comments that state the PACKAGE default ------------------
    (FS, 1, '# length_scale: "global" (default) vs "local"\n',
     '# length_scale: "global" vs "local" ("local" is the get_periods default since item 31)\n'),
    (FS, 1, '# `length_scale="local"` (opt-in; default remains "global" for exact backward\n'
            '# compatibility) makes the five global thresholds',
     '# `length_scale="local"` (introduced as opt-in; the get_periods default since\n'
     '# item 31, while the stage functions below fall back to "global" when called\n'
     '# directly without the key) makes the five global thresholds'),
    (FS, 1, '# incipient_method: "geometric" (default) vs "plateau"\n',
     '# incipient_method: "geometric" vs "plateau" ("plateau" is the get_periods default since item 31)\n'),
    (FS, 1, '# `incipient_method="plateau"` (opt-in; default remains "geometric", which is\n'
            '# byte-identical to every prior version) replaces',
     '# `incipient_method="plateau"` (introduced as opt-in, "geometric" staying the\n'
     '# default and byte-identical to every prior version; the get_periods default\n'
     '# since item 31) replaces'),
    (FS, 1, '# artifact at t0 has been dealt with. Under bare package defaults the very\n',
     '# artifact at t0 has been dealt with. Under the bare package defaults of that\n'
     '# measurement (01c4492, above) the very\n'),
    (FS, 1, 'This is why the method is opt-in and why tau',
     'This is why the method was introduced as opt-in and why tau'),
    (FS, 1, '# before, and `incipient_smooth_window=0` (the default) reproduces the previous\n',
     '# before, and `incipient_smooth_window=0` (the default before item 31, and the\n'
     '# fallback of find_incipient_period on a direct call) reproduces the previous\n'),
    # --- find_stages.py: stage-function docstrings/comments (checked against own fallback) --
    (FS, 5, "thresholds, including:", NOTE),
    (FS, 1, '(that\'s the "derivative"/default method,', '(that\'s the "derivative" method,'),
    (FS, 1, "exactly like the previous/next z_peak pair the default method already uses",
     'exactly like the previous/next z_peak pair the "derivative" method already uses'),
    (FS, 1, '    - "derivative" (default, unchanged behaviour): the mature window is a fixed\n',
     '    - "derivative" (the fallback on a direct call without the key): the mature\n'
     '      window is a fixed\n'),
    (FS, 1, '    - "amplitude" (opt-in): the mature window is the contiguous stretch of z\n',
     '    - "amplitude" (the get_periods default since item 31): the mature window is\n'
     '      the contiguous stretch of z\n'),
    (FS, 1, "    # Default 0.0 disables the rule: every valley has D1 >= 0 by construction,\n",
     "    # The fallback 0.0 (a direct call without the key; get_periods passes its own\n"
     "    # default) disables the rule: every valley has D1 >= 0 by construction,\n"),
    (FS, 1, "    # Default 0.0 disables the rule outright: the guard below runs the floor\n"
            "    # ONLY when it is > 0, so on the default path no depth is computed and no\n",
     "    # The fallback 0.0 (a direct call without the key; get_periods passes its own\n"
     "    # default) disables the rule outright: the guard below runs the floor\n"
     "    # ONLY when it is > 0, so on that path no depth is computed and no\n"),
    (FS, 1, "    # segment that ends shallower than it starts is still admitted by default,\n",
     "    # segment that ends shallower than it starts is still admitted under 0.0,\n"),
    (FS, 1, "    'decay_tail_amplitude_fraction' note (opt-in, default None: no effect)\n"
            "    ------------------------------------------------------------------------\n",
     "    'decay_tail_amplitude_fraction' note (fallback None on a direct call: no effect)\n"
     "    --------------------------------------------------------------------------------\n"),
    (FS, 1, "# decay_tail_amplitude_fraction (opt-in, see docstring above): if the NaN\n",
     "# decay_tail_amplitude_fraction (see the docstring above; None switches it off): if the NaN\n"),
    (FS, 1, "      * ``window <= 0`` disables it (the default);\n",
     "      * ``window <= 0`` disables it (the fallback of find_incipient_period on a\n"
     "        direct call);\n"),
    (FS, 1, '    """Item 30 (opt-in): the plateau boundary, pulled back so as not to erase an\n',
     '    """Item 30 (the get_periods default since item 31): the plateau boundary,\n'
     '    pulled back so as not to erase an\n'),
    (FS, 1, '    ``"geometric"`` (default, unchanged from every prior version)\n',
     '    ``"geometric"`` (the fallback on a direct call without the key; unchanged from every prior version)\n'),
    (FS, 1, '    ``"plateau"`` (opt-in)\n', '    ``"plateau"`` (the get_periods default since item 31)\n'),
    # --- determine_periods.py ---------------------------------------------------------------
    (DP, 1, "are all fractions of a *length*.  With the default\n"
            "    ``length_scale=\"global\"`` that length is the whole input series\n",
     "are all fractions of a *length*.  With\n"
     "    ``length_scale=\"global\"`` (the default before item 31) that length is the whole input series\n"),
    (DP, 1, "visible STEP. Measured over the 51 tracks with the package defaults, the\n",
     "visible STEP. Measured over the 51 tracks with the package defaults of that\n"
     "    time (before item 31), the\n"),
    (DP, 1, '"amplitude"\n            (opt-in) instead defines the mature window',
     '"amplitude"\n            (the default since item 31) instead defines the mature window'),
    # --- rst problems that break the build (determine_periods docstring) -----------------------
    (DP, 1, 'use `"northern"` to detect maxima in both hemispheres. For **sea level \n'
            '            pressure (SLP) data**, set to',
     'use `"northern"` to detect maxima in both hemispheres. For\n'
     '            **sea level pressure (SLP) data**, set to'),
    (DP, 1, "Polynomial order for Savitzky-Golay smoothing. **Must be less than or equal \n"
            "            to the window length specified in `use_smoothing` and `use_smoothing_twice`.** Default is 3.",
     "Polynomial order for Savitzky-Golay smoothing. Must be less than or equal\n"
     "            to the window length specified in `use_smoothing` and `use_smoothing_twice`. Default is 3."),
    (DP, 1, "`\"reflect\"` takes the normalised |dz| at t0 from a median 0.95",
     "`\"reflect\"` takes the normalised ``|dz|`` at t0 from a median 0.95"),
]

log = []
for f, n, old, new in EDITS:
    p = ROOT / f
    s = p.read_text()
    assert s.count(old) == n, (f, s.count(old), old[:70])
    p.write_text(s.replace(old, new))
    log.append(dict(file=f, count=n, old=old, new=new))
(Path(__file__).with_name("edit_16d_log.json")).write_text(json.dumps(log, indent=1, ensure_ascii=False))
print(f"{len(log)} edits ({sum(e['count'] for e in log)} replacements) in {len({e['file'] for e in log})} files")
