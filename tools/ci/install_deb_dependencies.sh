#!/bin/bash

echo "Installing NeuroDebian dependencies"

set -eu

echo "INSTALL_DEB_DEPENDENCIES = $INSTALL_DEB_DEPENDENCIES"

if $INSTALL_DEB_DEPENDENCIES; then
    bash <(wget -q -O- http://neuro.debian.net/_files/neurodebian-travis.sh)
    sudo apt update
    sudo apt install -y -qq fsl afni elastix fsl-atlases xvfb fusefat graphviz
fi
