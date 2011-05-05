def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('traits', parent_package, top_path)

    config.add_subpackage('protocols')
    config.add_subpackage('etsconfig')
    config.add_subpackage('logger')
    config.add_subpackage('qt')
    config.add_subpackage('util')
    config.add_extension('ctraits',
                         sources = ['ctraits.c'],
                         extra_compile_args = ['-DNDEBUG=1', '-O3'])
    config.add_extension('protocols._speedups',
                         sources = ['protocols/_speedups.c'],
                         extra_compile_args = ['-DNDEBUG=1', '-O3'],
                         )
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
