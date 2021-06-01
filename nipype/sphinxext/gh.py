"""Build a file URL."""
import os
import inspect
import subprocess

REVISION_CMD = "git rev-parse --short HEAD"


def _get_git_revision():
    # Comes from scikit-learn
    # https://github.com/scikit-learn/scikit-learn/blob/master/doc/sphinxext/github_link.py
    try:
        revision = subprocess.check_output(REVISION_CMD.split()).strip()
    except (subprocess.CalledProcessError, OSError):
        return None
    return revision.decode("utf-8")


def get_url(obj):
    """Return local or remote url for an object."""
    filename = inspect.getsourcefile(obj)
    uri = "file://%s" % filename
    revision = _get_git_revision()
    if revision is not None:
        shortfile = os.path.join("nipype", filename.split("nipype/")[-1])
        uri = "http://github.com/nipy/nipype/blob/%s/%s" % (revision, shortfile)
    lines, lstart = inspect.getsourcelines(obj)
    lend = len(lines) + lstart
    return "%s#L%d-L%d" % (uri, lstart, lend)
