#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done
source activate nipypetests-2.7

mkdir -p /scratch/docs
set -o pipefail && cd /root/src/nipype/doc && make html 2>&1 | tee /scratch/builddocs.log
cp -r /root/src/nipype/doc/_build/html/* /scratch/docs/
chmod 777 -R /scratch/docs
chmod 777 /scratch/builddocs.log
cat /scratch/builddocs.log && if grep -q "ERROR" /scratch/builddocs.log; then false; else true; fi
