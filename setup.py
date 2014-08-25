#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype : Neuroimaging in Python pipelines and interfaces package.

Nipype intends to create python interfaces to other neuroimaging
packages and create an API for specifying a full analysis pipeline in
python.
"""

import sys
from glob import glob
import os
from pip.req import parse_requirements
import versioneer

PY3 = sys.version_info[0] >= 3
if PY3:
    string_types = str,
else:
    string_types = basestring,
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from setuptools import setup, find_packages
from distutils.command.build_py import build_py

# XXX: write COMMIT_INFO.txt with versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'nipype/_version.py'
versioneer.versionfile_build = 'build/_version.py'
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'nipype-' # dirname like 'myproject-1.2.0'

from build_docs import cmdclass, INFO_VARS

#XXX: Build docs too

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

def main(**extra_args):
    setup(name=INFO_VARS['NAME'],
          maintainer=INFO_VARS['MAINTAINER'],
          maintainer_email=INFO_VARS['MAINTAINER_EMAIL'],
          description=INFO_VARS['DESCRIPTION'],
          long_description=INFO_VARS['LONG_DESCRIPTION'],
          url=INFO_VARS['URL'],
          download_url=INFO_VARS['DOWNLOAD_URL'],
          license=INFO_VARS['LICENSE'],
          classifiers=INFO_VARS['CLASSIFIERS'],
          author=INFO_VARS['AUTHOR'],
          author_email=INFO_VARS['AUTHOR_EMAIL'],
          platforms=INFO_VARS['PLATFORMS'],
          version=versioneer.get_version(),
          cmdclass=versioneer.get_cmdclass(),
          scripts=glob('bin/*'),
          install_requires=reqs,
          **extra_args)

if __name__ == "__main__":
    main()
