import configparser

import os
import sys
import subprocess

COMMIT_INFO_FNAME = "COMMIT_INFO.txt"


def pkg_commit_hash(pkg_path):
    """Get short form of commit hash.

    We get the commit hash from (in order of preference):
    * The local part of the version string (if installed)
    * git's output, if we are in a git repository

    Returns
    -------
    hash_from : str
       Where we got the hash from - description
    hash_str : str
       short form of hash
    """
    from . import __version__

    # If version has a local part (e.g. +g8234ec318)
    if "+" in __version__:
        local_part = __version__.split("+")[1]
        # hatch-vcs/setuptools-scm format: g<hash>
        if local_part.startswith("g"):
            hsh = local_part[1:].split(".")[0]
            return "installation", hsh

    # maybe we are in a repository
    try:
        proc = subprocess.Popen(
            "git rev-parse --short HEAD",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=pkg_path,
            shell=True,
        )
        repo_commit, _ = proc.communicate()
        if repo_commit:
            return "repository", repo_commit.decode().strip()
    except Exception:
        pass

    return "(none found)", "<not found>"


def get_pkg_info(pkg_path):
    """Return dict describing the context of this package

    Parameters
    ----------
    pkg_path : str
       path containing __init__.py for package

    Returns
    -------
    context : dict
       with named parameters of interest
    """
    src, hsh = pkg_commit_hash(pkg_path)
    from . import __version__ as VERSION
    import networkx
    import nibabel
    import numpy
    import scipy
    import traits

    return dict(
        pkg_path=pkg_path,
        commit_source=src,
        commit_hash=hsh,
        nipype_version=VERSION,
        sys_version=sys.version,
        sys_executable=sys.executable,
        sys_platform=sys.platform,
        numpy_version=numpy.__version__,
        scipy_version=scipy.__version__,
        networkx_version=networkx.__version__,
        nibabel_version=nibabel.__version__,
        traits_version=traits.__version__,
    )
