"""Fail the app_test job unless its skips are EXACTLY the allowed ones.

    python .circleci/check_app_skips.py <junit.xml>

The app job runs without playwright, so the four browser modules skip whole at
collection, and one synthetic case skips by design. Anything else that skips —
an app test that starts skipping for a new reason, or a dependency the lock in
tests/conftest.py does not name — fails here. Ids are junit (classname, name),
never the text of a skip reason; a module skipped at collection has an empty
classname and the dotted module as its name. A new legitimate skip means
updating ALLOWED on purpose.

Standard library only: this runs in CI, outside the package and the app.
"""

import sys
import xml.etree.ElementTree as ET

ALLOWED = {
    ("", "tests.test_app_pages_browser"),
    ("", "tests.test_compare_browser"),
    ("", "tests.test_label_browser"),
    ("", "tests.test_validate_browser"),
    ("tests.synthetic.test_synthetic_lifecycles",
     "test_lifecycle_phase_timing[IcIt_observational]"),
}


def main(path):
    skipped = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        if tc.find("skipped") is not None:
            skipped.append((tc.get("classname") or "", tc.get("name") or ""))
    unexpected = sorted(set(skipped) - ALLOWED)
    missing = sorted(ALLOWED - set(skipped))
    duplicated = sorted({s for s in skipped if skipped.count(s) > 1})
    for c, n in sorted(skipped):
        print(f"skipped: {c}::{n}" if c else f"skipped: {n}")
    if unexpected or missing or duplicated:
        for c, n in unexpected:
            print(f"UNEXPECTED skip: {c}::{n}" if c else f"UNEXPECTED skip: {n}")
        for c, n in missing:
            print(f"MISSING allowed skip: {c}::{n}" if c else f"MISSING allowed skip: {n}")
        for c, n in duplicated:
            print(f"DUPLICATED skip: {c}::{n}" if c else f"DUPLICATED skip: {n}")
        print(f"FAIL: {len(skipped)} skips, expected exactly the {len(ALLOWED)} allowed")
        return 1
    print(f"OK: skips are exactly the {len(ALLOWED)} allowed ids")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
