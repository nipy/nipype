#!/bin/bash

echo Running tests

source tools/ci/activate.sh
source tools/ci/env.sh

set -eu

# Required variables
echo CHECK_TYPE = $CHECK_TYPE

set -x

if [ "${CHECK_TYPE}" == "test" ]; then
    pytest --capture=no --verbose --doctest-modules -c nipype/pytest.ini \
        --cov-config .coveragerc --cov nipype --cov-report xml \
        --junitxml=test-results.xml nipype
else
    false
fi

set +eux

echo Done running tests
