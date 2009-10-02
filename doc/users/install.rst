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

NumPy_ 1.3 or later

SciPy_ 0.7 or later
  Numpy and Scipy are high-level, optimized scientific computing libraries.

NetworkX_ 1.0
  Python package for working with complex networks.

IPython_ 0.10
  Interactive python environment. This is necessary for the parallel
  components of the pipeline engine.
  
    * The IPython.kernel (parallel computing component) has the
      following dependencies:

      * `Twisted <http://twistedmatrix.com/trac/>`_
      * zope.interface: which is also a dependecy of Twisted and was
        installed automatically for me when I installed Twisted.


Strong Recommandations
~~~~~~~~~~~~~~~~~~~~~~

Matplotlib_
  Python plotting library.

Sphinx_
  Required for building the documentation

`Graphviz <http://www.graphviz.org/>`_
  Required for building the documentation

Interface Dependencies
~~~~~~~~~~~~~~~~~~~~~~

FSL_
  4.1.0 or later

matlab_ 
  2008a or later

SPM_
  currently SPM5, SPM8 will be supported in version 0.2



Getting the latest release
--------------------------

This will be possible once we `release.
<http://sourceforge.net/apps/trac/nipy/roadmap>`_

The latest release is `here <http://sourceforge.net/projects/nipy/files/latest>`_.

Building from source
--------------------

The installation process is similar to other Python packages so it
will be familiar if you have Python experience.

Unpack the tarball and change into the source directory.  Once in the
source directory, you can build the nipype using::

    python setup.py install

Or::

    sudo python setup.py install

.. include:: ../links_names.txt
