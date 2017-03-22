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

# These tests are manually balanced based on previous build timings. 
# They may need to be rebalanced in the future.
case ${CIRCLE_NODE_INDEX} in
  0)
    docker run --rm=false -it -e FSL_COURSE_DATA="/data/examples/nipype-fsl_course_data" -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_pytests.sh && \
    docker run --rm=false -it -e FSL_COURSE_DATA="/data/examples/nipype-fsl_course_data" -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py27 /usr/bin/run_pytests.sh && \
    docker run --rm=false -it -v $WORKDIR:/work -w /src/nipype/doc nipype/nipype:py35 /usr/bin/run_builddocs.sh && \
    docker run --rm=false -it -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh test_spm Linear /data/examples/ workflow3d && \
    docker run --rm=false -it -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh test_spm Linear /data/examples/ workflow4d
    ;;
  1)
    docker run --rm=false -it -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh fmri_spm_dartel Linear /data/examples/ level1 && \
    docker run --rm=false -it -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh fmri_spm_dartel Linear /data/examples/ l2pipeline
    ;;
  2)
    docker run --rm=false -it -e NIPYPE_NUMBER_OF_CPUS=4 -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py27 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ level1 && \
    docker run --rm=false -it -e NIPYPE_NUMBER_OF_CPUS=4 -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ l2pipeline
    ;;
  3)
    docker run --rm=false -it -e NIPYPE_NUMBER_OF_CPUS=4 -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /data/examples/ level1 && \
    docker run --rm=false -it -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh fmri_fsl_feeds Linear /data/examples/ l1pipeline && \
    docker run --rm=false -it -v $HOME/examples:/data/examples:ro -v $WORKDIR:/work -w /work nipype/nipype:py35 /usr/bin/run_examples.sh fmri_fsl_reuse Linear /data/examples/ level1_workflow
    ;;
esac

cp ${WORKDIR}/tests/*.xml ${CIRCLE_TEST_REPORTS}/tests/
codecov -f "coverage*.xml" -s "${WORKDIR}/tests/" -R "${HOME}/nipype/" -F unittests -e CIRCLE_NODE_INDEX
codecov -f "smoketest*.xml" -s "${WORKDIR}/tests/" -R "${HOME}/nipype/" -F smoketests -e CIRCLE_NODE_INDEX
