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

from distribution import Distribution

from traits.api import Float
from traitsui.api import View, Item

class Triangular(Distribution):
    """ A triangular distribution """
    mode = Float
    low = Float
    high = Float

    traits_view = View(Item('mode'), Item('low'), Item('high'))

    def _get_value(self, n):
        return self._state.triangular(self.low, self.mode, self.high, n)
