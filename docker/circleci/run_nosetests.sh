#!/bin/bash
set -e
set -x
set -u

# Create necessary directories
mkdir -p /scratch/nose /scratch/crashfiles

# Create a nipype config file
mkdir -p /root/.nipype
echo '[logging]' > /root/.nipype/nipype.cfg
echo 'log_to_file = true' >> /root/.nipype/nipype.cfg
echo 'log_directory = /scratch/logs/' >> /root/.nipype/nipype.cfg


# Run tests
cd /root/src/nipype/
make clean
nosetests -s nipype -c /root/src/nipype/.noserc --xunit-file="/scratch/nosetests.xml" --cover-xml-file="/scratch/coverage.xml"

# Copy crashfiles to scratch
for i in $(find /root/src/nipype/ -name "crash-*" ); do cp $i /scratch/crashfiles/; done
chmod 777 -R /scratch/*
