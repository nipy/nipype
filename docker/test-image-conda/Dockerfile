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

FROM nipype/testbase
MAINTAINER Stanford Center for Reproducible Neuroscience <crn.poldracklab@gmail.com>

# Preparations
RUN ln -snf /bin/bash /bin/sh
WORKDIR /root

# Install miniconda
RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh && \
    /bin/bash Miniconda-latest-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda-latest-Linux-x86_64.sh && \
    echo '#!/bin/bash' >> /etc/profile.d/anaconda.sh && \
    echo 'export PATH=/usr/local/miniconda/bin:$PATH' >> /etc/profile.d/anaconda.sh

ENV PATH /usr/local/miniconda/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# Create conda environment
RUN conda create -y -n nipypetests-2.7 lockfile && \
    echo '#!/bin/bash' >> /etc/profile.d/nipype.sh && \
    echo '#!/bin/bash' >> /etc/bashrc && \
    echo 'source activate nipypetests-2.7' >> /etc/profile.d/nipype.sh && \
    echo 'source activate nipypetests-2.7' >> /etc/bashrc

# Install pip
RUN source activate nipypetests-2.7 && \
    pip install --upgrade pip && \
    pip install nose && \
    pip install numpy && \
    pip install scipy && \
    pip install pandas && \
    pip install matplotlib && \
    pip install xvfbwrapper && \
    python -c "from matplotlib import font_manager"

# Create conda environment
RUN conda create -y -n nipypetests-3.4 lockfile python=3.4 

# Install pip
RUN source activate nipypetests-3.4 && \
    pip install --upgrade pip && \
    pip install nose && \
    pip install numpy && \
    pip install scipy && \
    pip install pandas && \
    pip install matplotlib && \
    pip install xvfbwrapper && \
    python -c "from matplotlib import font_manager"

# Create conda environment
RUN conda create -y -n nipypetests-3.5 lockfile python=3.5

# Install pip
RUN source activate nipypetests-3.5 && \
    pip install --upgrade pip && \
    pip install nose && \
    pip install numpy && \
    pip install scipy && \
    pip install pandas && \
    pip install matplotlib && \
    pip install xvfbwrapper && \
    python -c "from matplotlib import font_manager"



CMD ["/bin/bash"]
