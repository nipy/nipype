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

FROM nipype/testnipype:latest
MAINTAINER Stanford Center for Reproducible Neuroscience <crn.poldracklab@gmail.com>

# Preparations
RUN ln -snf /bin/bash /bin/sh
WORKDIR /root

# Install fsl-feeds and the nipype-tutorial data
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y fsl-feeds && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir -p ~/examples/ && \
    ln -sf /usr/share/fsl-feeds/ ~/examples/feeds && \
    curl -sSL "https://dl.dropbox.com/s/jzgq2nupxyz36bp/nipype-tutorial.tar.bz2" -o nipype-tutorial.tar.bz2 && \
    tar jxf nipype-tutorial.tar.bz2 -C /root/examples

# RUN curl -sSL "http://fsl.fmrib.ox.ac.uk/fslcourse/fdt1.tar.gz" -o fdt1.tar.gz && \
#     curl -sSL "http://fsl.fmrib.ox.ac.uk/fslcourse/fdt2.tar.gz" -o fdt2.tar.gz && \
#     curl -sSL "http://fsl.fmrib.ox.ac.uk/fslcourse/tbss.tar.gz" -o tbss.tar.gz && \
#     mkdir ~/examples/fsl_course_data && \
#     echo 'Untarring fsl course data...' && \
#     tar zxf fdt1.tar.gz -C ~/examples/fsl_course_data && \
#     tar zxf fdt2.tar.gz -C ~/examples/fsl_course_data && \
#     tar zxf tbss.tar.gz -C ~/examples/fsl_course_data && \
#     echo 'export FSL_COURSE_DATA=/root/examples/fsl_course_data' >> /etc/profile.d/nipype_data.sh
# ENV FSL_COURSE_DATA /root/examples/fsl_course_data
# RUN echo 'source /etc/profile.d/nipype_data.sh' >> /etc/bash.bashrc

CMD ["/bin/bash"]
