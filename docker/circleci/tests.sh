#!/bin/bash

set -o nounset
set -o xtrace

export CODECOV_TOKEN=ac172a50-8e66-42e5-8822-5373fcf54686

if [ "${CIRCLE_NODE_TOTAL:-}" != "4" ]; then
  echo "These tests were designed to be run at 4x parallelism."
  exit 1
fi

# These tests are manually balanced based on previous build timings. 
# They may need to be rebalanced in the future.
case ${CIRCLE_NODE_INDEX} in
  0)
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_dartel Linear /root/examples/ level1
    ;;
  1)
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_dartel Linear /root/examples/ l2pipeline
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh test_spm Linear /root/examples/ workflow3d
    time docker run -v /etc/localtime:/etc/localtime:ro -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /root/src/nipype nipype/nipype_test:py35 /usr/bin/run_pytests.sh py35
    time docker run -v /etc/localtime:/etc/localtime:ro -e NIPYPE_NUMBER_OF_CPUS=4 -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py27 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /root/examples/ level1
    ;;
  2)
    time docker run -v /etc/localtime:/etc/localtime:ro -e NIPYPE_NUMBER_OF_CPUS=4 -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /root/examples/ l2pipeline
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/scratch:/scratch -w /root/src/nipype/doc nipype/nipype_test:py35 /usr/bin/run_builddocs.sh
    time docker run -v /etc/localtime:/etc/localtime:ro -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /root/src/nipype nipype/nipype_test:py27 /usr/bin/run_pytests.sh py27
    time docker run -v /etc/localtime:/etc/localtime:ro -e NIPYPE_NUMBER_OF_CPUS=4 -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_spm_nested MultiProc /root/examples/ level1
    ;;
  3)
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh test_spm Linear /root/examples/ workflow4d
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_fsl_feeds Linear /root/examples/ l1pipeline
    time docker run -v /etc/localtime:/etc/localtime:ro -v ~/examples:/root/examples:ro -v ~/scratch:/scratch -w /scratch nipype/nipype_test:py35 /usr/bin/run_examples.sh fmri_fsl_reuse Linear /root/examples/ level1_workflow
    ;;
esac

# Put the artifacts in place
bash docker/circleci/teardown.sh

# Send coverage data to codecov.io
curl -so codecov.io https://codecov.io/bash
chmod 755 codecov.io
find "${CIRCLE_TEST_REPORTS}/pytest" -name 'coverage*.xml' -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F unittests
find "${CIRCLE_TEST_REPORTS}/pytest" -name 'smoketests*.xml' -print0 | \
  xargs -0 -I file ./codecov.io -f file -t "${CODECOV_TOKEN}" -F smoketests



