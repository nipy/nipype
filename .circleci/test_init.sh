#!/bin/bash
#
# Source before running tests

# Setting      # $ help set
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

export DOCKER_IMAGE="nipype/nipype"

export SCRIPT_NAME=`basename $0`
