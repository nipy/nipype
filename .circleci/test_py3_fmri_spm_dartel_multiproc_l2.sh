#!/bin/bash

docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_dartel MultiProc /data/examples/ l2pipeline
