#!/usr/bin/env python
"""Run the py->rst conversion and run all examples.

This also creates the index.rst file appropriately, makes figures, etc.

"""
import os
import sys
from glob import glob
import runpy
from toollib import sh

# We must configure the mpl backend before making any further mpl imports
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

examples_header = """

.. _examples:

Examples
========

.. note_about_examples
"""
# -----------------------------------------------------------------------------
# Function defintions
# -----------------------------------------------------------------------------

# These global variables let show() be called by the scripts in the usual
# manner, but when generating examples, we override it to write the figures to
# files with a known name (derived from the script name) plus a counter
figure_basename = None

# We must change the show command to save instead


def show():
    from matplotlib._pylab_helpers import Gcf
    allfm = Gcf.get_all_fig_managers()
    for fcount, fm in enumerate(allfm):
        fm.canvas.figure.savefig("%s_%02i.png" % (figure_basename, fcount + 1))


_mpl_show = plt.show
plt.show = show

# -----------------------------------------------------------------------------
# Main script
# -----------------------------------------------------------------------------

exclude_files = ['-x %s' % sys.argv[i + 1] for i, arg in enumerate(sys.argv) if arg == '-x']

tools_path = os.path.abspath(os.path.dirname(__file__))
ex2rst = os.path.join(tools_path, 'ex2rst')
# Work in examples directory
os.chdir("users/examples")
if not os.getcwd().endswith("users/examples"):
    raise OSError("This must be run from doc/examples directory")

# Run the conversion from .py to rst file
sh("%s %s --project Nipype --outdir . ../../../examples" % (ex2rst, ' '.join(exclude_files)))
sh("""%s --project Nipype %s --outdir . ../../../examples/frontiers_paper""" % (
    ex2rst, ' '.join(exclude_files)))

# Make the index.rst file
"""
index = open('index.rst', 'w')
index.write(examples_header)
for name in [os.path.splitext(f)[0] for f in glob('*.rst')]:
    #Don't add the index in there to avoid sphinx errors and don't add the
    #note_about examples again (because it was added at the top):
    if name not in(['index','note_about_examples']):
        index.write('   %s\n' % name)
index.close()
"""

# Execute each python script in the directory.
if "--no-exec" in sys.argv:
    pass
else:
    if not os.path.isdir("fig"):
        os.mkdir("fig")

    for script in glob("*.py"):
        figure_basename = os.path.join("fig", os.path.splitext(script)[0])
        runpy.run_path(script)
        plt.close("all")
