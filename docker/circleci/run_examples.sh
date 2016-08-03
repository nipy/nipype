#!/bin/bash
set -e
set -x
set -u

mkdir -p /root/.nipype
echo '[logging]' > /root/.nipype/nipype.cfg
echo 'workflow_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'interface_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'filemanip_level = DEBUG' >> /root/.nipype/nipype.cfg

python /root/src/nipype/tools/run_examples.py $@
