"""Passo 3: turn .circleci/config.yml into the (f) stability matrix.

ONLY for the disposable branch ci/app-tests-stability; never on ci/app-tests.

    python make_stability_config.py <config.yml>

The app_test job gains a dummy integer parameter `run` (unused by any step) and
the workflow is replaced by ONE matrix entry, leg x run(1..29) = 58 jobs, named
app_test_<leg>_<run>, on this branch only. No build_test, no publishing job.
Every step of app_test stays byte-identical, so each job is exactly the app_test
of the step-1 tip.
"""

import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text()

old_params = '''    parameters:
      leg:
        type: enum
        enum: ["floor", "newest"]
'''
new_params = old_params + '''      run:
        type: integer
        default: 0
'''
assert s.count(old_params) == 1
s = s.replace(old_params, new_params)

head, sep, _ = s.partition("\nworkflows:\n")
assert sep
runs = ", ".join(str(i) for i in range(1, 30))
s = head + sep + f'''  stability_f:
    jobs:
      - app_test:
          name: app_test_<< matrix.leg >>_<< matrix.run >>
          matrix:
            parameters:
              leg: ["floor", "newest"]
              run: [{runs}]
          filters:
            branches:
              only:
                - ci/app-tests-stability
'''
p.write_text(s)
print("stability matrix: 2 legs x 29 runs = 58 jobs")
