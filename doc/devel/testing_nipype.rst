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


Tests implementation
--------------------

Nipype testing framework is built upon `nose <http://nose.readthedocs.io/en/latest/>`_.
By the time these guidelines are written, Nipype implements 17638 tests.

To run the tests locally, first get nose installed::

  pip install nose


Then, after nipype is `installed in developer mode <../users/install.html#nipype-for-developers>`_,
the tests can be run with the following simple command::

  make tests


Skip tests
----------

Nipype will skip some tests depending on the currently available software and data
dependencies. Installing software dependencies and downloading the necessary data
will reduce the number of skip tests.

Some tests in Nipype make use of some images distributed within the `FSL course data
<http://fsl.fmrib.ox.ac.uk/fslcourse/>`_. This reduced version of the package can be downloaded `here
<https://3552243d5be815c1b09152da6525cb8fe7b900a6.googledrive.com/host/0BxI12kyv2olZVUswazA3NkFvOXM/nipype-fsl_course_data.tar.gz>`_.
To enable the tests depending on these data, just unpack the targz file and set the :code:`FSL_COURSE_DATA` environment
variable to point to that folder.


Testing Nipype using Docker
---------------------------

As of :code:`nipype-0.13`, Nipype is tested inside Docker containers. Once the developer
`has installed the Docker Engine <https://docs.docker.com/engine/installation/>`_, testing
Nipype is as easy as follows::

  cd path/to/nipype/
  docker build -f docker/nipype_test/Dockerfile_py27 -t nipype/nipype_test:py27
  docker run -it --rm -v /etc/localtime:/etc/localtime:ro \
                      -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" \
                      -v ~/examples:/root/examples:ro \
                      -v ~/scratch:/scratch \
                      -w /root/src/nipype \
                      nipype/nipype_test:py27 /usr/bin/run_nosetests.sh

For running nipype in Python 3.5::

  cd path/to/nipype/
  docker build -f docker/nipype_test/Dockerfile_py35 -t nipype/nipype_test:py35
  docker run -it --rm -v /etc/localtime:/etc/localtime:ro \
                      -e FSL_COURSE_DATA="/root/examples/nipype-fsl_course_data" \
                      -v ~/examples:/root/examples:ro \
                      -v ~/scratch:/scratch \
                      -w /root/src/nipype \
                      nipype/nipype_test:py35 /usr/bin/run_nosetests.sh
