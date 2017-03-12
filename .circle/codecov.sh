#!/bin/bash
#
# This script pull all coverage files into the $CIRCLE_TEST_REPORTS folder
# and sends data to codecov.
#

# Setting      # $ help set
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

# Send coverage data to codecov.io
curl -so codecov.io https://codecov.io/bash
chmod 755 codecov.io

find "${SCRATCH}/" -name 'coverage*.xml' -maxdepth 1 -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F unittests
find "${SCRATCH}/" -name 'smoketest*.xml' -maxdepth 1 -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F smoketests

# Place test and coverage in the tests folder
mkdir -p ${CIRCLE_TEST_REPORTS}/tests/
cp ${SCRATCH}/pytest*.xml ${CIRCLE_TEST_REPORTS}/tests/ || true
cp ${SCRATCH}/coverage*.xml ${CIRCLE_TEST_REPORTS}/tests/ || true
cp ${SCRATCH}/smoketest*.xml ${CIRCLE_TEST_REPORTS}/tests/ || true
