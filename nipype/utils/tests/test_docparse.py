from nipype.testing import *

from nipype.utils.docparse import reverse_opt_map, build_doc

class Foo(object):
    opt_map = {'outline': '-o', 'fun': '-f %.2f', 'flags': '%s'}

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
    rev_map = reverse_opt_map(Foo.opt_map)
    assert_equal(rev_map, map)

def test_build_doc():
    opts = reverse_opt_map(Foo.opt_map)
    doc = build_doc(foo_doc, opts)
    assert_equal(doc, fmtd_doc)

