#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os

# local imports
from apigen import ApiDocWriter

#*****************************************************************************
if __name__ == '__main__':
    print 'In build_modref_templates.py'
    package = 'nipype'
    outdir = os.path.join('api','generated')
    docwriter = ApiDocWriter(package)
    docwriter.package_skip_patterns += [r'\.fixes$',
                                        r'\.externals$',
                                        ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen', relative_to='api')
    print '%d files written' % len(docwriter.written_modules)
