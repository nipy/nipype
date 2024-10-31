SETUP_REQUIRES="pip setuptools>=30.3.0 wheel"

# Minimum requirements
REQUIREMENTS="-r requirements.txt"
# Minimum versions of minimum requirements
MIN_REQUIREMENTS="-r min-requirements.txt"

# Numpy and scipy upload nightly/weekly/intermittent wheels
NIGHTLY_WHEELS="https://pypi.anaconda.org/scipy-wheels-nightly/simple"
STAGING_WHEELS="https://pypi.anaconda.org/multibuild-wheels-staging/simple"
PRE_PIP_FLAGS="--pre --extra-index-url $NIGHTLY_WHEELS --extra-index-url $STAGING_WHEELS"

for CONF in /etc/fsl/fsl.sh /etc/afni/afni.sh; do
    if [ -r $CONF ]; then source $CONF; fi
done

FSLOUTPUTTYPE=NIFTI_GZ
