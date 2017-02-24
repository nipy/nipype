#!/bin/bash
#
# This script puts all artifacts in place after the smoke tests
#
#
set -u
set -e

mkdir -p ${CIRCLE_TEST_REPORTS}/pytest
mv ~/scratch/*.xml ${CIRCLE_TEST_REPORTS}/pytest
mkdir -p ~/docs
mv ~/scratch/docs/* ~/docs/
mkdir -p ~/logs
mv ~/scratch/builddocs.log ~/logs/builddocs.log
mv ~/scratch/logs/* ~/logs/
