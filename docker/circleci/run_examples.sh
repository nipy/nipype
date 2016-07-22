#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done

mkdir -p /root/.nipype
echo '[logging]' > /root/.nipype/nipype.cfg
echo 'workflow_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'interface_level = DEBUG' >> /root/.nipype/nipype.cfg
echo 'filemanip_level = DEBUG' >> /root/.nipype/nipype.cfg

source activate nipypetests-2.7
python /root/src/nipype/tools/run_examples.py $@
