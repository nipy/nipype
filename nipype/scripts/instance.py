"""
Import lib and class meta programming utilities.
"""

import inspect
import importlib

from ..interfaces.base import Interface


def import_module(module_path):
    """Import any module to the global Python environment.
       The module_path argument specifies what module to import in
       absolute or relative terms (e.g. either pkg.mod or ..mod).
       If the name is specified in relative terms, then the package argument
       must be set to the name of the package which is to act as the anchor
       for resolving the package name (e.g. import_module('..mod',
       'pkg.subpkg') will import pkg.mod).

    Parameters
    ----------
    module_path: str
        Path to the module to be imported

    Returns
    -------
    The specified module will be inserted into sys.modules and returned.
    """
    try:
        mod = importlib.import_module(module_path)
    except:
        raise ImportError(f"Error when importing object {module_path}.")
    else:
        return mod


def list_interfaces(module):
    """Return a list with the names of the Interface subclasses inside
    the given module.
    """
    iface_names = []
    for k, v in sorted(module.__dict__.items()):
        if inspect.isclass(v) and issubclass(v, Interface):
            iface_names.append(k)
    return iface_names
