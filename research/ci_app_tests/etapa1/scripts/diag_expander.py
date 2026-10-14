"""Passo 3b: what AppTest's `.expander` returns on an expander block, per version.

    python diag_expander.py <out.json>

Run with the python of a venv holding one streamlit version. Two tiny apps, run
with AppTest.from_string (public API only):

* FLAT   — one expander in the sidebar and one in the main area, each holding a
           checkbox: what `at.sidebar.expander[i].expander` and
           `at.expander[i].expander` return (labels), whether the group itself is
           in its own list (by identity), and the corrected count — descendants
           excluding the group itself, the expression the fixed test uses.
* NESTED — an expander inside an expander, in the sidebar and in the main area:
           whether streamlit allows it (the exception text if not) and, if it
           does, the corrected count for the outer group (positive control: >= 1).
"""

import json
import sys

import streamlit
from streamlit.testing.v1 import AppTest

FLAT = '''
import streamlit as st
with st.sidebar.expander("S-group"):
    st.checkbox("s-widget")
with st.expander("M-group"):
    st.checkbox("m-widget")
'''

NESTED_SIDEBAR = '''
import streamlit as st
with st.sidebar.expander("S-outer"):
    with st.expander("S-inner"):
        st.checkbox("s-widget")
'''

NESTED_MAIN = '''
import streamlit as st
with st.expander("M-outer"):
    with st.expander("M-inner"):
        st.checkbox("m-widget")
'''


def nested_descendants(group):
    """The fixed test's count: expanders under `group`, the group itself excluded."""
    return [e for e in group.expander if e is not group]


def describe(groups):
    return [{"label": g.label,
             "expander_labels": [e.label for e in g.expander],
             "contains_itself": any(e is g for e in g.expander),
             "corrected_count": len(nested_descendants(g))}
            for g in groups]


def run(src):
    at = AppTest.from_string(src, default_timeout=60)
    at.run()
    return at, [str(getattr(e, "value", e)) for e in at.exception]


def main(out):
    res = {"streamlit": streamlit.__version__}
    at, exc = run(FLAT)
    res["flat"] = {"exceptions": exc,
                   "sidebar": describe(at.sidebar.expander),
                   "main": describe(at.main.expander)}
    for name, src in (("nested_sidebar", NESTED_SIDEBAR), ("nested_main", NESTED_MAIN)):
        at, exc = run(src)
        block = at.sidebar if name == "nested_sidebar" else at.main
        res[name] = {"allowed": not exc, "exceptions": exc,
                     "all_expanders": [e.label for e in block.expander],
                     "groups": describe(block.expander)}
    json.dump(res, open(out, "w"), indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
