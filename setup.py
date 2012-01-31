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

desc = """Current neuroimaging software offer users an incredible opportunity to
analyze data using a variety of different algorithms. However, this has
resulted in a heterogeneous collection of specialized applications
without transparent interoperability or a uniform operating interface.

*Nipype*, an open-source, community-developed initiative under the
umbrella of NiPy, is a Python project that provides a uniform interface
to existing neuroimaging software and facilitates interaction between
these packages within a single workflow. Nipype provides an environment
that encourages interactive exploration of algorithms from different
packages (e.g., SPM, FSL, FreeSurfer, AFNI, Slicer), eases the
design of workflows within and between packages, and reduces the
learning curve necessary to use different packages. Nipype is creating a
collaborative platform for neuroimaging software development in a
high-level language and addressing limitations of existing pipeline
systems.

*Nipype* allows you to:

* easily interact with tools from different software packages
* combine processing steps from different software packages
* develop new workflows faster by reusing common steps from old ones
* process data faster by running it in parallel on many cores/machines
* make your research easily reproducible
* share your processing workflows with the community"""

def main(**extra_args):
    from numpy.distutils.core import setup

    install_requires=['numpy >=1.1',
              'scipy >=0.7',
              'networkx >=1.0',
              'nibabel >=1.0.0',
              'traits >=4.0.0',]

    try:
        import json
    except ImportError:
        install_requires.append('simplejson')

    setup( name = 'nipype',
           description = 'Neuroimaging in Python: Pipelines and Interfaces',
           author = 'Various',
           author_email = 'nipy-devel@neuroimaging.scipy.org',
           url = 'http://nipy.org/nipype',
           long_description = desc,
           configuration = configuration,
           cmdclass = cmdclass,
           install_requires=install_requires,
           **extra_args)


if __name__ == "__main__":
    main(**extra_setuptools_args)
