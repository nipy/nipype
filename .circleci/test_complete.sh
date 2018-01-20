#!/bin/bash
#
# Source after running test and storing relevant return code in $exitcode

# Exit with error if any of the tests failed
if [ "$exitcode" != "0" ]; then exit 1; fi

codecov --file "${WORKDIR}/tests/coverage*.xml" \
  --root "${HOME}/nipype/" --flags unittests -e SCRIPT_NAME

codecov --file "${WORKDIR}/tests/smoketest*.xml" \
  --root "${HOME}/nipype/" --flags smoketests -e SCRIPT_NAME
