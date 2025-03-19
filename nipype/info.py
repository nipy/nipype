"""This file contains defines parameters for nipy that we use to fill
settings in setup.py, the nipy top-level docstring, and for building the
docs.  In setup.py in particular, we exec this file, so it cannot import nipy
"""

# nipype version information
# Remove .dev0 for release
__version__ = "1.10.0"


def get_nipype_gitversion():
    """Nipype version as reported by the last commit in git

    Returns
    -------
    None or str
      Version of Nipype according to git.
    """
    import os
    import subprocess

    try:
        import nipype

        gitpath = os.path.realpath(
            os.path.join(os.path.dirname(nipype.__file__), os.path.pardir)
        )
    except:
        gitpath = os.getcwd()
    gitpathgit = os.path.join(gitpath, ".git")
    if not os.path.exists(gitpathgit):
        return None
    ver = None
    try:
        o, _ = subprocess.Popen(
            "git describe", shell=True, cwd=gitpath, stdout=subprocess.PIPE
        ).communicate()
    except Exception:
        pass
    else:
        ver = o.decode().strip().split("-")[-1]
    return ver


if __version__.endswith("-dev"):
    gitversion = get_nipype_gitversion()
    if gitversion:
        __version__ = f"{__version__}+{gitversion}"

CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering",
]
PYTHON_REQUIRES = ">= 3.9"

description = "Neuroimaging in Python: Pipelines and Interfaces"

# Note: this long_description is actually a copy/paste from the top-level
# README.txt, so that it shows up nicely on PyPI.  So please remember to edit
# it only in one place and sync it correctly.
long_description = """========================================================
NIPYPE: Neuroimaging in Python: Pipelines and Interfaces
========================================================

Current neuroimaging software offer users an incredible opportunity to
analyze data using a variety of different algorithms. However, this has
resulted in a heterogeneous collection of specialized applications
without transparent interoperability or a uniform operating interface.

*Nipype*, an open-source, community-developed initiative under the
umbrella of `NiPy <http://nipy.org>`_, is a Python project that provides a
uniform interface to existing neuroimaging software and facilitates interaction
between these packages within a single workflow. Nipype provides an environment
that encourages interactive exploration of algorithms from different
packages (e.g., AFNI, ANTS, BRAINS, BrainSuite, Camino, FreeSurfer, FSL, MNE,
MRtrix, MNE, Nipy, Slicer, SPM), eases the design of workflows within and
between packages, and reduces the learning curve necessary to use different \
packages. Nipype is creating a collaborative platform for neuroimaging \
software development in a high-level language and addressing limitations of \
existing pipeline systems.

*Nipype* allows you to:

* easily interact with tools from different software packages
* combine processing steps from different software packages
* develop new workflows faster by reusing common steps from old ones
* process data faster by running it in parallel on many cores/machines
* make your research easily reproducible
* share your processing workflows with the community
"""

# versions
NIBABEL_MIN_VERSION = "3.0"
NETWORKX_MIN_VERSION = "2.5"
NUMPY_MIN_VERSION = "1.21"
SCIPY_MIN_VERSION = "1.8"
TRAITS_MIN_VERSION = "6.2"
DATEUTIL_MIN_VERSION = "2.2"
SIMPLEJSON_MIN_VERSION = "3.8.0"
PROV_MIN_VERSION = "1.5.2"
RDFLIB_MIN_VERSION = "5.0.0"
CLICK_MIN_VERSION = "6.6.0"
PYDOT_MIN_VERSION = "1.2.3"

NAME = "nipype"
MAINTAINER = "nipype developers"
MAINTAINER_EMAIL = "neuroimaging@python.org"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "http://nipy.org/nipype"
DOWNLOAD_URL = "http://github.com/nipy/nipype/archives/master"
LICENSE = "Apache License, 2.0"
AUTHOR = "nipype developers"
AUTHOR_EMAIL = "neuroimaging@python.org"
PLATFORMS = "OS Independent"
MAJOR = __version__.split(".")[0]
MINOR = __version__.split(".")[1]
MICRO = __version__.replace("-", ".").split(".")[2]
ISRELEASE = (
    len(__version__.replace("-", ".").split(".")) == 3
    or "post" in __version__.replace("-", ".").split(".")[-1]
)
VERSION = __version__
PROVIDES = ["nipype"]
REQUIRES = [
    "click>=%s" % CLICK_MIN_VERSION,
    "networkx>=%s" % NETWORKX_MIN_VERSION,
    "nibabel>=%s" % NIBABEL_MIN_VERSION,
    "numpy>=%s" % NUMPY_MIN_VERSION,
    "packaging",
    "prov>=%s" % PROV_MIN_VERSION,
    "pydot>=%s" % PYDOT_MIN_VERSION,
    "python-dateutil>=%s" % DATEUTIL_MIN_VERSION,
    "rdflib>=%s" % RDFLIB_MIN_VERSION,
    "scipy>=%s" % SCIPY_MIN_VERSION,
    "simplejson>=%s" % SIMPLEJSON_MIN_VERSION,
    "traits>=%s" % TRAITS_MIN_VERSION,
    "filelock>=3.0.0",
    "acres",
    "etelemetry>=0.3.1",
    "looseversion!=1.2",
    "puremagic",
]

TESTS_REQUIRES = [
    "coverage >= 5.2.1",
    "pandas >= 1.5.0",
    "pytest >= 6",
    "pytest-cov >=2.11",
    "pytest-env",
    "pytest-timeout >=1.4",
    "pytest-doctestplus",
    "pytest-xdist >= 2.5",
    "sphinx >=7",
]

EXTRA_REQUIRES = {
    "data": ["datalad"],
    "doc": [
        "dipy",
        "ipython",
        "matplotlib",
        "nbsphinx",
        "sphinx-argparse",
        "sphinx>=2.1.2",
        "sphinxcontrib-apidoc",
    ],
    "duecredit": ["duecredit"],
    "maint": ["GitPython", "fuzzywuzzy"],
    "nipy": ["nitime", "nilearn", "dipy", "nipy", "matplotlib"],
    "profiler": ["psutil>=5.0"],
    "pybids": ["pybids>=0.7.0"],
    "specs": ["black"],
    "ssh": ["paramiko"],
    "tests": TESTS_REQUIRES,
    "xvfbwrapper": ["xvfbwrapper"],
    # 'mesh': ['mayavi']  # Enable when it works
}


def _list_union(iterable):
    return list(set(x for sublist in iterable for x in sublist))


# Enable a handle to install all extra dependencies at once
EXTRA_REQUIRES["all"] = _list_union(EXTRA_REQUIRES.values())
# dev = doc + tests + specs
EXTRA_REQUIRES["dev"] = _list_union(
    val for key, val in EXTRA_REQUIRES.items() if key in ("doc", "tests", "specs")
)

STATUS = "stable"
