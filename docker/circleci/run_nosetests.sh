#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done
source activate nipypetests-2.7
cd /root/src/nipype
mkdir -p /scratch/nose
nosetests -c /root/src/nipype/.noserc --xunit-file="/scratch/nosetests.xml" --cover-xml-file="/scratch/coverage.xml"
chmod 777 /scratch/nosetests.xml
chmod 777 /scratch/coverage.xml
chmod 777 -R /scratch/nose