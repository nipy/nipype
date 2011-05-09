import os

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('external', parent_package, top_path)

    config.add_extension('traits.ctraits',
                         sources = ['traits/ctraits.c'],
                         extra_compile_args = ['-DNDEBUG=1', '-O3'])
    config.add_extension('traits.protocols._speedups',
                         sources = ['traits/protocols/_speedups.c'],
                         extra_compile_args = ['-DNDEBUG=1', '-O3'],
                         )
    config.add_subpackage('traits')
    config.add_subpackage('traits.protocols')
    config.add_subpackage('traits.etsconfig')
    config.add_subpackage('traits.logger')
    config.add_subpackage('traits.qt')
    config.add_subpackage('traits.util')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
