"""Passo 2, commit CD: add the two negative-control jobs to .circleci/config.yml.

ONLY for the disposable branch ci/app-tests-controls; never on ci/app-tests.

    python add_negative_controls.py <config.yml>

app_control_noplotly  the app_test install without plotly -> CYCLOPHASER_REQUIRE_APP_DEPS
                      must stop the session with a UsageError naming plotly (c)
app_control_python_m  the full floor install, but `python -m pytest` from the
                      checkout root -> CYCLOPHASER_REQUIRE_INSTALLED must stop it (d)
"""

import sys
from pathlib import Path

JOB = '''
  app_control:
    # NEGATIVE CONTROLS (c)/(d), disposable branch only. Each must go red.
    parameters:
      control:
        type: enum
        enum: ["noplotly", "python_m"]
    docker:
      - image: cimg/python:3.12.3
    resource_class: medium
    steps:
      - checkout
      - run:
          name: Install build tools
          command: pip install --upgrade pip build
      - run:
          name: Build sdist and wheel
          command: python -m build
      - run:
          name: Install (<< parameters.control >>)
          command: |
            if [ "<< parameters.control >>" = "noplotly" ]; then
              pip install dist/*.whl streamlit pyyaml pytest
            else
              pip install dist/*.whl "streamlit==1.56.0" plotly pyyaml pytest
            fi
            pip freeze
      - run:
          name: Run tests (<< parameters.control >>)
          environment:
            CYCLOPHASER_REQUIRE_INSTALLED: "1"
            CYCLOPHASER_REQUIRE_APP_DEPS: "1"
          command: |
            if [ "<< parameters.control >>" = "noplotly" ]; then
              pytest --import-mode=append -m "not browser and not source_tree" --junitxml=test-reports/results.xml
            else
              python -m pytest --import-mode=append -m "not browser and not source_tree" --junitxml=test-reports/results.xml
            fi
      - store_test_results:
          path: test-reports
          when: always
'''

WF = '''      - app_control:
          name: app_control_<< matrix.control >>
          matrix:
            parameters:
              control: ["noplotly", "python_m"]
          filters:
            branches:
              only:
                - ci/app-tests-controls
'''

p = Path(sys.argv[1])
s = p.read_text()
anchor_job = "\n  test_pypi_publish:\n"
anchor_wf = "      - test_pypi_publish:\n"
assert s.count(anchor_job) == 1 and s.count(anchor_wf) == 1
s = s.replace(anchor_job, JOB + anchor_job).replace(anchor_wf, WF + anchor_wf)
p.write_text(s)
print("added app_control (noplotly, python_m)")
