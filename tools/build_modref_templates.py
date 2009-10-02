#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os

# local imports
from apigen import ApiDocWriter

#*****************************************************************************
if __name__ == '__main__':
    package = 'nipype'
    outdir = os.path.join('api','generated')
    docwriter = ApiDocWriter(package)
    # Packages that should not be included in generated API docs.
    docwriter.package_skip_patterns += ['\.externals$',
                                        '\.utils$',
                                        ]
    # Modules that should not be included in generated API docs.
    docwriter.module_skip_patterns += ['\.version$',
                                       '\.interfaces\.afni$',
                                       '\.pipeline\.alloy$',
                                       '\.pipeline\.s3_node_wrapper$',
                                       ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen', relative_to='api')
    print '%d files written' % len(docwriter.written_modules)
