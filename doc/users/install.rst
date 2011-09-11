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

Python_ 2.6 -2.7

Matplotlib_ 1.0
  Plotting library

NetworkX_ 1.0 - 1.4
  Python package for working with complex networks.

NumPy_ 1.3 - 1.5

SciPy_ 0.7 - 0.9
  Numpy and Scipy are high-level, optimized scientific computing libraries.

`simplejson <http://pypi.python.org/pypi/simplejson/2.0.9>`_
  json is included in Python 2.6, but if you are using Python 2.5 you
  will need to install simplejson.

Enthought_ Traits_ 4.0.0

.. note::

    Full distributions such as pythonxy_ or EPD_ provide the above packages. 

Nibabel_

Strong Recommendations
~~~~~~~~~~~~~~~~~~~~~~

IPython_ 0.10.2 or 0.11
  Interactive python environment. This is necessary for some parallel
  components of the pipeline engine.

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

Nipy_ 
  0.1.2+20110404 or later

Nitime_ 
  (optional)
  
Camino_
  
Camino2Trackvis_

ConnectomeViewer_

Download
--------

Download the latest release from `our github
page. <http://github.com/nipy/nipype>`_

To check out the latest development version::
 
        git clone git://github.com/nipy/nipype.git

Install
-------

The installation process is similar to other Python packages so it
will be familiar if you have Python experience. Nipype is also hosted on the 
PyPi repository so you can do::

	easy_install nipype

or::
	
	pip install nipype

Debian and Ubuntu
~~~~~~~~~~~~~~~~~

Add the `NeuroDebian <http://neuro.debian.org>`_ repository and install 
the ``python-nipype`` package using ``apt-get`` or your favourite package manager.

Mac OS X
~~~~~~~~

The easiest way to get nipype running on MacOSX is to install EPD_ and then add nibabel 
and nipype by executing::

	easy_install nibabel
	easy_install nipype

If you are running a 64 bit version of EPD 7.0, you will need to compile
ETS. Instructions for a 64-bit boot mode are available:  https://gist.github.com/845545
This is no longer needed in EPD 7.1.
 

From source
~~~~~~~~~~~

If you downloaded the source distribution named something
like ``nipype-x.y.tar.gz``, then unpack the tarball, change into the
``nipype-x.y`` directory and install nipype using::

    python setup.py install

**Note:** Depending on permissions you may need to use ``sudo``.

Testing the install
-------------------

The best way to test the install is to run the test suite.  If you have
nose_ installed, then do the following::

    python -c "import nipype; nipype.test()"

you can also test with nosetests: 

::

        nosetests --with-doctest /software/nipy-repo/masternipype/nipype
        --exclude=external --exclude=testing

All tests should pass (unless you're missing a dependency). If SUBJECTS_DIR 
variable is not set some FreeSurfer related tests will fail. If any tests
fail, please report them on our `bug tracker
<http://github.com/nipy/nipype/issues>`_.

On Debian systems, set the following environment variable before running
tests::

       export MATLABCMD=$pathtomatlabdir/bin/$platform/MATLAB

where, $pathtomatlabdir is the path to your matlab installation and
$platform is the directory referring to x86 or x64 installations
(typically glnxa64 on 64-bit installations).

.. include:: ../links_names.txt
