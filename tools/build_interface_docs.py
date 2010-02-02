#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os
import sys

# local imports
from interfacedocgen import InterfaceHelpWriter

#*****************************************************************************
if __name__ == '__main__':
    nipypepath = os.path.abspath('..')
    sys.path.insert(1,nipypepath)
    package = 'nipype'
    outdir = os.path.join('interfaces','generated')
    docwriter = InterfaceHelpWriter(package)
    # Packages that should not be included in generated API docs.
    docwriter.package_skip_patterns += ['\.externals$',
                                        '\.utils$',
                                        '\.pipeline',
                                        '.\testing',
                                        '\.interfaces\.gorlin_glue',
                                        ]
    # Modules that should not be included in generated API docs.
    docwriter.module_skip_patterns += ['\.version$',
                                       '\.interfaces\.afni$',
                                       '\.interfaces\.base$',
                                       '\.interfaces\.matlab$',
                                       '\.interfaces\.rest$',
                                       '\.interfaces\.pymvpa$',
                                       '\.pipeline\.alloy$',
                                       '\.pipeline\.s3_node_wrapper$',
                                       ]
    docwriter.class_skip_patterns += ['FSL',
                                      'spm.\SpecifyModel',
                                      'SpmInfo',
                                      'FSCommandLine',
                                      'SpmMatlab'
                                      ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen', relative_to='interfaces')
    print '%d files written' % len(docwriter.written_modules)
