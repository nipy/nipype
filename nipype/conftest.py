import pytest
import numpy
import os


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace['np'] = numpy
    doctest_namespace['os'] = os

    filepath = os.path.dirname(os.path.realpath(__file__))
    datadir = os.path.realpath(os.path.join(filepath, 'testing/data'))
    doctest_namespace["datadir"] = datadir
