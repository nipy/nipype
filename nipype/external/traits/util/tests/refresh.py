#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought util package component>
#------------------------------------------------------------------------------

# NOTE:
# This file, `refresh.py` can not be run by nosetests directly.
# It is run through `test_spawner.py`, see notes in there.

import unittest
import gc
import os
import sys
import pickle

from types import ClassType, FunctionType
from traits.util.refresh import refresh

def create_module(name, code):
    # get rid of pyc file
    remove_module(name)

    f = open(name+'.py','w')
    f.write(code)
    f.close()

def remove_module(name):
    # get rid of pyc file
    try:
        os.remove(name+'.pyc')
        os.remove(name+'.py')
    except:
        pass

class RefreshTestCase(unittest.TestCase):

    def test_old_style_class(self):

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f1 = """class Foo:
                        def method1(self):
                            return 0
                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            exec "import %s" % module_name
            exec "from %s import Foo" % module_name

            foo = Foo()
            assert(foo.method1() == 0)

            f2 = """class Foo:
                        def method1(self):
                            return 1
                        def method2(self):
                            return 1
                 """

            create_module(module_name, f2)
            refresh()

            assert(foo.method1() == 1)

            self.single_version_check("Foo")

        finally:
            remove_module(module_name)

    def test_new_style_class(self):

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f1 = """class FooNew(object):
                        def method1(self):
                            return 0
                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            exec "import %s" % module_name
            exec "from %s import FooNew" % module_name

            foo = FooNew()
            assert(foo.method1() == 0)

            f2 = """class FooNew(object):
                        def method1(self):
                            return 1
                        def method2(self):
                            return 1
                 """

            create_module(module_name, f2)
            refresh()

            assert(foo.method1() == 1)

            #self.single_version_check("FooNew")

        finally:
            remove_module(module_name)

    def test_traits_class(self):

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f1 = "from traits.api import HasTraits, Float\n" + \
                 """class FooTraits(HasTraits):
                        bar = Float(1.0)
                        def method1(self):
                            return 0
                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            exec "import %s" % module_name
            exec "from %s import FooTraits" % module_name

            foo = FooTraits()
            assert(foo.method1() == 0)

            f2 = "from traits.api import HasTraits, Int\n" + \
                 """class FooTraits(HasTraits):
                        bar = Int(2)
                        def method1(self):
                            return 1
                        def method2(self):
                            return 1
                 """

            create_module(module_name, f2)
            refresh()

            assert(foo.method1() == 1)

            # classes derived from HasTraits seem to continue to have
            # a copy hanging around.  This doesn't really cause problems,
            # it is just a little untidy.
            #self.single_version_check("FooTraits")

        finally:
            remove_module(module_name)

    def test_traits_instance(self):

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f1 = "from traits.api import HasTraits, Float\n" + \
                 """class FooTraits(HasTraits):
                        bar = Float(1.0)
                        def method1(self):
                            return 0
                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            exec "import %s" % module_name
            exec "from %s import FooTraits" % module_name

            foo = FooTraits()
            assert(foo.method1() == 0)

            f2 = "from traits.api import HasTraits, Int\n" + \
                 """class FooTraits(HasTraits):
                        bar = Int(2)
                        def method1(self):
                            return 1
                        def method2(self):
                            return 1
                 """

            create_module(module_name, f2)
            refresh()

            assert(foo.method1() == 1)

            # classes derived from HasTraits seem to continue to have
            # a copy hanging around.  This doesn't really cause problems,
            # it is just a little untidy.
            #self.single_version_check("FooTraits")

        finally:
            remove_module(module_name)

    def test_inheritance_class(self):

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f0 = """class Bar:
                        def method1(self):
                            return -1
                        def method2(self):
                            return -1
                 """
            create_module('bar_test', f0)

            f1 = "import bar_test\n" + \
                 """class FooSub(bar_test.Bar):
                        def method1(self):
                            return 0
                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            from bar_test import Bar
            bar = Bar()
            assert(bar.method1() == -1)

            exec "import %s" % module_name
            exec "from %s import FooSub" % module_name

            foo = FooSub()
            assert(foo.method1() == 0)

            f2 = """class FooSub:
                        def method1(self):
                            return 1
                        def method2(self):
                            return 1
                 """

            create_module(module_name, f2)
            refresh()

            # test method calls
            assert(foo.method1() == 1)
            assert(bar.method1() == -1)

            # isinstance

            assert(isinstance(foo, Bar))
            assert(isinstance(foo, FooSub))
            assert(isinstance(bar, Bar))

            # classes derived from object seem to continue to have
            # a copy hanging around.  This doesn't really cause problems,
            # it is just a little untidy.
            #self.single_class_check()

        finally:
            remove_module(module_name)
            remove_module('bar_test')

    def test_inheritance_class2(self):
        """ Change the base class definition and make sure that
            existing subclasses still behaves like the new
            base class.
        """

        module_name = 'foo_test2'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f0 = """class Bar:
                        def method1(self):
                            return -1
                        def method2(self):
                            return -1
                 """
            create_module('bar_test2', f0)

            f1 = "from bar_test2 import Bar\n" + \
                 """class FooSub(Bar):
                        def method1(self):
                            #print "base", self.__class__.__bases__
                            #print "Bar", repr(Bar)
                            #print "method1 im_class", repr(Bar.method1.im_class)
                            #print 'is instance:', isinstance(self, Bar)
                            result = Bar.method1(self)

                            return result

                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            from bar_test2 import Bar
            bar = Bar()
            assert(bar.method1() == -1)

            exec "import %s" % module_name
            exec "from %s import FooSub" % module_name

            foo = FooSub()
            assert(foo.method1() == -1)

            f2 = """class Bar:
                        def method1(self):
                            return -2
                        def method2(self):
                            return -1
                 """
            create_module('bar_test2', f2)
            refresh()

            assert(foo.method1() == -2)
            assert(bar.method1() == -2)

            # classes derived from object seem to continue to have
            # a copy hanging around.  This doesn't really cause problems,
            # it is just a little untidy.
            #self.single_class_check()

        finally:
            remove_module(module_name)
            remove_module('bar_test2')

    def test_pickle(self):
        # not sure this is really a worth while test.  It was added
        # based on some errors I (eric) was getting when testing in
        # envisage, but I am now not sure that the errors were refresh()
        # related.  Regardless, I have left the test here since it
        # doesn't do any harm, and I may need it in the future.

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f1 = """class FooNew(object):
                        def method1(self):
                            return 0
                        def method2(self):
                            return 0
                 """

            create_module(module_name, f1)

            exec "import %s" % module_name
            exec "from %s import FooNew" % module_name

            foo = FooNew()
            assert(foo.method1() == 0)

            f2 = """class FooNew(object):
                        def method1(self):
                            return 1
                        def method2(self):
                            return 1
                 """

            create_module(module_name, f2)
            refresh()

            assert(foo.method1() == 1)

            foo2 = pickle.loads(pickle.dumps(foo))

            assert(foo2.method1() == 1)

            #self.single_version_check("FooNew")
        finally:
            remove_module(module_name)

    def test_function(self):

        module_name = 'foo_test'

        try:
            # clean out any existing versions of foo_test in memory
            try:
                del sys.modules[module_name]
            except:
                pass

            f1 = """def foo(): return 0 """

            create_module(module_name, f1)

            exec "import %s" % module_name
            exec "from %s import foo" % module_name

            assert(foo() == 0)

            f2 = """def foo():
                        return 1
                 """

            create_module(module_name, f2)
            refresh()

            assert(foo() == 1)

            # fixme: this is failing with our new reload scheme
            self.single_version_check("foo", FunctionType)

        finally:
            remove_module(module_name)

    def single_version_check(self, name, types=(ClassType, type)):
        # Force garbage collection to ensure Python cleans up all
        # references to the reloaded class
        gc.collect()

        # now search the objects and make sure only one version of the
        # given class exists.
        gc_objs = gc.get_objects()
        versions = [obj for obj in gc_objs
                    if isinstance(obj, types) and
                    obj.__name__ == name]

        #there can be only one...
        assert len(versions) == 1


if __name__ == "__main__":
    unittest.main()
