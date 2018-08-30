#!/bin/bash

docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e NIPYPE_NUMBER_OF_CPUS=4 -e NIPYPE_RESOURCE_MONITOR=1 "${DOCKER_IMAGE}:py27" /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ l2pipeline
