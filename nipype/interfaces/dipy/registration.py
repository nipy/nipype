from distutils.version import LooseVersion
from ... import logging
from .base import HAVE_DIPY, dipy_version, dipy_to_nipype_interface, get_dipy_workflows

IFLOGGER = logging.getLogger("nipype.interface")


if HAVE_DIPY and LooseVersion(dipy_version()) >= LooseVersion("0.15"):
    from dipy.workflows import align

    l_wkflw = get_dipy_workflows(align)
    for name, obj in l_wkflw:
        new_name = name.replace("Flow", "")
        globals()[new_name] = dipy_to_nipype_interface(new_name, obj)
    del l_wkflw

else:
    IFLOGGER.info(
        "We advise you to upgrade DIPY version. This upgrade will"
        " open access to more function"
    )
