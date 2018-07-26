#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Script to auto-generate interface docs.
"""
from __future__ import print_function, unicode_literals
# stdlib imports
import os
import sys

# *****************************************************************************
if __name__ == '__main__':
    nipypepath = os.path.abspath('..')
    sys.path.insert(1, nipypepath)
    # local imports
    from interfacedocgen import InterfaceHelpWriter
    package = 'nipype'
    outdir = os.path.join('interfaces', 'generated')
    docwriter = InterfaceHelpWriter(package)
    # Packages that should not be included in generated API docs.
    docwriter.package_skip_patterns += [
        '\.external$',
        '\.fixes$',
        '\.utils$',
        '\.pipeline',
        '\.testing',
        '\.caching',
        '\.scripts',
    ]
    # Modules that should not be included in generated API docs.
    docwriter.module_skip_patterns += [
        '\.version$',
        '\.interfaces\.base$',
        '\.interfaces\.matlab$',
        '\.interfaces\.rest$',
        '\.interfaces\.pymvpa$',
        '\.interfaces\.slicer\.generate_classes$',
        '\.interfaces\.spm\.base$',
        '\.interfaces\.traits',
        '\.pipeline\.alloy$',
        '\.pipeline\.s3_node_wrapper$',
        '\.testing',
        '\.scripts',
    ]
    docwriter.class_skip_patterns += [
        'AFNICommand',
        'ANTS',
        'FSLCommand',
        'FS',
        'Info',
        '^SPM',
        'Tester',
        'Spec$',
        'Numpy'
        # NipypeTester raises an
        # exception when instantiated in
        # InterfaceHelpWriter.generate_api_doc
        'NipypeTester',
    ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen', relative_to='interfaces')
    print('%d files written' % len(docwriter.written_modules))
