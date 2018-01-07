#!/bin/bash
#
# Balance nipype testing workflows across CircleCI build nodes
#

# Setting      # $ help set
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

if [ "${CIRCLE_NODE_TOTAL:-}" != "4" ]; then
  echo "These tests were designed to be run at 4x parallelism."
  exit 1
fi

DOCKER_IMAGE="nipype/nipype"

# These tests are manually balanced based on previous build timings.
# They may need to be rebalanced in the future.
case ${CIRCLE_NODE_INDEX} in
  0)
       docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e CI_SKIP_TEST=1 -e NIPYPE_RESOURCE_MONITOR=1 -e FSL_COURSE_DATA="/data/examples/nipype-fsl_course_data"  "${DOCKER_IMAGE}:py36" /usr/bin/run_pytests.sh \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e CI_SKIP_TEST=1 -e NIPYPE_RESOURCE_MONITOR=1 -e FSL_COURSE_DATA="/data/examples/nipype-fsl_course_data" "${DOCKER_IMAGE}:py27" /usr/bin/run_pytests.sh \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /src/nipype/doc "${DOCKER_IMAGE}:py36" /usr/bin/run_builddocs.sh \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh test_spm Linear /data/examples/ workflow3d \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh test_spm Linear /data/examples/ workflow4d
    exitcode=$?
    ;;
  1)
       docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_dartel Linear /data/examples/ level1 \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_dartel Linear /data/examples/ l2pipeline
    exitcode=$?
    ;;
  2)
       docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e NIPYPE_NUMBER_OF_CPUS=4 "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ level1 \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e NIPYPE_NUMBER_OF_CPUS=4 -e NIPYPE_RESOURCE_MONITOR=1 "${DOCKER_IMAGE}:py27" /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ l2pipeline
    exitcode=$?
    ;;
  3)
       docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work -e NIPYPE_NUMBER_OF_CPUS=4 "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ level1 \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_fsl_feeds Linear /data/examples/ l1pipeline \
    && docker run --rm=false -t -v $WORKDIR:/work -v $HOME/examples:/data/examples:ro -w /work "${DOCKER_IMAGE}:py36" /usr/bin/run_examples.sh fmri_fsl_reuse Linear /data/examples/ level1_workflow
    exitcode=$?
    ;;
esac

# Exit with error if any of the tests failed
if [ "$exitcode" != "0" ]; then exit 1; fi

codecov --file "${WORKDIR}/tests/coverage*.xml" \
  --root "${HOME}/nipype/" --flags unittests -e CIRCLE_NODE_INDEX

codecov --file "${WORKDIR}/tests/smoketest*.xml" \
  --root "${HOME}/nipype/" --flags smoketests -e CIRCLE_NODE_INDEX
