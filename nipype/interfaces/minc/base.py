# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The minc module provides classes for interfacing with the `MINC
<http://www.bic.mni.mcgill.ca/ServicesSoftware/MINC>`_ command line tools.
This module was written to work with MINC version 2.2.00.

Author: Carlo Hamalainen <carlo@carlo-hamalainen.net>
        http://carlo-hamalainen.net
"""
import os
import os.path
import warnings

from ..base import CommandLine

warnings.filterwarnings("always", category=UserWarning)


def check_minc():
    """Returns True if and only if MINC is installed.'"""

    return Info.version() is not None


def no_minc():
    """Returns True if and only if MINC is *not* installed."""
    return not check_minc()


class Info(object):
    """Handle MINC version information.

    version refers to the version of MINC on the system
    """

    @staticmethod
    def version():
        """Check for minc version on the system

        Parameters
        ----------
        None

        Returns
        -------
        version : dict
           Version number as dict or None if MINC not found

        """
        try:
            clout = CommandLine(
                command="mincinfo", args="-version", terminal_output="allatonce"
            ).run()
        except IOError:
            return None

        out = clout.runtime.stdout

        def read_program_version(s):
            if "program" in s:
                return s.split(":")[1].strip()
            return None

        def read_libminc_version(s):
            if "libminc" in s:
                return s.split(":")[1].strip()
            return None

        def read_netcdf_version(s):
            if "netcdf" in s:
                return " ".join(s.split(":")[1:]).strip()
            return None

        def read_hdf5_version(s):
            if "HDF5" in s:
                return s.split(":")[1].strip()
            return None

        versions = {"minc": None, "libminc": None, "netcdf": None, "hdf5": None}

        for l in out.split("\n"):
            for name, f in [
                ("minc", read_program_version),
                ("libminc", read_libminc_version),
                ("netcdf", read_netcdf_version),
                ("hdf5", read_hdf5_version),
            ]:
                if f(l) is not None:
                    versions[name] = f(l)

        return versions


def aggregate_filename(files, new_suffix):
    """
    Try to work out a sensible name given a set of files that have
    been combined in some way (e.g. averaged). If we can't work out a
    sensible prefix, we use the first filename in the list.

    Examples
    --------

    >>> from nipype.interfaces.minc.base import aggregate_filename
    >>> f = aggregate_filename(['/tmp/foo1.mnc', '/tmp/foo2.mnc', '/tmp/foo3.mnc'], 'averaged')
    >>> os.path.split(f)[1] # This has a full path, so just check the filename.
    'foo_averaged.mnc'

    >>> f = aggregate_filename(['/tmp/foo1.mnc', '/tmp/blah1.mnc'], 'averaged')
    >>> os.path.split(f)[1] # This has a full path, so just check the filename.
    'foo1_averaged.mnc'

    """

    path = os.path.split(files[0])[0]
    names = [os.path.splitext(os.path.split(x)[1])[0] for x in files]
    common_prefix = os.path.commonprefix(names)

    path = os.getcwd()

    if common_prefix == "":
        return os.path.abspath(
            os.path.join(
                path, os.path.splitext(files[0])[0] + "_" + new_suffix + ".mnc"
            )
        )
    else:
        return os.path.abspath(
            os.path.join(path, common_prefix + "_" + new_suffix + ".mnc")
        )
