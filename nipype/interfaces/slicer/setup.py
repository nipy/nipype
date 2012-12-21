# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration('slicer', parent_package, top_path)

    config.add_data_dir('diffusion')
    config.add_data_dir('segmentation')
    config.add_data_dir('filtering')
    config.add_data_dir('quantification')
    config.add_data_dir('legacy')
    config.add_data_dir('registration')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
