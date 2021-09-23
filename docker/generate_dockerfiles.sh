#!/usr/bin/env bash
#
# Generate base and main Dockerfiles for Nipype.

set -e

USAGE="usage: $(basename $0) [-h] [-b] [-m]"

function Help {
  cat <<USAGE
Generate base and/or main Dockerfiles for Nipype.

Usage:

$(basename $0) [-h] [-b] [-m]

Options:

    -h : display this help message and exit
    -b : generate base Dockerfile
    -m : generate main Dockerfile

USAGE
}

# No command-line options passed.
if [ -z "$1" ]; then
  echo "$USAGE"
  exit 1
fi

# Get command-line options.
# Used the antsRegistrationSyN.sh as an example.
# https://github.com/ANTsX/ANTs/blob/master/Scripts/antsRegistrationSyN.sh
while getopts "hbm" OPT
do
  case $OPT in
    h)
      Help
      exit 0
    ;;
    b)
      GENERATE_BASE="1"
    ;;
    m)
      GENERATE_MAIN="1"
    ;;
    \?)
      echo "$USAGE" >&2
      exit 1
    ;;
  esac
done

# neurodocker version 0.7.0
NEURODOCKER_IMAGE="repronim/neurodocker:0.7.0@sha256:5e93c12b96863ee6af5f15a889f8ead2f729a4e31c31daf31006c836f8176870"
# neurodebian:stretch-non-free pulled on September 19, 2018
BASE_IMAGE="neurodebian:nd110-non-free@sha256:da71cf9be42f2798bc93383e60c8f98a2dd53c7996ca7c250fc0056eed13afe8"

NIPYPE_BASE_IMAGE="nipype/nipype:base"
PKG_MANAGER="apt"
DIR="$(dirname "$0")"

function generate_base_dockerfile() {
  docker run --rm "$NEURODOCKER_IMAGE" generate docker \
    --base "$BASE_IMAGE" --pkg-manager "$PKG_MANAGER" \
    --label maintainer="The nipype developers https://github.com/nipy/nipype" \
    --spm12 version=r7219 \
    --env 'LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH' \
    --freesurfer version=6.0.0-min \
    --dcm2niix version=v1.0.20190902 method=source \
    --run 'echo "cHJpbnRmICJrcnp5c3p0b2YuZ29yZ29sZXdza2lAZ21haWwuY29tCjUxNzIKICpDdnVtdkVWM3pUZmcKRlM1Si8yYzFhZ2c0RQoiID4gL29wdC9mcmVlc3VyZmVyLTYuMC4wLW1pbi9saWNlbnNlLnR4dA==" | base64 -d | sh' \
    --install afni ants apt-utils bzip2 convert3d file fsl-core \
              fsl-mni152-templates fusefat g++ git graphviz make python ruby \
              unzip xvfb git-annex-standalone liblzma-dev \
    --add-to-entrypoint "source /etc/fsl/fsl.sh && source /etc/afni/afni.sh" \
    --env ANTSPATH='/usr/lib/ants' \
          PATH='/usr/lib/ants:$PATH' \
    --run "gem install fakes3" \
    > "$DIR/Dockerfile.base"
}


function generate_main_dockerfile() {
  docker run --rm "$NEURODOCKER_IMAGE" generate docker \
    --base "$NIPYPE_BASE_IMAGE" --pkg-manager "$PKG_MANAGER" \
    --label maintainer="The nipype developers https://github.com/nipy/nipype" \
    --env MKL_NUM_THREADS=1 \
          OMP_NUM_THREADS=1 \
    --arg PYTHON_VERSION_MAJOR=3 PYTHON_VERSION_MINOR=8 BUILD_DATE VCS_REF VERSION \
    --user neuro \
    --run 'git config --global user.name nipybot
           && git config --global user.email "nipybot@gmail.com"' \
    --workdir /home/neuro \
    --miniconda create_env=neuro \
                conda_install='python=${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}
                               libxml2 libxslt matplotlib mkl "numpy!=1.16.0" paramiko
                               pandas psutil scikit-learn scipy traits rdflib' \
                pip_install="pytest-xdist" \
                activate=true \
    --copy docker/files/run_builddocs.sh docker/files/run_examples.sh \
           docker/files/run_pytests.sh nipype/external/fsl_imglob.py /usr/bin/ \
    --copy . /src/nipype \
    --user root \
    --run 'chown -R neuro /src
  && chmod +x /usr/bin/fsl_imglob.py /usr/bin/run_*.sh
  && . /etc/fsl/fsl.sh
  && ln -sf /usr/bin/fsl_imglob.py ${FSLDIR}/bin/imglob
  && mkdir /work
  && chown neuro /work' \
    --user neuro \
    --miniconda use_env=neuro \
                pip_opts="-e" \
                pip_install="/src/nipype[all] https://github.com/bids-standard/pybids/tarball/0.7.0" \
    --miniconda use_env=neuro \
                pip_install='"niflow-nipype1-workflows>=0.4.0"' \
    --workdir /work \
    --label org.label-schema.build-date='$BUILD_DATE' \
            org.label-schema.name="NIPYPE" \
            org.label-schema.description="NIPYPE - Neuroimaging in Python: Pipelines and Interfaces" \
            org.label-schema.url="http://nipype.readthedocs.io" \
            org.label-schema.vcs-ref='$VCS_REF' \
            org.label-schema.vcs-url="https://github.com/nipy/nipype" \
            org.label-schema.version='$VERSION' \
            org.label-schema.schema-version="1.0"
}


if [ "$GENERATE_BASE" == 1 ]; then
  generate_base_dockerfile > "$DIR/Dockerfile.base"
fi
if [ "$GENERATE_MAIN" == 1 ]; then
  generate_main_dockerfile > "$DIR/../Dockerfile"
fi
