# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration('interfaces', parent_package, top_path)

    config.add_subpackage('afni')
    config.add_subpackage('camino')
    config.add_subpackage('camino2trackvis')
    config.add_subpackage('cmtk')
    config.add_subpackage('diffusion_toolkit')
    config.add_subpackage('freesurfer')
    config.add_subpackage('fsl')
    config.add_subpackage('mrtrix')
    config.add_subpackage('nipy')
    config.add_subpackage('spm')
    config.add_subpackage('slicer')

    config.add_data_dir('script_templates')
    config.add_data_dir('tests')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
