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


# neurodocker:master pulled on October 9, 2018
NEURODOCKER_IMAGE="kaczmarj/neurodocker@sha256:c5c10fc11cbd7efe18ac10d2370742b8ecb3588c3aa9b2c15ca7e18363bfa9dc"

# neurodebian:stretch-non-free pulled on October 9, 2018
BASE_IMAGE="neurodebian@sha256:7cd978427d7ad215834fee221d0536ed7825b3cddebc481eba2d792dfc2f7332"

NIPYPE_BASE_IMAGE="nipype/nipype:base"
PKG_MANAGER="apt"
DIR="$(dirname "$0")"

function generate_base_dockerfile() {
  docker run --rm "$NEURODOCKER_IMAGE" generate docker \
  --base "$BASE_IMAGE" --pkg-manager "$PKG_MANAGER" \
  --label maintainer="The nipype developers https://github.com/nipy/nipype" \
  --spm12 version=r7219 \
  --afni version=latest install_python2=true \
  --freesurfer version=6.0.0 min=true \
  --run 'echo "cHJpbnRmICJrcnp5c3p0b2YuZ29yZ29sZXdza2lAZ21haWwuY29tXG41MTcyXG4gKkN2dW12RVYzelRmZ1xuRlM1Si8yYzFhZ2c0RVxuIiA+IC9vcHQvZnJlZXN1cmZlci9saWNlbnNlLnR4dAo=" | base64 -d | sh' \
  --install ants apt-utils bzip2 convert3d file fsl-core fsl-mni152-templates \
            fusefat g++ git graphviz make ruby unzip xvfb \
  --add-to-entrypoint "source /etc/fsl/fsl.sh" \
  --env ANTSPATH='/usr/lib/ants' PATH='/usr/lib/ants:$PATH' \
  --run "gem install fakes3" > "$DIR/Dockerfile.base"
}


function generate_main_dockerfile() {
  docker run --rm "$NEURODOCKER_IMAGE" generate docker \
  --base "$NIPYPE_BASE_IMAGE" --pkg-manager "$PKG_MANAGER" \
  --label maintainer="The nipype developers https://github.com/nipy/nipype" \
  --env MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  --user neuro \
  --miniconda create_env=neuro \
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
  --arg PYTHON_VERSION_MAJOR=3 PYTHON_VERSION_MINOR=6 BUILD_DATE VCS_REF VERSION \
  --miniconda create_env=neuro \
              conda_install='python=${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}
                             icu=58.1 libxml2 libxslt matplotlib mkl numpy paramiko
                             pandas psutil scikit-learn scipy traits=4.6.0' \
              pip_opts="-e" \
              pip_install="/src/nipype[all]" \
  --miniconda create_env=neuro \
              pip_install="grabbit==0.1.2" \
  --run-bash "mkdir -p /src/pybids
         && curl -sSL --retry 5 https://github.com/INCF/pybids/tarball/0.6.5
         | tar -xz -C /src/pybids --strip-components 1
         && source activate neuro
         && pip install --no-cache-dir -e /src/pybids" \
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
