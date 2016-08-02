# Copyright (c) 2016, The developers of nipype
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

FROM neurodebian:latest
MAINTAINER Nipype developers

# Preparations
RUN ln -snf /bin/bash /bin/sh
ARG DEBIAN_FRONTEND=noninteractive

RUN sed -i -e 's,main$,main contrib non-free,g' /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-get -y update && \
    apt-get install -y curl \
                       git \
                       xvfb \
                       bzip2 \
                       unzip \
                       apt-utils \
                       fusefat \
                       graphviz \
                       fsl-core && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    echo ". /etc/fsl/fsl.sh" >> /etc/bash.bashrc

ENV FSLDIR=/usr/share/fsl/5.0
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=/usr/lib/fsl/5.0:$PATH
ENV FSLMULTIFILEQUIT=TRUE
ENV POSSUMDIR=/usr/share/fsl/5.0
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish

# Install Matlab: from the good old install_spm_mcr.sh of @chrisfilo
WORKDIR /opt

RUN echo "destinationFolder=/opt/mcr" > mcr_options.txt && \
    echo "agreeToLicense=yes" >> mcr_options.txt && \
    echo "outputFile=/tmp/matlabinstall_log" >> mcr_options.txt && \
    echo "mode=silent" >> mcr_options.txt && \
    mkdir -p matlab_installer && \
    curl -sSL http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip \
         -o matlab_installer/installer.zip && \
    unzip matlab_installer/installer.zip -d matlab_installer/ && \
    matlab_installer/install -inputFile mcr_options.txt && \
    rm -rf matlab_installer mcr_options.txt

ENV SPMMCRCMD "/opt/spm12/run_spm12.sh /opt/mcr/v85/ script"
ENV FORCE_SPMMCR 1

# Install SPM
RUN curl -sSL http://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/dev/spm12_r6472_Linux_R2015a.zip -o spm12.zip && \
    unzip spm12.zip && \
    rm -rf spm12.zip

CMD ["/bin/bash"]

