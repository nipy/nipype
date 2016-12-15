#!/bin/bash
#
# This script puts all artifacts in place after the smoke tests
#
#
set -u
set -e

mkdir -p ${CIRCLE_TEST_REPORTS}/pytest
sudo mv ~/scratch/*.xml ${CIRCLE_TEST_REPORTS}/pytest
mkdir -p ~/docs
sudo mv ~/scratch/docs/* ~/docs/
mkdir -p ~/logs
sudo mv ~/scratch/builddocs.log ~/logs/builddocs.log
sudo mv ~/scratch/logs/* ~/logs/
