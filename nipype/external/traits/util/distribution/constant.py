#------------------------------------------------------------------------------
# Copyright (c) 2007, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought statistical distribution package component>
#------------------------------------------------------------------------------

import numpy

from traits.api import Float
from traitsui.api import View, Item

from distribution import Distribution

class Constant(Distribution):
    """ A constant distribution where all values are the same """
    value = Float

    traits_view = View(Item('value'))

    def _get_value(self, n):
        return numpy.repeat(self.value, n)
