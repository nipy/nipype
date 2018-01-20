#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

. $DIR/test_init.sh

# These tests are manually balanced based on previous build timings.
# They may need to be rebalanced in the future.
docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e CI_SKIP_TEST=1 -e NIPYPE_RESOURCE_MONITOR=1 -e FSL_COURSE_DATA="/data/examples/nipype-fsl_course_data"  "${DOCKER_IMAGE}:py36" /usr/bin/run_pytests.sh \
&& docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e CI_SKIP_TEST=1 -e NIPYPE_RESOURCE_MONITOR=1 -e FSL_COURSE_DATA="/data/examples/nipype-fsl_course_data" "${DOCKER_IMAGE}:py27" /usr/bin/run_pytests.sh \
&& docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /src/nipype/doc "${DOCKER_IMAGE}:py36" /usr/bin/run_builddocs.sh
exitcode=$?

. $DIR/test_complete.sh
