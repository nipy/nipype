"""Monkeypatch nose to accept any callable as a method.

By default, nose's ismethod() fails for static methods.
Once this is fixed in upstream nose we can disable it.

Note: merely importing this module causes the monkeypatch to be applied."""

import unittest
import nose.loader

def getTestCaseNames(self, testCaseClass):
    """Override to select with selector, unless
    config.getTestCaseNamesCompat is True
    """
    if self.config.getTestCaseNamesCompat:
        return unittest.TestLoader.getTestCaseNames(self, testCaseClass)

    def wanted(attr, cls=testCaseClass, sel=self.selector):
        item = getattr(cls, attr, None)
        # MONKEYPATCH: replace this:
        #if not ismethod(item):
        # With:
        if not hasattr(item, '__call__'):
        # END MONKEYPATCH
            return False
        return sel.wantMethod(item)
    cases = filter(wanted, dir(testCaseClass))
    for base in testCaseClass.__bases__:
        for case in self.getTestCaseNames(base):
            if case not in cases:
                cases.append(case)
    # add runTest if nothing else picked
    if not cases and hasattr(testCaseClass, 'runTest'):
        cases = ['runTest']
    if self.sortTestMethodsUsing:
        cases.sort(self.sortTestMethodsUsing)
    return cases


##########################################################################
# Apply monkeypatch here
nose.loader.TestLoader.getTestCaseNames = getTestCaseNames
##########################################################################
