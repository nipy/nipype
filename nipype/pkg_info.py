# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from future import standard_library
standard_library.install_aliases()
from builtins import open
import configparser

import os
import sys
import subprocess

COMMIT_INFO_FNAME = 'COMMIT_INFO.txt'
PY3 = sys.version_info[0] >= 3


def pkg_commit_hash(pkg_path):
    ''' Get short form of commit hash given directory `pkg_path`

    There should be a file called 'COMMIT_INFO.txt' in `pkg_path`.  This is a
    file in INI file format, with at least one section: ``commit hash`` and two
    variables ``archive_subst_hash`` and ``install_hash``.  The first has a
    substitution pattern in it which may have been filled by the execution of
    ``git archive`` if this is an archive generated that way.  The second is
    filled in by the installation, if the installation is from a git archive.

    We get the commit hash from (in order of preference):

    * A substituted value in ``archive_subst_hash``
    * A written commit hash value in ``install_hash`
    * git's output, if we are in a git repository

    If all these fail, we return a not-found placeholder tuple

    Parameters
    ----------
    pkg_path : str
       directory containing package

    Returns
    -------
    hash_from : str
       Where we got the hash from - description
    hash_str : str
       short form of hash
    '''
    # Try and get commit from written commit text file
    pth = os.path.join(pkg_path, COMMIT_INFO_FNAME)
    if not os.path.isfile(pth):
        raise IOError('Missing commit info file %s' % pth)
    if PY3:
        cfg_parser = configparser.RawConfigParser()
    else:
        cfg_parser = configparser.ConfigParser()
    with open(pth, encoding='utf-8') as fp:
        cfg_parser.readfp(fp)
    archive_subst = cfg_parser.get('commit hash', 'archive_subst_hash')
    if not archive_subst.startswith('$Format'):  # it has been substituted
        return 'archive substitution', archive_subst
    install_subst = cfg_parser.get('commit hash', 'install_hash')
    if install_subst != '':
        return 'installation', install_subst
    # maybe we are in a repository
    proc = subprocess.Popen(
        'git rev-parse --short HEAD',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=pkg_path,
        shell=True)
    repo_commit, _ = proc.communicate()
    if repo_commit:
        if PY3:
            repo_commit = repo_commit.decode()
        return 'repository', repo_commit.strip()
    return '(none found)', '<not found>'


def get_pkg_info(pkg_path):
    ''' Return dict describing the context of this package

    Parameters
    ----------
    pkg_path : str
       path containing __init__.py for package

    Returns
    -------
    context : dict
       with named parameters of interest
    '''
    src, hsh = pkg_commit_hash(pkg_path)
    from .info import VERSION
    if not PY3:
        src, hsh, VERSION = src.encode(), hsh.encode(), VERSION.encode()
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
        traits_version=traits.__version__)
