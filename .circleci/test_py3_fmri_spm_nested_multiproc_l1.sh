#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

. $DIR/test_init.sh

docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e NIPYPE_NUMBER_OF_CPUS=4 "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ level1
exitcode=$?

. $DIR/test_complete.sh
