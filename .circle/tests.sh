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
    docker run --rm -it -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /root/src/nipype nipype/nipype_test:py27 /usr/bin/run_pytests.sh py27 && \
    docker run --rm -it -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /root/src/nipype nipype/nipype_test:py35 /usr/bin/run_pytests.sh py35 && \
    docker run --rm -it -v $SCRATCH:/scratch -w /root/src/nipype/doc nipype/nipype_test:py35 /usr/bin/run_builddocs.sh && \
    docker run --rm -it -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh test_spm Linear /root/examples/ workflow3d && \
    docker run --rm -it -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh test_spm Linear /root/examples/ workflow4d
    ;;
  1)
    docker run --rm -it -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_dartel Linear /root/examples/ level1 && \
    docker run --rm -it -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_dartel Linear /root/examples/ l2pipeline
    ;;
  2)
    docker run --rm -it -e NIPYPE_NUMBER_OF_CPUS=4 -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py27 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /root/examples/ level1 && \
    docker run --rm -it -e NIPYPE_NUMBER_OF_CPUS=4 -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /root/examples/ l2pipeline
    ;;
  3)
    docker run --rm -it -e NIPYPE_NUMBER_OF_CPUS=4 -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /root/examples/ level1 && \
    docker run --rm -it -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_fsl_feeds Linear /root/examples/ l1pipeline && \
    docker run --rm -it -v $HOME/examples:/root/examples:ro -v $SCRATCH:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_fsl_reuse Linear /root/examples/ level1_workflow
    ;;
esac
