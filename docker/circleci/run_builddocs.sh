#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done
source activate nipypetests-2.7

set -o pipefail && cd /scratch/src/nipype/doc && make html 2>&1 | tee /scratch/builddoc.log
cat /scratch/builddoc.log && if grep -q "ERROR" /scratch/builddoc.log; then false; else true; fi

