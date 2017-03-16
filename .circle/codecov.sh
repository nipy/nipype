#!/bin/bash
#
# This script pull all coverage files into the $CIRCLE_TEST_REPORTS folder
# and sends data to codecov.
#

# Setting      # $ help set
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

mkdir -p ${CIRCLE_TEST_REPORTS}/
for report in $( ls ~/scratch/*.xml ); do
    rname=$( basename $report )
    cp ${report} ${CIRCLE_TEST_REPORTS}/${rname:: -4}_${CIRCLE_NODE_INDEX}.xml
done

# Send coverage data to codecov.io
curl -so codecov.io https://codecov.io/bash
chmod 755 codecov.io

find "${CIRCLE_TEST_REPORTS}/" -name 'coverage*.xml' -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F unittests
find "${CIRCLE_TEST_REPORTS}/" -name 'smoketests*.xml' -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F smoketests
