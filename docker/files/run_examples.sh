#!/bin/bash
set -e
set -x
set -u

WORKDIR=${WORKDIR:-/work}
arr=$@
tmp_var=$( IFS=$' '; echo "${arr[*]}" )
example_id=${tmp_var//[^A-Za-z0-9_-]/_}

mkdir -p ${HOME}/.nipype ${WORKDIR}/logs/example_${example_id} ${WORKDIR}/tests ${WORKDIR}/crashfiles
echo "[logging]" > ${HOME}/.nipype/nipype.cfg
echo "workflow_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "interface_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "utils_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "log_to_file = true" >> ${HOME}/.nipype/nipype.cfg
echo "log_directory = ${WORKDIR}/logs/example_${example_id}" >> ${HOME}/.nipype/nipype.cfg

echo '[execution]' >> ${HOME}/.nipype/nipype.cfg
echo 'crashfile_format = txt' >> ${HOME}/.nipype/nipype.cfg

if [[ "${NIPYPE_RESOURCE_MONITOR:-0}" == "1" ]]; then
    echo '[monitoring]' >> ${HOME}/.nipype/nipype.cfg
    echo 'enabled = true' >> ${HOME}/.nipype/nipype.cfg
    echo 'sample_frequency = 3' >> ${HOME}/.nipype/nipype.cfg
fi

# Set up coverage
export COVERAGE_FILE=${WORKDIR}/tests/.coverage.${example_id}
if [ "$2" == "MultiProc" ]; then
	echo "concurrency = multiprocessing" >> /src/nipype/.coveragerc
fi

coverage run /src/nipype/tools/run_examples.py $@
exit_code=$?

if [[ "${NIPYPE_RESOURCE_MONITOR:-0}" == "1" ]]; then
	cp resource_monitor.json 2>/dev/null ${WORKDIR}/logs/example_${example_id}/ || :
fi
# Collect crashfiles and generate xml report
coverage xml -o ${WORKDIR}/tests/smoketest_${example_id}.xml
find /work -maxdepth 1 -name "crash-*" -exec mv {} ${WORKDIR}/crashfiles/ \;
exit $exit_code
