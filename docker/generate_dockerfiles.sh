 #!/usr/bin/env bash

# kaczmarj/neurodocker:master pulled on September 13, 2017.
NEURODOCKER_IMAGE="kaczmarj/neurodocker:master"
# neurodebian/stretch-non-free:latest pulled on September 13, 2017.
BASE_IMAGE="neurodebian@sha256:b09c09faa34bca0ea096b9360ee5121e048594cb8e2d7744d7d546ade88a2996"
NIPYPE_BASE_IMAGE="kaczmarj/nipype:base"
PKG_MANAGER="apt"

# Save Dockerfiles relative to this path so that this script can be run from
# any directory. https://stackoverflow.com/a/246128/5666087
DIR="$(dirname "$0")"


function generate_base_dockerfile() {
  docker run --rm "$NEURODOCKER_IMAGE" generate \
  --base "$BASE_IMAGE" --pkg-manager "$PKG_MANAGER" \
  --label maintainer="The nipype developers https://github.com/nipy/nipype" \
  --spm version=12 matlab_version=R2017a \
  --afni version=latest \
  --freesurfer version=6.0.0 min=true \
  --run 'echo "cHJpbnRmICJrcnp5c3p0b2YuZ29yZ29sZXdza2lAZ21haWwuY29tXG41MTcyXG4gKkN2dW12RVYzelRmZ1xuRlM1Si8yYzFhZ2c0RVxuIiA+IC9vcHQvZnJlZXN1cmZlci9saWNlbnNlLnR4dAo=" | base64 -d | sh' \
  --install ants apt-utils bzip2 file fsl-core fsl-mni152-templates \
            fusefat g++ git graphviz make ruby unzip xvfb \
  --add-to-entrypoint "source /etc/fsl/fsl.sh" \
  --env ANTSPATH='/usr/lib/ants' PATH='/usr/lib/ants:$PATH' \
  --c3d version=1.0.0 \
  --instruction "RUN gem install fakes3" \
  --workdir /work \
  --no-check-urls > "$DIR/Dockerfile.base"
}


# The Dockerfile ADD/COPY instructions do not honor the current user, so the
# owner of the directories has to be manually changed to user neuro.
# See https://github.com/moby/moby/issues/6119 for more information on this
# behavior.
# Docker plans on changing this behavior by added a `--chown` flag to the
# ADD/COPY commands. See https://github.com/moby/moby/pull/34263.

function generate_main_dockerfile() {
  docker run --rm "$NEURODOCKER_IMAGE" generate \
  --base "$NIPYPE_BASE_IMAGE" --pkg-manager "$PKG_MANAGER" \
  --label maintainer="The nipype developers https://github.com/nipy/nipype" \
  --env MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  --user neuro \
  --miniconda env_name=neuro \
              add_to_path=true \
  --copy docker/files/run_builddocs.sh docker/files/run_examples.sh \
         docker/files/run_pytests.sh nipype/external/fsl_imglob.py /usr/bin/ \
  --copy . /src/nipype \
  --user root \
  --run "chmod 777 -R /src/nipype" \
  --user neuro \
  --arg PYTHON_VERSION_MAJOR=3 PYTHON_VERSION_MINOR=6 BUILD_DATE VCS_REF VERSION \
  --miniconda env_name=neuro \
              conda_install='python=${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}
                             icu=58.1 libxml2 libxslt matplotlib mkl numpy
                             pandas psutil scikit-learn scipy traits=4.6.0' \
              pip_opts="-e" \
              pip_install="/src/nipype[all]" \
  --label org.label-schema.build-date='$BUILD_DATE' \
          org.label-schema.name="NIPYPE" \
          org.label-schema.description="NIPYPE - Neuroimaging in Python: Pipelines and Interfaces" \
          org.label-schema.url="http://nipype.readthedocs.io" \
          org.label-schema.vcs-ref='$VCS_REF' \
          org.label-schema.vcs-url="https://github.com/nipy/nipype" \
          org.label-schema.version='$VERSION' \
          org.label-schema.schema-version="1.0" \
  --no-check-urls > "$DIR/../Dockerfile"
}


generate_base_dockerfile
generate_main_dockerfile
