#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

. $DIR/test_init.sh

docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /src/nipype/doc "${DOCKER_IMAGE}:py36" /usr/bin/run_builddocs.sh
exitcode=$?

. $DIR/test_complete.sh
