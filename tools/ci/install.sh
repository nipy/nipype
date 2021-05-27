#!/bin/bash

echo Installing nipype

source tools/ci/activate.sh
source tools/ci/env.sh

set -eu

# Required variables
echo INSTALL_TYPE = $INSTALL_TYPE
echo CHECK_TYPE = $CHECK_TYPE
echo NIPYPE_EXTRAS = $NIPYPE_EXTRAS
echo EXTRA_PIP_FLAGS = $EXTRA_PIP_FLAGS

set -x

if [ -n "$EXTRA_PIP_FLAGS" ]; then
    EXTRA_PIP_FLAGS=${!EXTRA_PIP_FLAGS}
fi

if [ "$INSTALL_TYPE" == "setup" ]; then
    python setup.py install
else
    pip install $EXTRA_PIP_FLAGS $ARCHIVE
fi

# Basic import check
python -c 'import nipype; print(nipype.__version__)'

if [ "$CHECK_TYPE" == "skiptests" ]; then
    exit 0
fi

pip install $EXTRA_PIP_FLAGS "nipype[$NIPYPE_EXTRAS]"

set +eux

echo Done installing nipype
