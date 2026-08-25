import importlib
import os
import shutil
import tempfile
import pytest
import numpy as np
import py.path as pp

NIPYPE_DATADIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "testing/data")
)
NIPYPE_TMPDIR = tempfile.mkdtemp()
TMP_DATADIR = os.path.join(NIPYPE_TMPDIR, "data")


def pytest_configure(config):
    global TMP_DATADIR
    # Pytest uses gettempdir() to construct its tmp_paths, but the logic to get
    # `pytest-of-<user>/pytest-<n>` directories is contingent on not directly
    # configuring the `config.option.base_temp` value.
    # Instead of replicating that logic, inject a new directory into gettempdir()
    #
    # Use the discovered temp dir as a base, to respect user/system settings.
    if ' ' not in (base_temp := tempfile.gettempdir()):
        new_base = os.path.join(base_temp, "nipype tmp")
        os.makedirs(new_base, exist_ok=True)
        os.environ['TMPDIR'] = new_base
        importlib.reload(tempfile)
        assert tempfile.gettempdir() == new_base
        TMP_DATADIR = os.path.join(new_base, "data")

    # xdist will result in this being run multiple times
    if not os.path.exists(TMP_DATADIR):
        shutil.copytree(NIPYPE_DATADIR, TMP_DATADIR)


def pytest_unconfigure(config):
    shutil.rmtree(NIPYPE_TMPDIR)


if "SUBJECTS_DIR" not in os.environ:
    os.environ["SUBJECTS_DIR"] = NIPYPE_TMPDIR


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace["np"] = np
    doctest_namespace["os"] = os
    doctest_namespace["pytest"] = pytest
    doctest_namespace["datadir"] = TMP_DATADIR


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
        tmpdir = pp.local(TMP_DATADIR)

        # Chdir only for the duration of the test.
        with tmpdir.as_cwd():
            yield

    else:
        # For normal tests, we have to yield, since this is a yield-fixture.
        yield
