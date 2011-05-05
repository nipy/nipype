#------------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license.

#
# Author: Enthought Inc
# Description: Qt API selector. Can be used to switch between pyQt and PySide
#------------------------------------------------------------------------------

import os

from traits.etsconfig.api import ETSConfig

qt_api = os.environ.get('QT_API', 'pyqt')

if ETSConfig.toolkit == 'qt4':

    if qt_api == 'pyqt':
        import sip
        sip.setapi('QString', 2)
        sip.setapi('QVariant', 2)

    else:
        print "---- using PySide ----"
