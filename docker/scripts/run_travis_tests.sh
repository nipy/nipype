#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done
source activate nipypetests-$1
cd /root/src/nipype
python -W once:FSL:UserWarning:nipype `which nosetests` --with-doctest --with-cov --cover-package nipype --cov-config /root/src/nipype/.coveragerc --logging-level=DEBUG --verbosity=3
