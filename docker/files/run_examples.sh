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
sed -i -E "s/(source = ).*'/\1\/src\/nipype\/nipype/" /src/nipype/.coveragerc

if [ "$2" == "MultiProc" ]; then
	echo "concurrency = multiprocessing" >> /src/nipype/.coveragerc
fi

coverage run --rcfile=/src/nipype/.coveragerc /src/nipype/tools/run_examples.py $@
exit_code=$?

coverage xml -o ${WORKDIR}/smoketest_${example_id}.xml || true

exit $exit_code
