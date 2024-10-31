# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
vtkbase provides some helpers to use VTK through the tvtk package (mayavi)

Code using tvtk should import it through this module
"""

import os
from .. import logging

iflogger = logging.getLogger("nipype.interface")

# Check that VTK can be imported and get version
_vtk_version = None
try:
    import vtk

    _vtk_version = (
        vtk.vtkVersion.GetVTKMajorVersion(),
        vtk.vtkVersion.GetVTKMinorVersion(),
    )
except ImportError:
    iflogger.warning("VTK was not found")

# Ensure that tvtk is loaded with the appropriate ETS_TOOLKIT env var
old_ets = os.getenv("ETS_TOOLKIT")
os.environ["ETS_TOOLKIT"] = "null"
_have_tvtk = False
try:
    from tvtk.api import tvtk

    _have_tvtk = True
except ImportError:
    iflogger.warning("tvtk wasn't found")
    tvtk = None
finally:
    if old_ets is not None:
        os.environ["ETS_TOOLKIT"] = old_ets
    else:
        del os.environ["ETS_TOOLKIT"]


def vtk_version():
    """Get VTK version"""
    global _vtk_version
    return _vtk_version


def no_vtk():
    """Checks if VTK is installed and the python wrapper is functional"""
    global _vtk_version
    return _vtk_version is None


def no_tvtk():
    """Checks if tvtk was found"""
    global _have_tvtk
    return not _have_tvtk


def vtk_old():
    """Checks if VTK uses the old-style pipeline (VTK<6.0)"""
    global _vtk_version
    if _vtk_version is None:
        raise RuntimeError("VTK is not correctly installed.")
    return _vtk_version[0] < 6


def configure_input_data(obj, data):
    """
    Configure the input data for vtk pipeline object obj.
    Copied from latest version of mayavi
    """
    if vtk_old():
        obj.input = data
    else:
        obj.set_input_data(data)


def vtk_output(obj):
    """Configure the input data for vtk pipeline object obj."""
    if vtk_old():
        return obj.output
    return obj.get_output()
