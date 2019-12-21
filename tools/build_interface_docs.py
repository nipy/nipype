#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Script to auto-generate interface docs.
"""
# stdlib imports
import os
import sys

# *****************************************************************************
if __name__ == "__main__":
    nipypepath = os.path.abspath("..")
    sys.path.insert(1, nipypepath)
    # local imports
    from apigen import InterfaceHelpWriter

    package = "nipype"
    outdir = os.path.join("interfaces", "generated")
    docwriter = InterfaceHelpWriter(package)
    # Packages that should not be included in generated API docs.
    docwriter.package_skip_patterns += [
        r"\.external$",
        r"\.fixes$",
        r"\.utils$",
        r"\.pipeline",
        r"\.testing",
        r"\.caching",
        r"\.scripts",
        r"\.sphinxext$",
        r"\.workflows"
    ]
    # Modules that should not be included in generated API docs.
    docwriter.module_skip_patterns += [
        r"\.conftest",
        r"\.interfaces\.base$",
        r"\.interfaces\.matlab$",
        r"\.interfaces\.pymvpa$",
        r"\.interfaces\.rest$",
        r"\.interfaces\.slicer\.generate_classes$",
        r"\.interfaces\.spm\.base$",
        r"\.interfaces\.traits",
        r"\.pipeline\.alloy$",
        r"\.pipeline\.s3_node_wrapper$",
        r"\.pkg_info"
        r"\.scripts",
        r"\.testing",
        r"\.version$",
    ]
    docwriter.class_skip_patterns += [
        "AFNICommand",
        "ANTS",
        "FSLCommand",
        "FS",
        "Info",
        "^SPM",
        "Tester",
        "Spec$",
        "Numpy",
        # NipypeTester raises an
        # exception when instantiated in
        # InterfaceHelpWriter.generate_api_doc
        "NipypeTester",
    ]
    docwriter.write_api_docs(outdir)
    # docwriter.write_index(outdir, "gen")
    print("%d files written" % len(docwriter.written_modules))
