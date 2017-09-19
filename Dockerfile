# Copyright (c) 2016, The developers of the Stanford CRN
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of crn_base nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


#
# Based on https://github.com/poldracklab/fmriprep/blob/9c92a3de9112f8ef1655b876de060a2ad336ffb0/Dockerfile
#
FROM nipype/base:latest
MAINTAINER The nipype developers https://github.com/nipy/nipype

ARG PYTHON_VERSION_MAJOR=3

# Installing and setting up miniconda
RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda${PYTHON_VERSION_MAJOR}-4.2.12-Linux-x86_64.sh && \
    bash Miniconda${PYTHON_VERSION_MAJOR}-4.2.12-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda${PYTHON_VERSION_MAJOR}-4.2.12-Linux-x86_64.sh

ENV PATH=/usr/local/miniconda/bin:$PATH \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    ACCEPT_INTEL_PYTHON_EULA=yes \
    MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1
# MKL/OMP_NUM_THREADS: unless otherwise specified, each process should
# only use one thread - nipype will handle parallelization

# Installing precomputed python packages
ARG PYTHON_VERSION_MINOR=6
RUN conda config --add channels conda-forge; sync && \
    conda config --set always_yes yes --set changeps1 no; sync && \
    conda install -y python=${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR} \
                     mkl \
                     numpy \
                     scipy \
                     scikit-learn \
                     matplotlib \
                     pandas \
                     libxml2 \
                     libxslt \
                     traits=4.6.0 \
                     psutil \
                     icu=58.1 && \
    sync;

# matplotlib cleanups: set default backend, precaching fonts
RUN sed -i 's/\(backend *: \).*$/\1Agg/g' /usr/local/miniconda/lib/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages/matplotlib/mpl-data/matplotlibrc && \
    python -c "from matplotlib import font_manager"

# Install CI scripts
COPY docker/files/run_* /usr/bin/
RUN chmod +x /usr/bin/run_*

# Replace imglob with a Python3 compatible version
COPY nipype/external/fsl_imglob.py /usr/bin/fsl_imglob.py
RUN rm -rf ${FSLDIR}/bin/imglob && \
    chmod +x /usr/bin/fsl_imglob.py && \
    ln -s /usr/bin/fsl_imglob.py ${FSLDIR}/bin/imglob

# Installing dev requirements (packages that are not in pypi)
WORKDIR /src/
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && \
    rm -rf ~/.cache/pip

# Installing nipype
COPY . /src/nipype
RUN cd /src/nipype && \
    pip install -e .[all] && \
    rm -rf ~/.cache/pip

WORKDIR /work/

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="NIPYPE" \
      org.label-schema.description="NIPYPE - Neuroimaging in Python: Pipelines and Interfaces" \
      org.label-schema.url="http://nipype.readthedocs.io" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/nipy/nipype" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"
