#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os
import sys

#*****************************************************************************
if __name__ == '__main__':
    nipypepath = os.path.abspath('..')
    sys.path.insert(1, nipypepath)
    package = 'nipype'
    # local imports
    from apigen import ApiDocWriter
    outdir = os.path.join('api', 'generated')
    docwriter = ApiDocWriter(package)
    # Packages that should not be included in generated API docs.
    docwriter.package_skip_patterns += ['\.external$',
                                        '\.utils$',
                                        '\.interfaces\.',
                                        '\.workflows$',
                                        '\.pipeline\.plugins$',
                                        '\.testing$',
                                        '\.fixes$',
                                        '\.algorithms$',
                                        ]
    # Modules that should not be included in generated API docs.
    docwriter.module_skip_patterns += ['\.version$',
                                       '\.interfaces\.(?!(base|matlab))',
                                       '\.pipeline\.utils$',
                                       '\.interfaces\.pymvpa$',
                                       ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen', relative_to='api')
    print '%d files written' % len(docwriter.written_modules)
