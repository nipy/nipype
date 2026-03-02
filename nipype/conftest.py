import os
import shutil
from tempfile import mkdtemp
import pytest
import numpy as np
import py.path as pp

NIPYPE_DATADIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "testing/data")
)
temp_folder = mkdtemp()
data_dir = os.path.join(temp_folder, "data")
shutil.copytree(NIPYPE_DATADIR, data_dir)


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace["np"] = np
    doctest_namespace["os"] = os
    doctest_namespace["pytest"] = pytest
    doctest_namespace["datadir"] = data_dir


@pytest.fixture(scope='session', autouse=True)
def legacy_printoptions():
    np.set_printoptions(legacy='1.21')


@pytest.fixture(autouse=True)
def _docdir(request):
    """Grabbed from https://stackoverflow.com/a/46991331"""
    # Trigger ONLY for the doctests.
    doctest_plugin = request.config.pluginmanager.getplugin("doctest")
    if isinstance(request.node, doctest_plugin.DoctestItem):
        # Get the fixture dynamically by its name.
        tmpdir = pp.local(data_dir)

        # Chdir only for the duration of the test.
        with tmpdir.as_cwd():
            yield

    else:
        # For normal tests, we have to yield, since this is a yield-fixture.
        yield


def pytest_unconfigure(config):
    # Delete temp folder after session is finished
    shutil.rmtree(temp_folder)
