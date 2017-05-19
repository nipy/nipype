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
    python setup.py develop

or::

    cd nipype
    pip install -r requirements.txt
    pip install -e .[tests]



Test implementation
-------------------

Nipype testing framework is built upon `pytest <http://doc.pytest.org/en/latest/>`_.
By the time these guidelines are written, Nipype implements 17638 tests.

After installation in developer mode, the tests can be run with the
following simple command at the root folder of the project ::

    make tests

If ``make`` is not installed in the system, it is possible to run the tests using::

     py.test --doctest-modules --cov=nipype nipype


A successful test run should complete in 10-30 minutes and end with
something like::

    ----------------------------------------------------------------------
    2445 passed, 41 skipped, 7 xfailed in 1277.66 seconds



No test should fail (unless you're missing a dependency). If the ``SUBJECTS_DIR```
environment variable is not set, some FreeSurfer related tests will fail.
If any of the tests failed, please report them on our `bug tracker
<http://github.com/nipy/nipype/issues>`_.

On Debian systems, set the following environment variable before running
tests::

       export MATLABCMD=$pathtomatlabdir/bin/$platform/MATLAB

where ``$pathtomatlabdir`` is the path to your matlab installation and
``$platform`` is the directory referring to x86 or x64 installations
(typically ``glnxa64`` on 64-bit installations).

Skip tests
~~~~~~~~~~

Nipype will skip some tests depending on the currently available software and data
dependencies. Installing software dependencies and downloading the necessary data
will reduce the number of skip tests.

Some tests in Nipype make use of some images distributed within the `FSL course data
<http://fsl.fmrib.ox.ac.uk/fslcourse/>`_. This reduced version of the package can be downloaded `here
<https://files.osf.io/v1/resources/nefdp/providers/osfstorage/57f472cf9ad5a101f977ecfe>`_.
To enable the tests depending on these data, just unpack the targz file and set the :code:`FSL_COURSE_DATA` environment
variable to point to that folder.

Xfail tests
~~~~~~~~~~~

Some tests are expect to fail until the code will be changed or for other reasons.


Avoiding any MATLAB calls from testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On unix systems, set an empty environment variable::

    export NIPYPE_NO_MATLAB=

This will skip any tests that require matlab.


Testing Nipype using Docker
---------------------------

As of :code:`nipype-0.13`, Nipype is tested inside Docker containers. First, install the
`Docker Engine <https://docs.docker.com/engine/installation/>`_.
Nipype has one base docker image called nipype/base:latest, and several additional test images
for various Python versions.

The base nipype image is built as follows::

  cd path/to/nipype/
  docker build -t nipype/base:latest -f docker/base.Dockerfile .

This base image contains several useful tools (FreeSurfer, AFNI, FSL, ANTs, etc.),
but not nipype.

It is possible to fetch a built image from the latest master branch of nipype
using::

  docker run -it --rm nipype/nipype:master


The docker run command will then open the container and offer a bash shell for the
developer.

For building a continer for running nipype in Python 3.6::

  cd path/to/nipype/
  docker build -f Dockerfile -t nipype/nipype_test:py36 .
  docker run -it --rm -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" \
                      -v ~/examples:/root/examples:ro \
                      -v ~/scratch:/scratch \
                      -w /root/src/nipype \
                      nipype/nipype_test:py36 /usr/bin/run_pytests.sh

The last examples assume that the example data is downladed into ~/examples and
the ~/scratch folder will be created if it does not exist previously.
