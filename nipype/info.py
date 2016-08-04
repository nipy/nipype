""" This file contains defines parameters for nipy that we use to fill
settings in setup.py, the nipy top-level docstring, and for building the
docs.  In setup.py in particular, we exec this file, so it cannot import nipy
"""


# nipype version information.  An empty _version_extra corresponds to a
# full release.  '.dev' as a _version_extra string means this is a development
# version
_version_major = 0
_version_minor = 12
_version_micro = 0
_version_extra = ''  # Remove -dev for release


def get_nipype_gitversion():
    """Nipype version as reported by the last commit in git

    Returns
    -------
    None or str
      Version of NiPype according to git.
    """
    import os
    import subprocess
    try:
        import nipype
        gitpath = os.path.realpath(os.path.join(os.path.dirname(nipype.__file__),
                                                os.path.pardir))
    except:
        gitpath = os.getcwd()
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
        ver = o.decode().strip().split('-')[-1]
    return ver

if '-dev' in _version_extra:
    gitversion = get_nipype_gitversion()
    if gitversion:
        _version_extra = '-' + gitversion + '.dev'

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
__version__ = "%s.%s.%s%s" % (_version_major,
                              _version_minor,
                              _version_micro,
                              _version_extra)

CLASSIFIERS = ["Development Status :: 5 - Production/Stable",
               "Environment :: Console",
               "Intended Audience :: Science/Research",
               "License :: OSI Approved :: Apache Software License",
               "Operating System :: MacOS :: MacOS X",
               "Operating System :: POSIX :: Linux",
               "Programming Language :: Python :: 2.7",
               "Programming Language :: Python :: 3.4",
               "Programming Language :: Python :: 3.5",
               "Topic :: Scientific/Engineering"]

description = 'Neuroimaging in Python: Pipelines and Interfaces'

# Note: this long_description is actually a copy/paste from the top-level
# README.txt, so that it shows up nicely on PyPI.  So please remember to edit
# it only in one place and sync it correctly.
long_description = \
    """
========================================================
NIPYPE: Neuroimaging in Python: Pipelines and Interfaces
========================================================

Current neuroimaging software offer users an incredible opportunity to
analyze data using a variety of different algorithms. However, this has
resulted in a heterogeneous collection of specialized applications
without transparent interoperability or a uniform operating interface.

*Nipype*, an open-source, community-developed initiative under the
umbrella of NiPy_, is a Python project that provides a uniform interface
to existing neuroimaging software and facilitates interaction between
these packages within a single workflow. Nipype provides an environment
that encourages interactive exploration of algorithms from different
packages (e.g., AFNI, ANTS, BRAINS, BrainSuite, Camino, FreeSurfer, FSL, MNE,
MRtrix, MNE, Nipy, Slicer, SPM), eases the design of workflows within and
between packages, and reduces the learning curve necessary to use different
packages. Nipype is creating a collaborative platform for neuroimaging software
development in a high-level language and addressing limitations of existing
pipeline systems.

*Nipype* allows you to:

* easily interact with tools from different software packages
* combine processing steps from different software packages
* develop new workflows faster by reusing common steps from old ones
* process data faster by running it in parallel on many cores/machines
* make your research easily reproducible
* share your processing workflows with the community
"""

# versions
NIBABEL_MIN_VERSION = '2.0.1'
NETWORKX_MIN_VERSION = '1.7'
NUMPY_MIN_VERSION = '1.6.2'
SCIPY_MIN_VERSION = '0.11'
TRAITS_MIN_VERSION = '4.3'
DATEUTIL_MIN_VERSION = '1.5'
NOSE_MIN_VERSION = '1.2'
FUTURE_MIN_VERSION = '0.15.2'
SIMPLEJSON_MIN_VERSION = '3.8.0'
PROV_MIN_VERSION = '1.4.0'

NAME = 'nipype'
MAINTAINER = "nipype developers"
MAINTAINER_EMAIL = "neuroimaging@python.org"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "http://nipy.org/nipype"
DOWNLOAD_URL = "http://github.com/nipy/nipype/archives/master"
LICENSE = "Apache License, 2.0"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "nipype developers"
AUTHOR_EMAIL = "neuroimaging@python.org"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
ISRELEASE = _version_extra == ''
VERSION = __version__
PROVIDES = ['nipype']
REQUIRES = ["nibabel>=%s" % NIBABEL_MIN_VERSION,
            "networkx>=%s" % NETWORKX_MIN_VERSION,
            "numpy>=%s" % NUMPY_MIN_VERSION,
            "python-dateutil>=%s" % DATEUTIL_MIN_VERSION,
            "scipy>=%s" % SCIPY_MIN_VERSION,
            "traits>=%s" % TRAITS_MIN_VERSION,
            "nose>=%s" % NOSE_MIN_VERSION,
            "future>=%s" % FUTURE_MIN_VERSION,
            "simplejson>=%s" % SIMPLEJSON_MIN_VERSION,
            "prov>=%s" % PROV_MIN_VERSION,
            "mock",
            "xvfbwrapper"]
STATUS = 'stable'
