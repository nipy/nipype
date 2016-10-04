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
# Build helper
import sys
from glob import glob
import os
from os.path import join as pjoin
from io import open

# Commit hash writing, and dependency checking
from setuptools.command.build_py import build_py


PY3 = sys.version_info[0] >= 3

class BuildWithCommitInfoCommand(build_py):
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
        # The line below may contain a valid hash if it has been substituted during 'git archive'
        archive_subst_hash=$Format:%h$
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
    def run(self):
        from configparser import ConfigParser
        import subprocess

        build_py.run(self)
        proc = subprocess.Popen('git rev-parse --short HEAD',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
        repo_commit, _ = proc.communicate()
        # Fix for python 3
        if PY3:
            repo_commit = repo_commit.decode()

        # We write the installation commit even if it's empty
        cfg_parser = ConfigParser()
        cfg_parser.read(pjoin('nipype', 'COMMIT_INFO.txt'))
        cfg_parser.set('commit hash', 'install_hash', repo_commit.strip())
        out_pth = pjoin(self.build_lib, 'nipype', 'COMMIT_INFO.txt')
        if PY3:
            cfg_parser.write(open(out_pth, 'wt'))
        else:
            cfg_parser.write(open(out_pth, 'wb'))


def main():
    from setuptools import setup, find_packages

    thispath, _ = os.path.split(__file__)

    testdatafiles = [pjoin('testing', 'data', val)
                     for val in os.listdir(pjoin(thispath, 'nipype', 'testing', 'data'))
                     if not os.path.isdir(pjoin(thispath, 'nipype', 'testing', 'data', val))]

    testdatafiles += [
        pjoin('testing', 'data', 'dicomdir', '*'),
        pjoin('testing', 'data', 'bedpostxout', '*'),
        pjoin('testing', 'data', 'tbss_dir', '*'),
        pjoin('workflows', 'data', '*'),
        pjoin('pipeline', 'engine', 'report_template.html'),
        pjoin('external', 'd3.js'),
        pjoin('interfaces', 'script_templates', '*'),
        pjoin('interfaces', 'tests', 'realign_json.json'),
        pjoin('interfaces', 'tests', 'use_resources'),
    ]

    # Python 3: use a locals dictionary
    # http://stackoverflow.com/a/1463370/6820620
    ldict = locals()
    # Get version and release info, which is all stored in nipype/info.py
    ver_file = os.path.join(thispath, 'nipype', 'info.py')
    with open(ver_file) as infofile:
        exec(infofile.read(), globals(), ldict)

    setup(
        name=ldict['NAME'],
        maintainer=ldict['MAINTAINER'],
        maintainer_email=ldict['MAINTAINER_EMAIL'],
        description=ldict['DESCRIPTION'],
        long_description=ldict['LONG_DESCRIPTION'],
        url=ldict['URL'],
        download_url=ldict['DOWNLOAD_URL'],
        license=ldict['LICENSE'],
        classifiers=ldict['CLASSIFIERS'],
        author=ldict['AUTHOR'],
        author_email=ldict['AUTHOR_EMAIL'],
        platforms=ldict['PLATFORMS'],
        version=ldict['VERSION'],
        install_requires=ldict['REQUIRES'],
        setup_requires=['future', 'configparser'],
        provides=ldict['PROVIDES'],
        packages=[
            'nipype',
            'nipype.algorithms',
            'nipype.algorithms.tests',
            'nipype.caching',
            'nipype.caching.tests',
            'nipype.external',
            'nipype.fixes',
            'nipype.fixes.numpy',
            'nipype.fixes.numpy.testing',
            'nipype.interfaces',
            'nipype.interfaces.afni',
            'nipype.interfaces.afni.tests',
            'nipype.interfaces.ants',
            'nipype.interfaces.ants.tests',
            'nipype.interfaces.camino',
            'nipype.interfaces.camino.tests',
            'nipype.interfaces.camino2trackvis',
            'nipype.interfaces.camino2trackvis.tests',
            'nipype.interfaces.cmtk',
            'nipype.interfaces.cmtk.tests',
            'nipype.interfaces.diffusion_toolkit',
            'nipype.interfaces.diffusion_toolkit.tests',
            'nipype.interfaces.dipy',
            'nipype.interfaces.dipy.tests',
            'nipype.interfaces.elastix',
            'nipype.interfaces.elastix.tests',
            'nipype.interfaces.freesurfer',
            'nipype.interfaces.freesurfer.tests',
            'nipype.interfaces.fsl',
            'nipype.interfaces.fsl.tests',
            'nipype.interfaces.minc',
            'nipype.interfaces.minc.tests',
            'nipype.interfaces.mipav',
            'nipype.interfaces.mipav.tests',
            'nipype.interfaces.mne',
            'nipype.interfaces.mne.tests',
            'nipype.interfaces.mrtrix',
            'nipype.interfaces.mrtrix3',
            'nipype.interfaces.mrtrix.tests',
            'nipype.interfaces.mrtrix3.tests',
            'nipype.interfaces.nipy',
            'nipype.interfaces.nipy.tests',
            'nipype.interfaces.nitime',
            'nipype.interfaces.nitime.tests',
            'nipype.interfaces.script_templates',
            'nipype.interfaces.semtools',
            'nipype.interfaces.semtools.brains',
            'nipype.interfaces.semtools.brains.tests',
            'nipype.interfaces.semtools.diffusion',
            'nipype.interfaces.semtools.diffusion.tests',
            'nipype.interfaces.semtools.diffusion.tractography',
            'nipype.interfaces.semtools.diffusion.tractography.tests',
            'nipype.interfaces.semtools.filtering',
            'nipype.interfaces.semtools.filtering.tests',
            'nipype.interfaces.semtools.legacy',
            'nipype.interfaces.semtools.legacy.tests',
            'nipype.interfaces.semtools.registration',
            'nipype.interfaces.semtools.registration.tests',
            'nipype.interfaces.semtools.segmentation',
            'nipype.interfaces.semtools.segmentation.tests',
            'nipype.interfaces.semtools.testing',
            'nipype.interfaces.semtools.tests',
            'nipype.interfaces.semtools.utilities',
            'nipype.interfaces.semtools.utilities.tests',
            'nipype.interfaces.slicer',
            'nipype.interfaces.slicer.diffusion',
            'nipype.interfaces.slicer.diffusion.tests',
            'nipype.interfaces.slicer.filtering',
            'nipype.interfaces.slicer.filtering.tests',
            'nipype.interfaces.slicer.legacy',
            'nipype.interfaces.slicer.legacy.diffusion',
            'nipype.interfaces.slicer.legacy.diffusion.tests',
            'nipype.interfaces.slicer.legacy.tests',
            'nipype.interfaces.slicer.quantification',
            'nipype.interfaces.slicer.quantification.tests',
            'nipype.interfaces.slicer.registration',
            'nipype.interfaces.slicer.registration.tests',
            'nipype.interfaces.slicer.segmentation',
            'nipype.interfaces.slicer.segmentation.tests',
            'nipype.interfaces.slicer.tests',
            'nipype.interfaces.spm',
            'nipype.interfaces.spm.tests',
            'nipype.interfaces.tests',
            'nipype.interfaces.vista',
            'nipype.interfaces.vista.tests',
            'nipype.pipeline',
            'nipype.pipeline.engine',
            'nipype.pipeline.engine.tests',
            'nipype.pipeline.plugins',
            'nipype.pipeline.plugins.tests',
            'nipype.testing',
            'nipype.testing.data',
            'nipype.testing.data.bedpostxout',
            'nipype.testing.data.dicomdir',
            'nipype.testing.data.tbss_dir',
            'nipype.utils',
            'nipype.utils.tests',
            'nipype.workflows',
            'nipype.workflows.data',
            'nipype.workflows.dmri',
            'nipype.workflows.dmri.camino',
            'nipype.workflows.dmri.connectivity',
            'nipype.workflows.dmri.dipy',
            'nipype.workflows.dmri.fsl',
            'nipype.workflows.dmri.fsl.tests',
            'nipype.workflows.dmri.mrtrix',
            'nipype.workflows.fmri',
            'nipype.workflows.fmri.fsl',
            'nipype.workflows.fmri.fsl.tests',
            'nipype.workflows.fmri.spm',
            'nipype.workflows.fmri.spm.tests',
            'nipype.workflows.graph',
            'nipype.workflows.misc',
            'nipype.workflows.rsfmri',
            'nipype.workflows.rsfmri.fsl',
            'nipype.workflows.smri',
            'nipype.workflows.smri.ants',
            'nipype.workflows.smri.freesurfer',
            'nipype.workflows.warp'],

        package_data={'nipype': testdatafiles},
        scripts=glob('bin/*'),
        cmdclass={'build_py': BuildWithCommitInfoCommand},
        tests_require=ldict['TESTS_REQUIRES'],
        test_suite='nose.collector',
        zip_safe=False,
        extras_require=ldict['EXTRA_REQUIRES']
    )

if __name__ == "__main__":
    main()
