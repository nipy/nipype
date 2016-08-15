#!/bin/bash
set -e
set -x
set -u

mkdir -p /scratch/nose /scratch/crashfiles
mkdir -p /root/.nipype
echo '[logging]' > /root/.nipype/nipype.cfg
echo 'log_to_file = true' >> /root/.nipype/nipype.cfg
echo 'log_directory = /scratch/logs/' >> /root/.nipype/nipype.cfg

nosetests -c /root/src/nipype/.noserc --xunit-file="/scratch/nosetests.xml" --cover-xml-file="/scratch/coverage.xml"

cp /root/nipype/src/crash-* /scratch/crashfiles/
chmod 777 -R /scratch/*