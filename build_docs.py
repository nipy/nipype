# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Code to build the documentation in the setup.py

To use this code, run::

    python setup.py build_sphinx
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import open, str

# Standard library imports
import sys
import os
from os.path import join as pjoin
import zipfile
import warnings
import shutil
from distutils.cmd import Command
from distutils.command.clean import clean

_info_fname = pjoin(os.path.dirname(__file__), 'nipype', 'info.py')
INFO_VARS = {}
exec(str(open(_info_fname, 'rt').read()), {}, INFO_VARS)

DOC_BUILD_DIR = os.path.join('doc', '_build', 'html')
DOC_DOCTREES_DIR = os.path.join('doc', '_build', 'doctrees')

###############################################################################
# Distutils Command class for installing nipype to a temporary location.


class TempInstall(Command):
    temp_install_dir = os.path.join('build', 'install')

    def run(self):
        """ build and install nipype in a temporary location. """
        install = self.distribution.get_command_obj('install')
        install.install_scripts = self.temp_install_dir
        install.install_base = self.temp_install_dir
        install.install_platlib = self.temp_install_dir
        install.install_purelib = self.temp_install_dir
        install.install_data = self.temp_install_dir
        install.install_lib = self.temp_install_dir
        install.install_headers = self.temp_install_dir
        install.run()

        # Horrible trick to reload nipype with our temporary instal
        for key in list(sys.modules.keys()):
            if key.startswith('nipype'):
                sys.modules.pop(key, None)
        sys.path.append(os.path.abspath(self.temp_install_dir))
        # Pop the cwd
        sys.path.pop(0)
        import nipype

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


###############################################################################
# Distutils Command class for API generation
class APIDocs(TempInstall):
    description = \
        """generate API docs """

    user_options = [
        ('None', None, 'this command has no options'),
    ]

    def run(self):
        # First build the project and install it to a temporary location.
        TempInstall.run(self)
        os.chdir('doc')
        try:
            # We are running the API-building script via an
            # system call, but overriding the import path.
            toolsdir = os.path.abspath(pjoin('..', 'tools'))
            for docbuilder in ['build_interface_docs.py']:
                build_templates = pjoin(toolsdir, docbuilder)
                cmd = """%s -c 'import sys; sys.path.append("%s"); sys.path.append("%s"); execfile("%s", dict(__name__="__main__"))'""" \
                    % (sys.executable,
                       toolsdir,
                       self.temp_install_dir,
                       build_templates)
                os.system(cmd)
        finally:
            os.chdir('..')


###############################################################################
# Code to copy the sphinx-generated html docs in the distribution.
def relative_path(filename):
    """ Return the relative path to the file, assuming the file is
        in the DOC_BUILD_DIR directory.
    """
    length = len(os.path.abspath(DOC_BUILD_DIR)) + 1
    return os.path.abspath(filename)[length:]


###############################################################################
# Distutils Command class build the docs
# Sphinx import.
try:
    from sphinx.setup_command import BuildDoc
except:
    MyBuildDoc = None
else:
    class MyBuildDoc(BuildDoc):
        """ Sub-class the standard sphinx documentation building system, to
            add logics for API generation and matplotlib's plot directive.
        """

        def run(self):
            self.run_command('api_docs')
            # We need to be in the doc directory for to plot_directive
            # and API generation to work
            """
            os.chdir('doc')
            try:
                BuildDoc.run(self)
            finally:
                os.chdir('..')
            """
            # It put's the build in a doc/doc/_build directory with the
            # above?!?!  I'm leaving the code above here but commented out
            # in case I'm missing something?
            BuildDoc.run(self)
            self.zip_docs()

        def zip_docs(self):
            if not os.path.exists(DOC_BUILD_DIR):
                raise OSError('Doc directory does not exist.')
            target_file = os.path.join('doc', 'documentation.zip')
            # ZIP_DEFLATED actually compresses the archive. However, there
            # will be a RuntimeError if zlib is not installed, so we check
            # for it. ZIP_STORED produces an uncompressed zip, but does not
            # require zlib.
            try:
                zf = zipfile.ZipFile(target_file, 'w',
                                     compression=zipfile.ZIP_DEFLATED)
            except RuntimeError:
                warnings.warn('zlib not installed, storing the docs '
                              'without compression')
                zf = zipfile.ZipFile(target_file, 'w',
                                     compression=zipfile.ZIP_STORED)

            for root, dirs, files in os.walk(DOC_BUILD_DIR):
                relative = relative_path(root)
                if not relative.startswith('.doctrees'):
                    for f in files:
                        zf.write(os.path.join(root, f),
                                 os.path.join(relative, 'html_docs', f))
            zf.close()

        def finalize_options(self):
            """ Override the default for the documentation build
                directory.
            """
            self.build_dir = os.path.join(*DOC_BUILD_DIR.split(os.sep)[:-1])
            BuildDoc.finalize_options(self)

###############################################################################
# Distutils Command class to clean


class Clean(clean):

    def run(self):
        clean.run(self)
        api_path = os.path.join('doc', 'api', 'generated')
        if os.path.exists(api_path):
            print("Removing %s" % api_path)
            shutil.rmtree(api_path)
        interface_path = os.path.join('doc', 'interfaces', 'generated')
        if os.path.exists(interface_path):
            print("Removing %s" % interface_path)
            shutil.rmtree(interface_path)
        if os.path.exists(DOC_BUILD_DIR):
            print("Removing %s" % DOC_BUILD_DIR)
            shutil.rmtree(DOC_BUILD_DIR)
        if os.path.exists(DOC_DOCTREES_DIR):
            print("Removing %s" % DOC_DOCTREES_DIR)
            shutil.rmtree(DOC_DOCTREES_DIR)


# The command classes for distutils, used by the setup.py
cmdclass = {'build_sphinx': MyBuildDoc,
            'api_docs': APIDocs,
            'clean': Clean,
            }
