# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration('workflows', parent_package, top_path)

    config.add_subpackage('data')
    config.add_data_dir('data')
    config.add_subpackage('dmri')
    config.add_subpackage('fmri')
    config.add_subpackage('graph')
    config.add_subpackage('misc')
    config.add_subpackage('rsfmri')
    config.add_subpackage('smri')
    config.add_subpackage('warp')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
