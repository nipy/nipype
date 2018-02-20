#!/bin/bash
set -e
set -x
set -u


TESTPATH=${1:-/src/nipype/nipype}
WORKDIR=${WORK:-/work}
PYTHON_VERSION=$( python -c "import sys; print('{}{}'.format(sys.version_info[0], sys.version_info[1]))" )

# Create necessary directories
mkdir -p ${WORKDIR}/tests ${WORKDIR}/crashfiles ${WORKDIR}/logs/py${PYTHON_VERSION}

# Create a nipype config file
mkdir -p ${HOME}/.nipype
echo '[logging]' > ${HOME}/.nipype/nipype.cfg
echo 'log_to_file = true' >> ${HOME}/.nipype/nipype.cfg
echo "log_directory = ${WORKDIR}/logs/py${PYTHON_VERSION}" >> ${HOME}/.nipype/nipype.cfg

echo '[execution]' >> ${HOME}/.nipype/nipype.cfg
echo 'crashfile_format = txt' >> ${HOME}/.nipype/nipype.cfg

if [[ "${NIPYPE_RESOURCE_MONITOR:-0}" == "1" ]]; then
    echo 'resource_monitor = true' >> ${HOME}/.nipype/nipype.cfg
fi

# Run tests using pytest
export COVERAGE_FILE=${WORKDIR}/tests/.coverage.py${PYTHON_VERSION}
py.test -v --junitxml=${WORKDIR}/tests/pytests_py${PYTHON_VERSION}.xml \
    --cov nipype --cov-config /src/nipype/.coveragerc \
    --cov-report xml:${WORKDIR}/tests/coverage_py${PYTHON_VERSION}.xml \
    -c ${TESTPATH}/pytest.ini ${TESTPATH}
exit_code=$?

# Collect crashfiles
find ${WORKDIR} -maxdepth 1 -name "crash-*" -exec mv {} ${WORKDIR}/crashfiles/ \;

echo "Unit tests finished with exit code ${exit_code}"
exit ${exit_code}
