#!/bin/bash
set -e
set -x
set -u

mkdir -p /root/.nipype
echo '[logging]' > /root/.nipype/nipype.cfg
echo 'workflow_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'interface_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'filemanip_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'log_to_file = true' >> /root/.nipype/nipype.cfg
echo 'log_directory = /scratch/logs/' >> /root/.nipype/nipype.cfg

coverage run /root/src/nipype/tools/run_examples.py $@
arr=$@
tmp_var=$( IFS=$' '; echo "${arr[*]}" )
coverage xml -o "/scratch/smoketest_${tmp_var//[^A-Za-z0-9_-]/_}.xml"

chmod 777 -R /scratch/logs
