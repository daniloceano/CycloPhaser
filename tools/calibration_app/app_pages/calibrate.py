"""Calibrate page — registration only.

The Calibrate page's code is app.py itself, inline below its "Pages" block:
app.py is the entrypoint the public app on Streamlit Community Cloud points at,
and a large part of its declarations is read straight out of its source by the
test suite, so it was not split. When this page is the one open, app.py never
calls this file's `run()`; it carries on with its own body instead. This file
exists because `st.Page` registers a page by file (the menu entry, the URL
`/calibrate`, and `AppTest.switch_page`, which finds pages by path).
"""
