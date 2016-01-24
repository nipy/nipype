# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous utility functions
"""

from future import standard_library
standard_library.install_aliases()
from builtins import next
from pickle import dumps, loads
import inspect

from distutils.version import LooseVersion
import numpy as np
from textwrap import dedent
import sys
import re
from collections import Iterator

from ..external.six import string_types


def human_order_sorted(l):
    """Sorts string in human order (i.e. 'stat10' will go after 'stat2')"""
    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        if isinstance(text, tuple):
            text = text[0]
        return [atoi(c) for c in re.split('(\d+)', text)]

    return sorted(l, key=natural_keys)


def trim(docstring, marker=None):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            # replace existing REST marker with doc level marker
            stripped = line.lstrip().strip().rstrip()
            if marker is not None and stripped and \
               all([s == stripped[0] for s in stripped]) and \
               stripped[0] not in [':']:
                line = line.replace(stripped[0], marker)
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


def getsource(function):
    """Returns the source code of a function"""
    src = dedent(inspect.getsource(function))
    return src


def create_function_from_source(function_source, imports=None):
    """Return a function object from a function source

    Parameters
    ----------
    function_source : pickled string
        string in pickled form defining a function
    imports : list of strings
        list of import statements in string form that allow the function
        to be executed in an otherwise empty namespace
    """
    ns = {}
    import_keys = []
    try:
        if imports is not None:
            for statement in imports:
                exec(statement, ns)
            import_keys = list(ns.keys())
        exec(function_source, ns)

    except Exception as msg:
        msg = str(msg) + '\nError executing function:\n %s\n' % function_source
        msg += '\n'.join(["Functions in connection strings have to be standalone.",
                          "They cannot be declared either interactively or inside",
                          "another function or inline in the connect string. Any",
                          "imports should be done inside the function"
                          ])
        raise RuntimeError(msg)
    ns_funcs = list(set(ns) - set(import_keys + ['__builtins__']))
    assert len(ns_funcs) == 1, "Function or inputs are ill-defined"
    funcname = ns_funcs[0]
    func = ns[funcname]
    return func


def find_indices(condition):
    "Return the indices where ravel(condition) is true"
    res, = np.nonzero(np.ravel(condition))
    return res


def is_container(item):
    """Checks if item is a container (list, tuple, dict, set)

    Parameters
    ----------
    item : object
        object to check for .__iter__

    Returns
    -------
    output : Boolean
        True if container
        False if not (eg string)
    """
    if isinstance(item, string_types):
        return False
    elif hasattr(item, '__iter__'):
        return True
    else:
        return False


def container_to_string(cont):
    """Convert a container to a command line string.

    Elements of the container are joined with a space between them,
    suitable for a command line parameter.

    If the container `cont` is only a sequence, like a string and not a
    container, it is returned unmodified.

    Parameters
    ----------
    cont : container
       A container object like a list, tuple, dict, or a set.

    Returns
    -------
    cont_str : string
        Container elements joined into a string.

    """
    if hasattr(cont, '__iter__') and not isinstance(cont, string_types):
        return str(' '.join(cont))

    return str(cont)


# Dependency checks.  Copied this from Nipy, with some modificiations
# (added app as a parameter).
def package_check(pkg_name, version=None, app=None, checker=LooseVersion,
                  exc_failed_import=ImportError,
                  exc_failed_check=RuntimeError):
    """Check that the minimal version of the required package is installed.

    Parameters
    ----------
    pkg_name : string
        Name of the required package.
    version : string, optional
        Minimal version number for required package.
    app : string, optional
        Application that is performing the check.  For instance, the
        name of the tutorial being executed that depends on specific
        packages.  Default is *Nipype*.
    checker : object, optional
        The class that will perform the version checking.  Default is
        distutils.version.LooseVersion.
    exc_failed_import : Exception, optional
        Class of the exception to be thrown if import failed.
    exc_failed_check : Exception, optional
        Class of the exception to be thrown if version check failed.

    Examples
    --------
    package_check('numpy', '1.3')
    package_check('networkx', '1.0', 'tutorial1')

    """

    if app:
        msg = '%s requires %s' % (app, pkg_name)
    else:
        msg = 'Nipype requires %s' % pkg_name
    if version:
        msg += ' with version >= %s' % (version,)
    try:
        mod = __import__(pkg_name)
    except ImportError:
        raise exc_failed_import(msg)
    if not version:
        return
    try:
        have_version = mod.__version__
    except AttributeError:
        raise exc_failed_check('Cannot find version for %s' % pkg_name)
    if checker(have_version) < checker(version):
        raise exc_failed_check(msg)


def str2bool(v):
    if isinstance(v, bool):
        return v
    lower = v.lower()
    if lower in ("yes", "true", "t", "1"):
        return True
    elif lower in ("no", "false", "n", "f", "0"):
        return False
    else:
        raise ValueError("%s cannot be converted to bool" % v)


def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])


def unflatten(in_list, prev_structure):
    if not isinstance(in_list, Iterator):
        in_list = iter(in_list)

    if not isinstance(prev_structure, list):
        return next(in_list)
    else:
        out = []
        for item in prev_structure:
            out.append(unflatten(in_list, item))
        return out
