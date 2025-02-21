#!/bin/bash

echo Running tests

source tools/ci/activate.sh
source tools/ci/env.sh

set -eu

# Required variables
echo CHECK_TYPE = "$CHECK_TYPE"

set -x

if [ "${CHECK_TYPE}" == "test" ]; then
    pytest --capture=no --verbose --doctest-modules -c nipype/pytest.ini \
        --cov-config .coveragerc --cov nipype --cov-report xml \
        --junitxml=test-results.xml nipype
elif [ "$CHECK_TYPE" = "specs" ]; then
    make specs
    git status -s
    test -z "$(git status -s)"
elif [ "$CHECK_TYPE" = "style" ]; then
    black --check nipype setup.py
else
    false
fi

set +eux

echo Done running tests
