# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.utils.docparse import reverse_opt_map, build_doc, insert_doc

foo_opt_map = {'outline': '-o', 'fun': '-f %.2f', 'flags': '%s'}

foo_doc = """Usage: foo infile outfile [opts]

Bunch of options:

  -o        something about an outline
  -f <f>    intensity of fun factor

Other stuff:
  -v        verbose

"""

fmtd_doc = """Parameters
----------
outline :
     something about an outline
fun :
     <f> intensity of fun factor

Others Parameters
-----------------
  -v        verbose"""


def test_rev_opt_map():
    map = {'-f': 'fun', '-o': 'outline'}
    rev_map = reverse_opt_map(foo_opt_map)
    assert rev_map == map


def test_build_doc():
    opts = reverse_opt_map(foo_opt_map)
    doc = build_doc(foo_doc, opts)
    assert doc == fmtd_doc


inserted_doc = """Parameters
----------
infile : str
    The name of the input file
outfile : str
    The name of the output file
outline :
     something about an outline
fun :
     <f> intensity of fun factor

Others Parameters
-----------------
  -v        verbose"""


def test_insert_doc():
    new_items = ['infile : str', '    The name of the input file']
    new_items.extend(['outfile : str', '    The name of the output file'])
    newdoc = insert_doc(fmtd_doc, new_items)
    assert newdoc == inserted_doc
