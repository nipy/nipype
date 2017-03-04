#!/bin/bash
#
# This script pull all coverage files into the $CIRCLE_TEST_REPORTS folder
# and sends data to codecov.
#

# Setting      # $ help set
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

mkdir -p ${CIRCLE_TEST_REPORTS}/unittests ${CIRCLE_TEST_REPORTS}/smoketest
cp ${SCRATCH}/coverage*.xml ${CIRCLE_TEST_REPORTS}/unittests/
cp ${SCRATCH}/smoketests*.xml ${CIRCLE_TEST_REPORTS}/smoketest/

# Send coverage data to codecov.io
curl -so codecov.io https://codecov.io/bash
chmod 755 codecov.io

find "${CIRCLE_TEST_REPORTS}/unittests" -name '*.xml' -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F unittests
find "${CIRCLE_TEST_REPORTS}/smoketest" -name '*.xml' -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F smoketests
