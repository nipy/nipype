#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype : Neuroimaging in Python pipelines and interfaces package.

Nipype intends to create python interfaces to other neuroimaging
packages and create an API for specifying a full analysis pipeline in
python.

"""

import sys


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

    config.get_version('nipype/version.py') # sets config.version

    config.add_subpackage('nipype', 'nipype')
    config.add_subpackage('nipype.testing.numpytesting')

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

# We need to import nipy as late as possible, 
from nipype import  __doc__

def main(**extra_args):
    from numpy.distutils.core import setup
    
    setup( name = 'nipype',
           description = 'Nipype, a Neuroimaging in Python package',
           author = 'Various',
           author_email = 'nipy-devel@neuroimaging.scipy.org',
           url = 'http://nipy.sourceforge.net/nipype',
           long_description = __doc__,
           configuration = configuration,
           cmdclass = cmdclass,
           **extra_args)


if __name__ == "__main__":
    main(**extra_setuptools_args)
