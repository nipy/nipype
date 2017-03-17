#!/bin/bash
set -e
set -x
set -u

WORKDIR=${WORK:-/work}
arr=$@
tmp_var=$( IFS=$' '; echo "${arr[*]}" )
example_id=${tmp_var//[^A-Za-z0-9_-]/_}

mkdir -p ${HOME}/.nipype ${WORKDIR}/logs/example_${example_id} ${WORKDIR}/tests ${WORKDIR}/crashfiles
echo "[logging]" > ${HOME}/.nipype/nipype.cfg
echo "workflow_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "interface_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "filemanip_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "log_to_file = true" >> ${HOME}/.nipype/nipype.cfg
echo "log_directory = ${WORKDIR}/logs/example_${example_id}" >> ${HOME}/.nipype/nipype.cfg

# Set up coverage
export COVERAGE_FILE=${WORKDIR}/tests/.coverage.${example_id}
if [ "$2" == "MultiProc" ]; then
	echo "concurrency = multiprocessing" >> /src/nipype/.coveragerc
fi

coverage run /src/nipype/tools/run_examples.py $@
exit_code=$?

# Collect crashfiles and generate xml report
coverage xml -o ${WORKDIR}/tests/smoketest_${example_id}.xml
find /work -name "crash-*" -maxdepth 1 -exec mv {} ${WORKDIR}/crashfiles/ \;
exit $exit_code

