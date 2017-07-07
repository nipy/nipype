#!/bin/bash
set -e
set -x
set -u


TESTPATH=${1:-/src/nipype/}
WORKDIR=${WORK:-/work}
PYTHON_VERSION=$( python -c "import sys; print('{}{}'.format(sys.version_info[0], sys.version_info[1]))" )

# Create necessary directories
mkdir -p ${WORKDIR}/tests ${WORKDIR}/crashfiles ${WORKDIR}/logs/py${PYTHON_VERSION}

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

# Run tests using pytest
export COVERAGE_FILE=${WORKDIR}/tests/.coverage.py${PYTHON_VERSION}
py.test -v --junitxml=${WORKDIR}/tests/pytests_py${PYTHON_VERSION}.xml --cov nipype --cov-config /src/nipype/.coveragerc --cov-report xml:${WORKDIR}/tests/coverage_py${PYTHON_VERSION}.xml ${TESTPATH}
exit_code=$?

# Workaround: run here the profiler tests in python 3
if [[ "${PYTHON_VERSION}" -ge "30" ]]; then
    echo '[execution]' >> ${HOME}/.nipype/nipype.cfg
    echo 'profile_runtime = true' >> ${HOME}/.nipype/nipype.cfg
    export COVERAGE_FILE=${WORKDIR}/tests/.coverage.py${PYTHON_VERSION}_extra
    py.test -v --junitxml=${WORKDIR}/tests/pytests_py${PYTHON_VERSION}_extra.xml --cov nipype --cov-report xml:${WORKDIR}/tests/coverage_py${PYTHON_VERSION}_extra.xml /src/nipype/nipype/interfaces/tests/test_runtime_profiler.py /src/nipype/nipype/pipeline/plugins/tests/test_multiproc*.py
    exit_code=$(( $exit_code + $? ))
fi

# Collect crashfiles
find ${WORKDIR} -name "crash-*" -maxdepth 1 -exec mv {} ${WORKDIR}/crashfiles/ \;

echo "Unit tests finished with exit code ${exit_code}"
exit ${exit_code}

