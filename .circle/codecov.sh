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
${HOME}/bin/codecov -f "coverage*.xml" -s "${WORKDIR}/tests/" -R "${HOME}/nipype/" -F unittests -v -K
${HOME}/bin/codecov -f "smoketest*.xml" -s "${WORKDIR}/tests/" -R "${HOME}/nipype/" -F smoketests -v -K
