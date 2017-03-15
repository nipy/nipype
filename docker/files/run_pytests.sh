#!/bin/bash
set -e
set -x
set -u

WORKDIR=${WORK:-/work}
PYTHON_VERSION=$( python -c "import sys; print('{}{}'.format(sys.version_info[0], sys.version_info[1]))" )

# Create necessary directories
mkdir -p ${WORKDIR}/crashfiles ${WORKDIR}/logs/py${PYTHON_VERSION}

# Create a nipype config file
mkdir -p ${HOME}/.nipype
echo '[logging]' > ${HOME}/.nipype/nipype.cfg
echo 'log_to_file = true' >> ${HOME}/.nipype/nipype.cfg
echo "log_directory = ${WORKDIR}/logs/py${PYTHON_VERSION}" >> ${HOME}/.nipype/nipype.cfg

# Enable profile_runtime tests only for python 2.7
if [[ "${PYTHON_VERSION}" -lt "30" ]]; then
    echo '[execution]' >> ${HOME}/.nipype/nipype.cfg
    echo 'profile_runtime = true' >> ${HOME}/.nipype/nipype.cfg
fi

cd /src/nipype/
make clean
# Run tests using pytest
py.test -n ${CIRCLE_NCPUS:-4} --doctest-modules --junitxml=${WORKDIR}/pytests_py${PYTHON_VERSION}.xml --cov-report xml:${WORKDIR}/coverage_py${PYTHON_VERSION}.xml --cov=nipype nipype


# Workaround: run here the profiler tests in python 3
if [[ "${PYTHON_VERSION}" -ge "30" ]]; then
    echo '[execution]' >> ${HOME}/.nipype/nipype.cfg
    echo 'profile_runtime = true' >> ${HOME}/.nipype/nipype.cfg
    py.test -n ${CIRCLE_NCPUS:-4} --junitxml=${WORKDIR}/pytests_py${PYTHON_VERSION}_profiler.xml --cov-report xml:${WORKDIR}/coverage_py${PYTHON_VERSION}_profiler.xml --cov=nipype nipype/interfaces/tests/test_runtime_profiler.py
    py.test -n ${CIRCLE_NCPUS:-4} --junitxml=${WORKDIR}/pytests_py${PYTHON_VERSION}_multiproc.xml --cov-report xml:${WORKDIR}/coverage_py${PYTHON_VERSION}_multiproc.xml --cov=nipype nipype/pipeline/plugins/tests/test_multiproc*.py
fi

# Copy crashfiles to scratch
find /src/nipype/ -name "crash-*" -exec cp {} ${WORKDIR}/crashfiles/ \;
