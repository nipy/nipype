.. _dev_testing_nipype:

==============
Testing nipype
==============

In order to ensure the stability of each release of Nipype, the project uses two
continuous integration services: `CircleCI <https://circleci.com/gh/nipy/nipype/tree/master>`_
and `Travis CI <https://travis-ci.org/nipy/nipype>`_.
If both batteries of tests are passing, the following badges should be shown in green color:

.. image:: https://travis-ci.org/nipy/nipype.png?branch=master
  :target: https://travis-ci.org/nipy/nipype

.. image:: https://circleci.com/gh/nipy/nipype/tree/master.svg?style=svg
  :target: https://circleci.com/gh/nipy/nipype/tree/master


Installation for developers
---------------------------

To check out the latest development version::

    git clone https://github.com/nipy/nipype.git

After cloning::

    cd nipype
    pip install -r requirements.txt
    pip install -e .[dev]


Test implementation
-------------------

Nipype testing framework is built upon `pytest <http://doc.pytest.org/en/latest/>`_.

After installation in developer mode, the tests can be run with the
following command at the root folder of the project ::

     pytest -v --doctest-modules nipype


A successful test run should complete in 10-30 minutes and end with
something like::

    ----------------------------------------------------------------------
    2445 passed, 41 skipped, 7 xfailed in 1277.66 seconds



No test should fail (unless you're missing a dependency). If the ``SUBJECTS_DIR```
environment variable is not set, some FreeSurfer related tests will fail.
If any of the tests failed, please report them on our `bug tracker
<http://github.com/nipy/nipype/issues>`_.

On Debian systems with a local copy of MATLAB installed, set the following 
environment variable before running tests::

       export MATLABCMD=$pathtomatlabdir/bin/$platform/MATLAB

where ``$pathtomatlabdir`` is the path to your matlab installation and
``$platform`` is the directory referring to x86 or x64 installations
(typically ``glnxa64`` on 64-bit installations).

Skipped tests
~~~~~~~~~~~~~

Nipype will skip some tests depending on the currently available software and data
dependencies. Installing software dependencies and downloading the necessary data
will reduce the number of skipped tests.

A few tests in Nipype make use of some images distributed within the `FSL course data
<http://fsl.fmrib.ox.ac.uk/fslcourse/>`_. This reduced version of the package can be downloaded `here
<https://files.osf.io/v1/resources/nefdp/providers/osfstorage/57f472cf9ad5a101f977ecfe>`_.
To enable the tests depending on these data, just unpack the targz file and set the :code:`FSL_COURSE_DATA` environment
variable to point to that folder. 
Note, that the test execution time can increase significantly with these additional tests.  


Xfailed tests
~~~~~~~~~~~~~

Some tests are expect to fail until the code will be changed or for other reasons.


Testing Nipype using Docker
---------------------------

Nipype is tested inside Docker containers and users can use nipype images to test local versions. 
First, install the `Docker Engine <https://docs.docker.com/engine/installation/>`_.
Nipype has one base docker image called nipype/nipype:base, that contains several useful tools
 (FreeSurfer, AFNI, FSL, ANTs, etc.), and additional test images
for specific Python versions: py27 for Python 2.7 and py36 for Python 3.6.

Users can pull the nipype image for Python 3.6 as follows::
  
  docker pull nipype/nipype:py36

In order to test a local version of nipype you can run test within container as follows::

  docker run -it -v $PWD:/src/nipype --rm nipype/nipype:py36 py.test -v --doctest-modules /src/nipype/nipype


Additional comments
-------------------

If the project is tested both on your local OS and within a Docker container, you might have to remove all 
``__pycache__`` directories before switching between your OS and a container.
