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
"""Build helper."""

import os
from os.path import join as pjoin
from glob import glob
import sys
from functools import partial

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

# Commit hash writing, and dependency checking
from nisext.sexts import get_comrec_build, package_check, install_scripts_bat
cmdclass = {'build_py': get_comrec_build('nipype'),
            'install_scripts': install_scripts_bat}

# Get version and release info, which is all stored in nipype/info.py
ver_file = os.path.join('nipype', 'info.py')
exec(open(ver_file).read())

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

# Do dependency checking
pkg_chk('networkx', NETWORKX_MIN_VERSION)
pkg_chk('nibabel', NIBABEL_MIN_VERSION)
pkg_chk('numpy', NUMPY_MIN_VERSION)
pkg_chk('scipy', SCIPY_MIN_VERSION)
pkg_chk('traits', TRAITS_MIN_VERSION)
pkg_chk('nose', NOSE_MIN_VERSION)
custom_dateutil_messages = {'missing opt': ('Missing optional package "%s"'
                                            ' provided by package '
                                            '"python-dateutil"')}
pkg_chk('dateutil', DATEUTIL_MIN_VERSION,
        messages = custom_dateutil_messages)

def main(**extra_args):
    setup(name=NAME,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION,
          url=URL,
          download_url=DOWNLOAD_URL,
          license=LICENSE,
          classifiers=CLASSIFIERS,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          platforms=PLATFORMS,
          version=VERSION,
          requires=REQUIRES,
          provides=PROVIDES,
          packages     = [ 'nipype',
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
                           'nipype.interfaces.mipav',
                           'nipype.interfaces.mipav.tests',
                           'nipype.interfaces.mne',
                           'nipype.interfaces.mne.tests',
                           'nipype.interfaces.mrtrix',
                           'nipype.interfaces.mrtrix.tests',
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
                           'nipype.pipeline.plugins',
                           'nipype.pipeline.plugins.tests',
                           'nipype.pipeline.tests',
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
          # The package_data spec has no effect for me (on python 2.6) -- even
          # changing to data_files doesn't get this stuff included in the source
          # distribution -- not sure if it has something to do with the magic
          # above, but distutils is surely the worst piece of code in all of
          # python -- duplicating things into MANIFEST.in but this is admittedly
          # only a workaround to get things started -- not a solution
          package_data = {'nipype':
                          [pjoin('testing', 'data', '*'),
                           pjoin('testing', 'data', 'dicomdir', '*'),
                           pjoin('testing', 'data', 'bedpostxout', '*'),
                           pjoin('testing', 'data', 'tbss_dir', '*'),
                           pjoin('workflows', 'data', '*'),
                           pjoin('pipeline', 'report_template.html'),
                           pjoin('external', 'd3.js'),
                           pjoin('interfaces', 'script_templates', '*'),
                           pjoin('interfaces', 'tests', 'realign_json.json')
                          ]},
          scripts      = glob('bin/*'),
          cmdclass = cmdclass,
          **extra_args
         )

if __name__ == "__main__":
    main(**extra_setuptools_args)
