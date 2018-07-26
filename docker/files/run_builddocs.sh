#!/bin/bash
set -e
set -x
set -u

WORKDIR=${WORK:-/work}

mkdir -p ${WORKDIR}/docs
make html 2>&1 | tee ${WORKDIR}/builddocs.log
cp -r /src/nipype/doc/_build/html/* ${WORKDIR}/docs/
cat ${WORKDIR}/builddocs.log && if grep -q "ERROR" ${WORKDIR}/builddocs.log; then false; else true; fi
