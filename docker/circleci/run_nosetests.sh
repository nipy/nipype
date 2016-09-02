#!/bin/bash
set -e
set -x
set -u

# Create necessary directories
mkdir -p /scratch/nose /scratch/crashfiles /scratch/logs/$1

# Create a nipype config file
mkdir -p /root/.nipype
echo '[logging]' > /root/.nipype/nipype.cfg
echo 'log_to_file = true' >> /root/.nipype/nipype.cfg
echo "log_directory = /scratch/logs/$1" >> /root/.nipype/nipype.cfg
echo '[execution]' >> /root/.nipype/nipype.cfg
echo 'profile_runtime = true' >> /root/.nipype/nipype.cfg

# Run tests
cd /root/src/nipype/
make clean
nosetests -s nipype -c /root/src/nipype/.noserc --xunit-file="/scratch/nosetests_$1.xml" --cover-xml-file="/scratch/coverage_$1.xml"

# Copy crashfiles to scratch
for i in $(find /root/src/nipype/ -name "crash-*" ); do cp $i /scratch/crashfiles/; done
chmod 777 -R /scratch/*
