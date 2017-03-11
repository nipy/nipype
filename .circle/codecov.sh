#!/bin/bash
#
# This script pull all coverage files into the $CIRCLE_TEST_REPORTS folder
# and sends data to codecov.
#

# Setting      # $ help set
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

# Place py.test reports in folders
for f in $( find $SCRATCH/ -name "pytest*.xml" ); do
	folder=$( basename ${f:: -4} )
	mkdir -p ${CIRCLE_TEST_REPORTS}/$folder
	cp $f ${CIRCLE_TEST_REPORTS}/$folder/pytest.xml
done

# Send coverage data to codecov.io
curl -so codecov.io https://codecov.io/bash
chmod 755 codecov.io

find "${SCRATCH}/" -name 'coverage*.xml' -maxdepth 1 -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F unittests
find "${SCRATCH}/" -name 'smoketest*.xml' -maxdepth 1 -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F smoketests

# Place coverage in the correct folders
mkdir -p ${CIRCLE_TEST_REPORTS}/unittests ${CIRCLE_TEST_REPORTS}/smoketest
cp ${SCRATCH}/coverage*.xml ${CIRCLE_TEST_REPORTS}/unittests/ || true
cp ${SCRATCH}/smoketest*.xml ${CIRCLE_TEST_REPORTS}/smoketest/ || true
