# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
''' Null tester to signal nose tests disabled

Merely returns error reporting lack of nose package or version number
below requirements.

See pkgtester, nosetester modules

'''

class NullTester(object):
    def test(self, labels=None, *args, **kwargs):
        raise ImportError, \
              'Need nose >=0.10 for tests - see %s' % \
              'http://somethingaboutorange.com/mrl/projects/nose'
    bench = test
