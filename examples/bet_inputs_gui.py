# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This example demonstrates how one can use Traits to generate a GUI.
This requires TraitsUI to be installed.  You can find more information
about TraitsUI here:

  http://code.enthought.com/projects/traits_gui/

If you run this example from ipython you can then query the bet.inputs
and see that updating the values in the GUI will update the values in
the ipython bet instance.  Remember to start ipython with threading
support for you GUI backend:

  ipython -wthread

"""

import os
import tempfile

import enthought.traits.api as traits

from nipype.interfaces import fsl

# Make fake input file
_, fname = tempfile.mkstemp()

bet = fsl.BET()
bet.inputs.in_file = fname

# WX blows up when trying to handle boolean "CheckBox" widgets with
# value of type 'undefined' instead of type 'bool'.  Loop over inputs
# and set any 'undefined' to False.
for attr, trt in bet.inputs.traits().items():
    if isinstance(trt.trait_type, traits.Bool):
        if getattr(bet.inputs, attr) == traits.Undefined:
            setattr(bet.inputs, attr, False)

bet.inputs.configure_traits()

# Remove fake input file
os.remove(fname)
