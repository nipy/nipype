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

FROM ubuntu:vivid
MAINTAINER Stanford Center for Reproducible Neuroscience <crn.poldracklab@gmail.com>

# Preparations
RUN ln -snf /bin/bash /bin/sh
ARG DEBIAN_FRONTEND=noninteractive

# Update packages and install the minimal set of tools
RUN apt-get update && \
    apt-get install -y curl \
                       git \
                       xvfb \
                       bzip2 \
                       unzip \
                       apt-utils \
                       gfortran \
                       fusefat \
                       liblapack-dev \
                       libblas-dev \
                       libatlas-dev \
                       libatlas-base-dev \
                       libblas3 \
                       libblas-common \
                       libopenblas-dev \
                       libxml2-dev \
                       libxslt1-dev \
                       libfreetype6-dev \
                       libpng12-dev \
                       libqhull-dev \
                       libxft-dev \
                       libjpeg-dev \
                       libyaml-dev \
                       graphviz


# Install ANTs
RUN mkdir -p /opt/ants && \
    curl -sSL "https://2a353b13e8d2d9ac21ce543b7064482f771ce658.googledrive.com/host/0BxI12kyv2olZVFhUcGVpYWF3R3c/ANTs-Linux_Ubuntu14.04.tar.bz2" \
    | tar -xjC /opt/ants --strip-components 1
ENV ANTSPATH /opt/ants
ENV PATH $ANTSPATH:$PATH

# Enable neurodebian
RUN curl -sSL http://neuro.debian.net/lists/vivid.de-m.full | tee /etc/apt/sources.list.d/neurodebian.sources.list && \
    curl -sSL http://neuro.debian.net/lists/vivid.us-tn.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key adv --recv-keys --keyserver hkp://pgp.mit.edu:80 0xA5D32F012649A5A9 && \
    apt-get update && \
    apt-get install -y fsl-core afni

RUN echo '#!/bin/bash' > /etc/profile.d/nipype_deps.sh && \
    echo 'export ANTSPATH=/opt/ants' >> /etc/profile.d/nipype_deps.sh && \
    echo 'export PATH=$ANTSPATH:$PATH' >> /etc/profile.d/nipype_deps.sh && \
    echo 'source /etc/fsl/fsl.sh' >> /etc/profile.d/nipype_deps.sh && \
    echo 'source /etc/afni/afni.sh' >> /etc/profile.d/nipype_deps.sh
    
# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Matlab: from the good old install_spm_mcr.sh of @chrisfilo
WORKDIR /root

RUN echo "destinationFolder=/root/mcr" > mcr_options.txt && \
    echo "agreeToLicense=yes" >> mcr_options.txt && \
    echo "outputFile=/tmp/matlabinstall_log" >> mcr_options.txt && \
    echo "mode=silent" >> mcr_options.txt && \
    mkdir -p matlab_installer && \
    curl -sSL http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip \
         -o matlab_installer/installer.zip && \
    unzip matlab_installer/installer.zip -d matlab_installer/ && \
    matlab_installer/install -inputFile mcr_options.txt && \
    rm -rf matlab_installer mcr_options.txt && \
#    echo 'export LD_LIBRARY_PATH=/root/mcr/v85/runtime/glnxa64:/root/mcr/v85/bin/glnxa64:/root/mcr/v85/sys/os/glnxa64:$LD_LIBRARY_PATH' >> /etc/profile.d/nipype_deps.sh && \
    echo 'export SPMMCRCMD="/root/spm12/run_spm12.sh /root/mcr/v85/ script"' >> /etc/profile.d/nipype_deps.sh && \ 
    echo 'export FORCE_SPMMCR=1' >> /etc/profile.d/nipype_deps.sh

ENV SPMMCRCMD "/root/spm12/run_spm12.sh /root/mcr/v85/ script"
ENV FORCE_SPMMCR 1

# Install SPM
RUN curl -sSL http://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/dev/spm12_r6472_Linux_R2015a.zip -o spm12.zip && \
    unzip spm12.zip && \
    rm -rf spm12.zip

RUN echo "source /etc/profile.d/nipype_deps.sh" >> /etc/bash.bashrc

CMD ["/bin/bash"]

