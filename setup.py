#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype : Neuroimaging in Python pipelines and interfaces package.

Nipype intends to create python interfaces to other neuroimaging
packages and create an API for specifying a full analysis pipeline in
python.

Much of the machinery at the beginning of this file has been copied over from
nibabel denoted by ## START - COPIED FROM NIBABEL and a corresponding ## END

"""

import sys
from glob import glob
import os

## START - COPIED FROM NIBABEL
from os.path import join as pjoin
from functools import partial

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

# For some commands, use setuptools.
if len(set(('develop', 'bdist_egg', 'bdist_rpm', 'bdist', 'bdist_dumb',
            'install_egg_info', 'egg_info', 'easy_install', 'bdist_wheel',
            'bdist_mpkg')).intersection(sys.argv)) > 0:
    # setup_egg imports setuptools setup, thus monkeypatching distutils.
    import setup_egg

from distutils.core import setup

from distutils.version import LooseVersion
from distutils.command.build_py import build_py

from distutils import log

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

def _add_append_key(in_dict, key, value):
    """ Helper for appending dependencies to setuptools args """
    # If in_dict[key] does not exist, create it
    # If in_dict[key] is a string, make it len 1 list of strings
    # Append value to in_dict[key] list
    if key not in in_dict:
        in_dict[key] = []
    elif isinstance(in_dict[key], string_types):
        in_dict[key] = [in_dict[key]]
    in_dict[key].append(value)

# Dependency checks
def package_check(pkg_name, version=None,
                  optional=False,
                  checker=LooseVersion,
                  version_getter=None,
                  messages=None,
                  setuptools_args=None,
                  pypi_pkg_name=None
                  ):
    ''' Check if package `pkg_name` is present and has good enough version

    Has two modes of operation.  If `setuptools_args` is None (the default),
    raise an error for missing non-optional dependencies and log warnings for
    missing optional dependencies.  If `setuptools_args` is a dict, then fill
    ``install_requires`` key value with any missing non-optional dependencies,
    and the ``extras_requires`` key value with optional dependencies.

    This allows us to work with and without setuptools.  It also means we can
    check for packages that have not been installed with setuptools to avoid
    installing them again.

    Parameters
    ----------
    pkg_name : str
       name of package as imported into python
    version : {None, str}, optional
       minimum version of the package that we require. If None, we don't
       check the version.  Default is None
    optional : bool or str, optional
       If ``bool(optional)`` is False, raise error for absent package or wrong
       version; otherwise warn.  If ``setuptools_args`` is not None, and
       ``bool(optional)`` is not False, then `optional` should be a string
       giving the feature name for the ``extras_require`` argument to setup.
    checker : callable, optional
       callable with which to return comparable thing from version
       string.  Default is ``distutils.version.LooseVersion``
    version_getter : {None, callable}:
       Callable that takes `pkg_name` as argument, and returns the
       package version string - as in::

          ``version = version_getter(pkg_name)``

       If None, equivalent to::

          mod = __import__(pkg_name); version = mod.__version__``
    messages : None or dict, optional
       dictionary giving output messages
    setuptools_args : None or dict
       If None, raise errors / warnings for missing non-optional / optional
       dependencies.  If dict fill key values ``install_requires`` and
       ``extras_require`` for non-optional and optional dependencies.
    pypi_pkg_name : None or string
       When the pypi package name differs from the installed module. This is the
       case with the package python-dateutil which installs as dateutil.
    '''
    setuptools_mode = not setuptools_args is None
    optional_tf = bool(optional)
    if version_getter is None:
        def version_getter(pkg_name):
            mod = __import__(pkg_name)
            return mod.__version__
    if messages is None:
        messages = {}
    msgs = {
         'missing': 'Cannot import package "%s" - is it installed?',
         'missing opt': 'Missing optional package "%s"',
         'opt suffix' : '; you may get run-time errors',
         'version too old': 'You have version %s of package "%s"'
                            ' but we need version >= %s', }
    msgs.update(messages)
    status, have_version = _package_status(pkg_name,
                                           version,
                                           version_getter,
                                           checker)
    if pypi_pkg_name:
        pkg_name = pypi_pkg_name

    if status == 'satisfied':
        return
    if not setuptools_mode:
        if status == 'missing':
            if not optional_tf:
                raise RuntimeError(msgs['missing'] % pkg_name)
            log.warn(msgs['missing opt'] % pkg_name +
                     msgs['opt suffix'])
            return
        elif status == 'no-version':
            raise RuntimeError('Cannot find version for %s' % pkg_name)
        assert status == 'low-version'
        if not optional_tf:
            raise RuntimeError(msgs['version too old'] % (have_version,
                                                          pkg_name,
                                                          version))
        log.warn(msgs['version too old'] % (have_version,
                                            pkg_name,
                                            version)
                    + msgs['opt suffix'])
        return
    # setuptools mode
    if optional_tf and not isinstance(optional, string_types):
        raise RuntimeError('Not-False optional arg should be string')
    dependency = pkg_name

    if version:
        dependency += '>=' + version
    if optional_tf:
        if not 'extras_require' in setuptools_args:
            setuptools_args['extras_require'] = {}
        _add_append_key(setuptools_args['extras_require'],
                        optional,
                        dependency)
        return
    _add_append_key(setuptools_args, 'install_requires', dependency)
    return


def _package_status(pkg_name, version, version_getter, checker):
    try:
        __import__(pkg_name)
    except ImportError:
        return 'missing', None
    if not version:
        return 'satisfied', None
    try:
        have_version = version_getter(pkg_name)
    except AttributeError:
        return 'no-version', None
    if checker(have_version) < checker(version):
        return 'low-version', have_version
    return 'satisfied', have_version

## END - COPIED FROM NIBABEL

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

# Prepare setuptools args
if 'setuptools' in sys.modules:
    extra_setuptools_args = dict(
        tests_require=['nose'],
        test_suite='nose.collector',
        zip_safe=False,
        extras_require = dict(
            doc='Sphinx>=0.3',
            test='nose>=0.10.1'),
    )
    pkg_chk = partial(package_check, setuptools_args = extra_setuptools_args)
else:
    extra_setuptools_args = {}
    pkg_chk = package_check

# Hard and soft dependency checking
pkg_chk('networkx', INFO_VARS['NETWORKX_MIN_VERSION'])
pkg_chk('nibabel', INFO_VARS['NIBABEL_MIN_VERSION'])
pkg_chk('numpy', INFO_VARS['NUMPY_MIN_VERSION'])
pkg_chk('scipy', INFO_VARS['SCIPY_MIN_VERSION'])
pkg_chk('traits', INFO_VARS['TRAITS_MIN_VERSION'])
pkg_chk('nose', INFO_VARS['NOSE_MIN_VERSION'])
pkg_chk('dateutil', INFO_VARS['DATEUTIL_MIN_VERSION'],
        pypi_pkg_name='python-dateutil')

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
          configuration=configuration,
          cmdclass=cmdclass,
          scripts=glob('bin/*'),
          **extra_args)

if __name__ == "__main__":
    main(**extra_setuptools_args)
