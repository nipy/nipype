.. _install:

======================
 Download and install
======================

This page covers the necessary steps to install nipype.  Below is a
list of required dependencies, along with additional software
recommendations.

Dependencies
------------

Must Have
~~~~~~~~~

Python_ 2.5 or later
  We are currently looking at lowering this dependency to python 2.4

NumPy_ 1.3 or later

SciPy_ 0.7 or later
  Numpy and Scipy are high-level, optimized scientific computing libraries.

NetworkX_ 1.0dev
  Our releases will depend on a release of NetworkX.


Strong Recommandations
~~~~~~~~~~~~~~~~~~~~~~

IPython_
  Interactive python environment. This is necessary for the parallel
  components of the pipeline engine.

Matplotlib_
  Python plotting library.


Installing from binary packages
-------------------------------

This will be possible once we `release.
<https://sourceforge.net/apps/trac/nipy/roadmap>`_


Building from source
--------------------

The installation process is similar to other Python packages so it
will be familiar if you have Python experience.

Unpack the tarball and change into the source directory.  Once in the
source directory, you can build the neuroimaging package using::

    python setup.py install

Or::

    sudo python setup.py install

.. include:: ../links_names.txt
