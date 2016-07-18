#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done
source activate nipypetests-2.7
python /scratch/src/nipype/tools/run_examples.py $@
