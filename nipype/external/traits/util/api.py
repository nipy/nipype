import sys

from deprecated import deprecated
from synchronized import synchronized

def called_from(levels=1, context=1):
    """ Prints the caller's stack info """
    print '***** Deprecated.  Please use enthought.debug.called_from'
    from inspect import stack
    stk = stack(context)
    frame, file_name, line_num, func_name, lines, index = stk[1]
    print "'%s' called from:" % func_name
    for frame_rec in stk[2: 2 + levels]:
        frame, file_name, line_num, func_name, lines, index = frame_rec
        print '   %s (%s: %d)' % (func_name, file_name, line_num)
        if lines is not None:
            if len(lines) == 1:
                print '      ' + lines[0].strip()[:73]
            else:
                for i, line in enumerate( lines ):
                    print '   %s  %s' % ('|>'[ i == index ], line.rstrip())


# command line version
def test(level=1, verbosity=1):
    pass
    # The stuff below is broken, and seems obsolete since we use nosetests.
    #import unittest
    #runner = unittest.TextTestRunner(verbosity=verbosity)
    #runner.run(test_suite(level))
    #return runner


# returns a test suite for use elsewhere
def test_suite(level=1):
    pass
    # The stuff below is broken, and seems obsolete since we use nosetests.
    #import traits.util
    #import traits.util.testingx as testing
    #return testing.harvest_test_suites(traits.util,level=level)
