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
from os.path import join as pjoin

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from distutils.command.build_py import build_py

def get_comrec_build(pkg_dir, build_cmd=build_py):
    """ Return extended build command class for recording commit

    The extended command tries to run git to find the current commit, getting
    the empty string if it fails.  It then writes the commit hash into a file
    in the `pkg_dir` path, named ``COMMIT_INFO.txt``.

    In due course this information can be used by the package after it is
    installed, to tell you what commit it was installed from if known.

    To make use of this system, you need a package with a COMMIT_INFO.txt file -
    e.g. ``myproject/COMMIT_INFO.txt`` - that might well look like this::

        # This is an ini file that may contain information about the code state
        [commit hash]
        # The line below may contain a valid hash if it has been substituted
        during 'git archive' archive_subst_hash=$Format:%h$
        # This line may be modified by the install process
        install_hash=

    The COMMIT_INFO file above is also designed to be used with git substitution
    - so you probably also want a ``.gitattributes`` file in the root directory
    of your working tree that contains something like this::

       myproject/COMMIT_INFO.txt export-subst

    That will cause the ``COMMIT_INFO.txt`` file to get filled in by ``git
    archive`` - useful in case someone makes such an archive - for example with
    via the github 'download source' button.

    Although all the above will work as is, you might consider having something
    like a ``get_info()`` function in your package to display the commit
    information at the terminal.  See the ``pkg_info.py`` module in the nipy
    package for an example.
    """
    class MyBuildPy(build_cmd):
        ''' Subclass to write commit data into installation tree '''
        def run(self):
            build_cmd.run(self)
            import subprocess
            proc = subprocess.Popen('git rev-parse HEAD',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            repo_commit, _ = proc.communicate()
            # Fix for python 3
            repo_commit = str(repo_commit)
            # We write the installation commit even if it's empty
            cfg_parser = ConfigParser()
            cfg_parser.read(pjoin(pkg_dir, 'COMMIT_INFO.txt'))
            cfg_parser.set('commit hash', 'install_hash', repo_commit)
            out_pth = pjoin(self.build_lib, pkg_dir, 'COMMIT_INFO.txt')
            cfg_parser.write(open(out_pth, 'wt'))
    return MyBuildPy

from build_docs import cmdclass, INFO_VARS

# Add custom commit-recording build command
cmdclass['build_py'] = get_comrec_build('nipype')

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration(None, parent_package, top_path)
    config.set_options(ignore_setup_xxx_py=True,
                       assume_default_configuration=True,
                       delegate_options_to_subpackages=True,
                       quiet=True)
    # The quiet=True option will silence all of the name setting warnings:
    # Ignoring attempt to set 'name' (from 'nipy.core' to
    #    'nipy.core.image')
    # Robert Kern recommends setting quiet=True on the numpy list, stating
    # these messages are probably only used in debugging numpy distutils.
    config.get_version('nipype/__init__.py') # sets config.version
    config.add_subpackage('nipype', 'nipype')
    return config

################################################################################
# For some commands, use setuptools

if len(set(('develop', 'bdist_egg', 'bdist_rpm', 'bdist', 'bdist_dumb',
            'bdist_wininst', 'install_egg_info', 'egg_info', 'easy_install',
            )).intersection(sys.argv)) > 0:
    from setup_egg import extra_setuptools_args

# extra_setuptools_args can be defined from the line above, but it can
# also be defined here because setup.py has been exec'ed from
# setup_egg.py.
if not 'extra_setuptools_args' in globals():
    extra_setuptools_args = dict()


################################################################################
# Import the documentation building classes.

try:
    from build_docs import cmdclass
except ImportError:
    """ Pass by the doc build gracefully if sphinx is not installed """
    print "Sphinx is not installed, docs cannot be built"
    cmdclass = {}


################################################################################

def main(**extra_args):
    from numpy.distutils.core import setup

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
          version=INFO_VARS['VERSION'],
          install_requires=INFO_VARS['REQUIRES'],
          configuration = configuration,
          cmdclass = cmdclass,
          scripts = glob('bin/*'),
          **extra_args)

if __name__ == "__main__":
    main(**extra_setuptools_args)
