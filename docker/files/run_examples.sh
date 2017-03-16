#!/bin/bash
set -e
set -x
set -u

WORKDIR=${WORK:-/work}
arr=$@
tmp_var=$( IFS=$' '; echo "${arr[*]}" )
example_id=${tmp_var//[^A-Za-z0-9_-]/_}

mkdir -p ${HOME}/.nipype ${WORKDIR}/logs/example_${example_id}
echo "[logging]" > ${HOME}/.nipype/nipype.cfg
echo "workflow_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "interface_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "filemanip_level = DEBUG" >> ${HOME}/.nipype/nipype.cfg
echo "log_to_file = true" >> ${HOME}/.nipype/nipype.cfg
echo "log_directory = ${WORKDIR}/logs/example_${example_id}" >> ${HOME}/.nipype/nipype.cfg

# Set up coverage
echo "[run]" >> .coveragerc
echo "branch = True" >> .coveragerc
echo "source = /src/nipype" >> .coveragerc
echo "include = */nipype/*" >> .coveragerc
echo "omit =" >> .coveragerc
echo "    */nipype/external/*" >> .coveragerc
echo "    */nipype/fixes/*" >> .coveragerc
echo "    */setup.py" >> .coveragerc


parallel=""
if [ "$2" == "MultiProc" ]; then
	parallel="--concurrency=multiprocessing"
fi

coverage run ${parallel} /src/nipype/tools/run_examples.py $@
test_exit=$?
coverage xml -o "${WORKDIR}/smoketest_${example_id}.xml"

exit $test_exit