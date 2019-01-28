
from distutils.version import LooseVersion
from ... import logging
from .base import HAVE_DIPY, dipy_version, dipy_to_nipype_interface

IFLOGGER = logging.getLogger('nipype.interface')

if HAVE_DIPY and LooseVersion(dipy_version()) >= LooseVersion('0.15'):

    from dipy.workflows.align import ResliceFlow, SlrWithQbxFlow

    Reslice = dipy_to_nipype_interface("Reslice", ResliceFlow)
    StreamlineRegistration = dipy_to_nipype_interface("StreamlineRegistration",
                                                      SlrWithQbxFlow)

else:
    IFLOGGER.info("We advise you to upgrade DIPY version. This upgrade will"
                  " activate Reslice, StreamlineRegistration.")
