#-------------------------------------------------------------------------------
#
#  Copyright (c) 2007, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in /LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#-------------------------------------------------------------------------------

from __future__ import absolute_import

from cPickle import dumps, loads
import unittest

from ..api import Dict, HasTraits, Int, List

class C(HasTraits):

    # A dict trait containing a list trait
    a = Dict(Int, List(Int))

    # And we must initialize it to something non-trivial
    def __init__(self):
        super(C, self).__init__()
        self.a = {1 : [2,3]}

class PickleValidatedDictTestCase(unittest.TestCase):
    def test(self):

        # And we must unpickle one
        x = dumps(C())
        try:
            loads(x)
        except AttributeError, e:
            self.fail('Unpickling raised an AttributeError: %s' % e)

