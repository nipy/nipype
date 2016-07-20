#!/bin/bash
#
# This script puts all artifacts in place after the smoke tests
#
#
set -u
set -e

mkdir -p ${CIRCLE_TEST_REPORTS}/nose
sudo mv ~/scratch/nosetests.xml ${CIRCLE_TEST_REPORTS}/nose/${CIRCLE_PROJECT_REPONAME}.xml
mkdir -p ~/docs
sudo mv ~/scratch/docs/* ~/docs/
sudo mv ~/scratch/builddocs.log ~/docs/log.txt
