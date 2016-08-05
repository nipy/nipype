#!/bin/bash
#
# This script puts all artifacts in place after the smoke tests
#
#
set -u
set -e

mkdir -p ${CIRCLE_TEST_REPORTS}/nose
sudo mv ~/scratch/builddocs.log ~/builddocs.log
sudo cp ~/scratch/nosetests.xml ${CIRCLE_TEST_REPORTS}/nose/${CIRCLE_PROJECT_REPONAME}.xml
sudo mv ~/scratch/coverage.xml ~/coverage.xml
mkdir -p ~/docs
sudo mv ~/scratch/docs/* ~/docs/
mkdir -p ~/logs
sudo mv $(pwd)/scratch/logs/* ~/logs/