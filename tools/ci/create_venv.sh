#!/bin/bash

echo Creating isolated virtual environment

source tools/ci/env.sh

set -eu

# Required variables
echo SETUP_REQUIRES = "$SETUP_REQUIRES"

set -x

python -m pip install --upgrade pip virtualenv
virtualenv --python=python virtenv
source tools/ci/activate.sh
python --version
python -m pip install -U "$SETUP_REQUIRES"
which python
which pip

set +eux

echo Done creating isolated virtual environment
