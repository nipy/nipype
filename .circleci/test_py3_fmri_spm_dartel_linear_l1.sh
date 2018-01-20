#!/bin/bash

. test_init.sh

docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_dartel Linear /data/examples/ level1
exitcode=$?

. test_complete.sh
