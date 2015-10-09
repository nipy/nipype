# We import numpy fixes during init of the testing package.  We need to delay
# import of the testing package until after it has initialized

from os.path import dirname

# Cache for the actual testing functin
_tester = None

def test(*args, **kwargs):
    """ test function for fixes subpackage

    This function defers import of the testing machinery so it can import from
    us first.

    See nipy.test docstring for parameters and return values
    """
    global _tester
    if _tester is None:
        from nipy.testing import Tester
        _tester = Tester(dirname(__file__)).test
    return _tester(*args, **kwargs)

# Remind nose not to test the test function
test.__test__ = False
