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

Python_ 2.5 or 2.6 

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

`simplejson <http://pypi.python.org/pypi/simplejson/2.0.9>`_
  json is included in Python 2.6, but if you are using Python 2.5 you
  will need to install simplejson.

Enthought_ Traits_ 3.2.0 or later

nibabel 1.0.0 or later

Note
~~~~
Full distributions such as pythonxy_ or EPD_ provide the above
packages. 

Strong Recommendations
~~~~~~~~~~~~~~~~~~~~~~

Matplotlib_
  Python plotting library.

Sphinx_
  Required for building the documentation

`Graphviz <http://www.graphviz.org/>`_
  Required for building the documentation

Interface Dependencies
~~~~~~~~~~~~~~~~~~~~~~

These are the software packages that nipype.interfaces wraps:

FSL_
  4.1.0 or later

matlab_ 
  2008a or later

SPM_
  SPM5/8

FreeSurfer_
  FreeSurfer version 4 and higher
  
AFNI_
  2009_12_31_1431 or later

Slicer_
 3.6 or later

Download
--------

Download the latest release from `our github
page. <http://github.com/nipy/nipype>`_

To check out the latest development version::
 
        git clone git://github.com/nipy/nipype.git

Install
-------

The installation process is similar to other Python packages so it
will be familiar if you have Python experience.

From source
~~~~~~~~~~~

If you downloaded the source distribution named something
like ``nipype-x.y.tar.gz``, then unpack the tarball, change into the
``nipype-x.y`` directory and install nipype using::

    python setup.py install

**Note:** Depending on permissions you may need to use ``sudo``.

From egg
~~~~~~~~

If you downloaded an egg, named something like
``nipype-x.y-py2.5.egg``, then install nipype using::

    easy_install nipype-x.y-py2.5.egg


Testing the install
-------------------

The best way to test the install is to run the test suite.  If you
have nose_ installed, then do the following in ipython_::

    import nipype
    nipype.test()

All tests should pass (unless you're missing a dependency). If any tests
fail, please report them on our `bug tracker
<http://github.com/nipy/nipype/issues>`_.

On Debian systems, set the following environment variable before running
tests::

       export MATLABCMD=$pathtomatlabdir/bin/$platform/MATLAB

where, $pathtomatlabdir is the path to your matlab installation and
$platform is the directory referring to x86 or x64 installations
(typically glnxa64 on 64-bit installations).


.. include:: ../links_names.txt
