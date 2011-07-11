# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import time, sys, os, subprocess
from tempfile import mkstemp

import nipype

version = '0.4'
release = True

# Return the svn version as a string, raise a ValueError otherwise
# This code was copied from numpy trunk, revision 6873, and modified slightly

__all__ = ['get_nipype_gitversion']


def get_nipype_gitversion():
    """PyMVPA version as reported by git.

    Returns
    -------
    None or str
      Version of NiPype according to git.
    """
    gitpath = os.path.realpath(os.path.join(os.path.dirname(nipype.__file__), os.path.pardir))
    gitpathgit = os.path.join(gitpath, '.git')
    if not os.path.exists(gitpathgit):
        return None
    ver = None
    try:
        (tmpd, tmpn) = mkstemp('nipype', 'git')
        retcode = subprocess.call(['git',
                                   '--git-dir=%s' % gitpathgit,
                                   '--work-tree=%s' % gitpath,
                                   'describe', '--abbrev=4', 'HEAD'
                                   ],
                                  stdout=tmpd,
                                  stderr=subprocess.STDOUT)
        outline = open(tmpn, 'r').readlines()[0].strip()
        if outline.startswith('upstream/'):
            ver = outline.replace('upstream/', '')
    finally:
        os.remove(tmpn)
    return ver

if not release:
    version += '.dev'

