# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import subprocess

import nipype

version = '0.4.2'
release = False

__all__ = ['get_nipype_gitversion']


def get_nipype_gitversion():
    """Nipype version as reported by the last commit in git

    Returns
    -------
    None or str
      Version of NiPype according to git.
    """
    gitpath = os.path.realpath(os.path.join(os.path.dirname(nipype.__file__),
                                            os.path.pardir))
    gitpathgit = os.path.join(gitpath, '.git')
    if not os.path.exists(gitpathgit):
        return None
    ver = None
    try:
        o, _ = subprocess.Popen('git describe', shell=True, cwd=gitpath,
                         stdout=subprocess.PIPE).communicate()
    except Exception:
        pass
    else:
        ver = o.strip().split('-')[-1]
    return ver

if not release:
    gitversion = get_nipype_gitversion()
    if gitversion:
        version += '-' + gitversion
    version += '.dev'
