# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous utility functions
"""
import os
import sys
import re
from collections import Iterator
from warnings import warn

from distutils.version import LooseVersion

import numpy as np

try:
    from textwrap import indent as textwrap_indent
except ImportError:

    def textwrap_indent(text, prefix):
        """ A textwrap.indent replacement for Python < 3.3 """
        if not prefix:
            return text
        splittext = text.splitlines(True)
        return prefix + prefix.join(splittext)


def human_order_sorted(l):
    """Sorts string in human order (i.e. 'stat10' will go after 'stat2')"""

    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        if isinstance(text, tuple):
            text = text[0]
        return [atoi(c) for c in re.split("(\d+)", text)]

    return sorted(l, key=natural_keys)


def trim(docstring, marker=None):
    if isinstance(docstring, bytes):
        docstring = str(docstring, "utf-8")

    if not docstring:
        return ""
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
            if (
                marker is not None
                and stripped
                and all([s == stripped[0] for s in stripped])
                and stripped[0] not in [":"]
            ):
                line = line.replace(stripped[0], marker)
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return "\n".join(trimmed)


def find_indices(condition):
    "Return the indices where ravel(condition) is true"
    (res,) = np.nonzero(np.ravel(condition))
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
    if isinstance(item, str):
        return False
    elif hasattr(item, "__iter__"):
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
    if hasattr(cont, "__iter__") and not isinstance(cont, str):
        cont = " ".join(cont)
    return str(cont)


# Dependency checks.  Copied this from Nipy, with some modificiations
# (added app as a parameter).
def package_check(
    pkg_name,
    version=None,
    app=None,
    checker=LooseVersion,
    exc_failed_import=ImportError,
    exc_failed_check=RuntimeError,
):
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
    package_check('scipy', '0.7', 'tutorial1')

    """

    if app:
        msg = "%s requires %s" % (app, pkg_name)
    else:
        msg = "Nipype requires %s" % pkg_name
    if version:
        msg += " with version >= %s" % (version,)
    try:
        mod = __import__(pkg_name)
    except ImportError as e:
        raise exc_failed_import(msg) from e
    if not version:
        return
    try:
        have_version = mod.__version__
    except AttributeError as e:
        raise exc_failed_check("Cannot find version for %s" % pkg_name) from e
    if checker(have_version) < checker(version):
        raise exc_failed_check(msg)


def str2bool(v):
    """
    Convert strings (and bytearrays) to boolean values

    >>> all([str2bool(v) for v in (True, "yes", "true",
    ...      "y", "t", "Yes", "True", "1", "on", "On")])
    True
    >>> all([str2bool(v.encode('utf-8'))
    ...      for v in ("yes", "true", "y", "t", "1", "Yes", "on", "On")])
    True
    >>> any([str2bool(v) for v in (False, "no", "false", "n", "f",
    ...      "False", "0", "off", "Off")])
    False
    >>> any([str2bool(v.encode('utf-8'))
    ...      for v in ("no", "false", "n", "f", "0", "off", "Off")])
    False
    >>> str2bool(None)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> str2bool('/some/path')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> str2bool('Agg')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> str2bool('INFO')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> str2bool('/some/bytes/path'.encode('utf-8'))  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...

    """
    if isinstance(v, bool):
        return v

    if isinstance(v, bytes):
        v = v.decode("utf-8")

    if isinstance(v, str):
        lower = v.lower()
        if lower in ("yes", "true", "y", "t", "1", "on"):
            return True
        elif lower in ("no", "false", "n", "f", "0", "off"):
            return False

    raise ValueError("%r cannot be converted to bool" % v)


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

    out = []
    for item in prev_structure:
        out.append(unflatten(in_list, item))
    return out


def normalize_mc_params(params, source):
    """
    Normalize a single row of motion parameters to the SPM format.

    SPM saves motion parameters as:
        x   Right-Left          (mm)
        y   Anterior-Posterior  (mm)
        z   Superior-Inferior   (mm)
        rx  Pitch               (rad)
        ry  Roll                (rad)
        rz  Yaw                 (rad)
    """
    if source.upper() == "FSL":
        params = params[[3, 4, 5, 0, 1, 2]]
    elif source.upper() in ("AFNI", "FSFAST"):
        params = params[np.asarray([4, 5, 3, 1, 2, 0]) + (len(params) > 6)]
        params[3:] = params[3:] * np.pi / 180.0
    elif source.upper() == "NIPY":
        from nipy.algorithms.registration import to_matrix44, aff2euler

        matrix = to_matrix44(params)
        params = np.zeros(6)
        params[:3] = matrix[:3, 3]
        params[-1:2:-1] = aff2euler(matrix)

    return params


def dict_diff(dold, dnew, indent=0):
    """Helper to log what actually changed from old to new values of
    dictionaries.

    typical use -- log difference for hashed_inputs
    """
    # First check inputs, since they usually are lists of tuples
    # and dicts are required.
    if isinstance(dnew, list):
        dnew = dict(dnew)
    if isinstance(dold, list):
        dold = dict(dold)

    # Compare against hashed_inputs
    # Keys: should rarely differ
    new_keys = set(dnew.keys())
    old_keys = set(dold.keys())

    diff = []
    if new_keys - old_keys:
        diff += ["  * keys not previously seen: %s" % (new_keys - old_keys)]

    if old_keys - new_keys:
        diff += ["  * keys not presently seen: %s" % (old_keys - new_keys)]

    # Add topical message
    if diff:
        diff.insert(0, "Dictionaries had differing keys:")

    diffkeys = len(diff)

    # Values in common keys would differ quite often,
    # so we need to join the messages together
    for k in new_keys.intersection(old_keys):
        try:
            new, old = dnew[k], dold[k]
            same = new == old
            if not same:
                # Since JSON does not discriminate between lists and
                # tuples, we might need to cast them into the same type
                # as the last resort.  And lets try to be more generic
                same = old.__class__(new) == old
        except Exception:
            same = False
        if not same:
            diff += ["  * %s: %r != %r" % (k, dnew[k], dold[k])]

    if len(diff) > diffkeys:
        diff.insert(diffkeys, "Some dictionary entries had differing values:")

    return textwrap_indent("\n".join(diff), " " * indent)


def rgetcwd(error=True):
    """
    Robust replacement for getcwd when folders get removed
    If error==True, this is just an alias for os.getcwd()
    """
    if error:
        return os.getcwd()

    try:
        cwd = os.getcwd()
    except OSError as exc:
        # Changing back to cwd is probably not necessary
        # but this makes sure there's somewhere to change to.
        cwd = os.getenv("PWD")
        if cwd is None:
            raise OSError(
                (
                    exc.errno,
                    "Current directory does not exist anymore, "
                    "and nipype was not able to guess it from the environment",
                )
            )
        warn('Current folder does not exist, replacing with "%s" instead.' % cwd)
    return cwd
