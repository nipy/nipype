#!/bin/bash

docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e NIPYPE_NUMBER_OF_CPUS=4 "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ level1
