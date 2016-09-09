# -*- coding: utf-8 -*-
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
       for resolving the package name (e.g. import_module('..mod', 'pkg.subpkg')

       will import pkg.mod).

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
        return mod
    except:
        raise ImportError('Error when importing object {}.'.format(module_path))


def list_interfaces(module):
    """Return a list with the names of the Interface subclasses inside
    the given module.
    """
    iface_names = []
    for k, v in sorted(list(module.__dict__.items())):
        if inspect.isclass(v) and issubclass(v, Interface):
            iface_names.append(k)
    return iface_names


def instantiate_this(class_path, init_args):
    """Instantiates an object of the class in class_path with the given
    initialization arguments.

    Parameters
    ----------
    class_path: str
        String to the path of the class.

    init_args: dict
        Dictionary of the names and values of the initialization arguments
        to the class

    Return
    ------
    Instantiated object
    """
    try:
        cls = import_this(class_path)
        if init_args is None:
            return cls()
        else:
            return cls(**init_args)
    except:
        raise RuntimeError('Error instantiating class {} '
                           'with the arguments {}.'.format(class_path,
                                                           init_args))
