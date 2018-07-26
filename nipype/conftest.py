import pytest
import numpy
import os

DATADIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), 'testing/data'))


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace['np'] = numpy
    doctest_namespace['os'] = os

    doctest_namespace["datadir"] = DATADIR


@pytest.fixture(autouse=True)
def in_testing(request):
    # This seems to be a reliable way to distinguish tests from doctests
    if request.function is None:
        os.chdir(DATADIR)
