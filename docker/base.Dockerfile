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
FROM ubuntu:xenial-20161213
MAINTAINER The nipype developers https://github.com/nipy/nipype

# Set noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Installing requirements for freesurfer installation
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /opt
# Installing freesurfer -- do it first so that it is cached early
#-----------------------------------------------------------------------------
# 3. Install FreeSurfer v6.0 (minimized with reprozip):
#    https://github.com/freesurfer/freesurfer/issues/70
#-----------------------------------------------------------------------------
RUN curl -sSL https://dl.dropbox.com/s/pbaisn6m5qpi9uu/recon-all-freesurfer6-2.min.tgz?dl=0 | tar zx -C /opt
ENV FS_OVERRIDE=0 \
    OS=Linux \
    FSF_OUTPUT_FORMAT=nii.gz \
    FIX_VERTEX_AREA=\
    FREESURFER_HOME=/opt/freesurfer
ENV MNI_DIR=$FREESURFER_HOME/mni \
    SUBJECTS_DIR=$FREESURFER_HOME/subjects
ENV PERL5LIB=$MNI_DIR/share/perl5 \
    MNI_PERL5LIB=$MNI_DIR/share/perl5 \
    MINC_BIN_DIR=$MNI_DIR/bin \
    MINC_LIB_DIR=$MNI_DIR/lib \
    MNI_DATAPATH=$MNI_DIR/data
ENV PATH=$FREESURFER_HOME/bin:$FREESURFER_HOME/tktools:$MINC_BIN_DIR:$PATH
ENV FSL_DIR=/usr/share/fsl/5.0
RUN echo "cHJpbnRmICJrcnp5c3p0b2YuZ29yZ29sZXdza2lAZ21haWwuY29tXG41MTcyXG4gKkN2dW12RVYzelRmZ1xuRlM1Si8yYzFhZ2c0RVxuIiA+IC9vcHQvZnJlZXN1cmZlci9saWNlbnNlLnR4dAo=" | base64 -d | sh

# Enable neurodebian
COPY docker/files/neurodebian.gpg /etc/apt/neurodebian.gpg
RUN curl -sSL http://neuro.debian.net/lists/xenial.us-ca.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key add /etc/apt/neurodebian.gpg && \
    apt-key adv --refresh-keys --keyserver hkp://ha.pool.sks-keyservers.net 0xA5D32F012649A5A9 || true

# Installing general Debian utilities and Neurodebian packages (FSL, AFNI, git)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    fsl-core=5.0.9-1~nd+1+nd16.04+1 \
                    fsl-mni152-templates=5.0.7-2 \
                    afni=16.2.07~dfsg.1-2~nd16.04+1 \
                    bzip2 \
                    ca-certificates \
                    xvfb \
                    git=1:2.7.4-0ubuntu1 \
                    graphviz=2.38.0-12ubuntu2 \
                    unzip \
                    apt-utils \
                    fusefat \
                    make \
                    file \
                    # Added g++ to compile dipy in py3.6
                    g++=4:5.3.1-1ubuntu1 \
                    ruby=1:2.3.0+1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV FSLDIR=/usr/share/fsl/5.0 \
    FSLOUTPUTTYPE=NIFTI_GZ \
    FSLMULTIFILEQUIT=TRUE \
    POSSUMDIR=/usr/share/fsl/5.0 \
    LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH \
    FSLTCLSH=/usr/bin/tclsh \
    FSLWISH=/usr/bin/wish \
    AFNI_MODELPATH=/usr/lib/afni/models \
    AFNI_IMSAVE_WARNINGS=NO \
    AFNI_TTATLAS_DATASET=/usr/share/afni/atlases \
    AFNI_PLUGINPATH=/usr/lib/afni/plugins \
    PATH=/usr/lib/fsl/5.0:/usr/lib/afni/bin:$PATH

# Installing and setting up ANTs
RUN mkdir -p /opt/ants && \
    curl -sSL "https://dl.dropbox.com/s/2f4sui1z6lcgyek/ANTs-Linux-centos5_x86_64-v2.2.0-0740f91.tar.gz?dl=0" \
    | tar -zx -C /opt

ENV ANTSPATH=/opt/ants \
    PATH=$ANTSPATH:$PATH

# Installing and setting up c3d
RUN mkdir -p /opt/c3d && \
    curl -sSL "http://downloads.sourceforge.net/project/c3d/c3d/1.0.0/c3d-1.0.0-Linux-x86_64.tar.gz" \
    | tar -xzC /opt/c3d --strip-components 1

ENV C3DPATH=/opt/c3d/ \
    PATH=$C3DPATH/bin:$PATH

# Install fake-S3
ENV GEM_HOME /usr/lib/ruby/gems/2.3
ENV BUNDLE_PATH="$GEM_HOME" \
    BUNDLE_BIN="$GEM_HOME/bin" \
    BUNDLE_SILENCE_ROOT_WARNING=1 \
    BUNDLE_APP_CONFIG="$GEM_HOME"
ENV PATH $BUNDLE_BIN:$PATH
RUN mkdir -p "$GEM_HOME" "$BUNDLE_BIN" && \
    chmod 777 "$GEM_HOME" "$BUNDLE_BIN"

RUN gem install fakes3

# Install Matlab MCR: from the good old install_spm_mcr.sh of @chrisfilo
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

# Install SPM
RUN curl -sSL http://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/dev/spm12_r6472_Linux_R2015a.zip -o spm12.zip && \
    unzip spm12.zip && \
    rm -rf spm12.zip

ENV MATLABCMD="/opt/mcr/v85/toolbox/matlab" \
    SPMMCRCMD="/opt/spm12/run_spm12.sh /opt/mcr/v85/ script" \
    FORCE_SPMMCR=1

WORKDIR /work

