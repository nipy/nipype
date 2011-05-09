#-------------------------------------------------------------------------------
#
#  Copyright (c) 2007, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in /LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#-------------------------------------------------------------------------------

""" Tests for protocols usage. """

from __future__ import absolute_import


# Standard library imports.
import pickle, unittest, os

# Enthought library imports.
from ..api import (Bool, HasTraits, Int, Interface, Str, Adapter, adapts,
        Property)

# NOTE: There is a File class in enthought.io module, but since we want to
# eliminate dependencies of Traits on other modules, we create another
# minimal File class here to test the adapter implementation.

# Test class
class File(HasTraits):

    # The path name of this file/folder.
    path = Str

    # Is this an existing file?
    is_file = Property(Bool)

    # Is this an existing folder?
    is_folder = Property(Bool)

    def _get_is_file(self):
        """ Returns True if the path exists and is a file. """

        return os.path.exists(self.path) and os.path.isfile(self.path)

    def _get_is_folder(self):
        """ Returns True if the path exists and is a folder. """

        return os.path.exists(self.path) and os.path.isdir(self.path)


# Test class.
class Person(HasTraits):
    """ A person! """

    name = Str
    age  = Int

class ProtocolsUsageTestCase(unittest.TestCase):
    """ Tests for protocols usage. """
    def test_adapts(self):
        """ adapts """
        class IFoo(Interface):
            """ A simple interface. """
            def foo(self):
                """ The only method for the IFoo interface. """

        class Bar(HasTraits):
            """ A type that *doesn't* implement 'IFoo'. """

        class BarToIFooAdapter(Adapter):
            """ Adapts from Bar to IFoo. """
            adapts(Bar, to=IFoo)

            def foo(self):
                """ An implementation of the single method in the interface."""
                return 'foo'

        b = Bar()

        # Make sure that the Bar instance can be adapted to 'IFoo'.
        self.assertNotEqual(None, IFoo(b))
        self.assertEqual('foo', IFoo(b).foo())

    def test_factory(self):
        """ factory """

        class IInputStream(Interface):
            """ Fake interface for input stream. """

            def get_input_stream(self):
                """ Get an input stream. """

        def factory(obj):
            """ A factory for File to IInputStream adapters. """

            if not obj.is_folder:
                adapter = FileToIInputStreamAdapter(adaptee=obj)

            else:
                adapter = None

            return adapter

        class FileToIInputStreamAdapter(Adapter):
            """ An adapter from 'File' to 'IInputStream'. """

            adapts(File, to=IInputStream, factory=factory)

            ###################################################################
            # 'IInputStream' interface.
            ###################################################################

            def get_input_stream(self):
                """ Get an input stream. """

                return file(self.adaptee.path, 'r')

        # Create a reference to this file
        cwd = os.path.dirname(os.path.abspath(__file__))
        f = File(path=os.path.join(cwd, 'protocols_usage_test_case.py'))
        self.assert_(f.is_file)

        # A reference to the parent folder
        g = File(path='..')
        self.assert_(g.is_folder)

        # We should be able to adapt the file to an input stream...
        self.assertNotEqual(None, IInputStream(f, None))

        # ... but not the folder.
        self.assertEqual(None, IInputStream(g, None))

        # Make sure we can use the stream (this reads this module and makes
        # sure that it contains the right doc string).
        stream = IInputStream(f).get_input_stream()
        self.assert_('"""' + __doc__ in stream.read())

        return

    def test_when_expression(self):
        """ when expression """

        class IInputStream(Interface):
            """ Fake interface for input stream. """

            def get_input_stream(self):
                """ Get an input stream. """

        class FileToIInputStreamAdapter(Adapter):
            """ An adapter from 'File' to 'IInputStream'. """

            adapts(File, to=IInputStream, when='not adaptee.is_folder')

            ###################################################################
            # 'IInputStream' interface.
            ###################################################################

            def get_input_stream(self):
                """ Get an input stream. """

                return file(self.adaptee.path, 'r')

        # Create a reference to this file
        cwd = os.path.dirname(os.path.abspath(__file__))
        f = File(path=os.path.join(cwd, 'protocols_usage_test_case.py'))
        self.assert_(f.is_file)

        # A reference to the parent folder
        g = File(path='..')
        self.assert_(g.is_folder)

        # We should be able to adapt the file to an input stream...
        self.assertNotEqual(None, IInputStream(f, None))

        # ... but not the folder.
        self.assertEqual(None, IInputStream(g, None))

        # Make sure we can use the stream (this reads this module and makes
        # sure that it contains the right doc string).
        stream = IInputStream(f).get_input_stream()
        self.assert_('"""' + __doc__ in stream.read())

        return

    def test_cached(self):
        """ cached """

        class ISaveable(Interface):
            """ Fake interface for saveable. """

            # Is the object 'dirty'?
            dirty = Bool(False)

            def save(self, output_stream):
                """ Save the object to an output stream. """


        class HasTraitsToISaveableAdapter(Adapter):
            """ An adapter from 'HasTraits' to 'ISaveable'. """

            adapts(HasTraits, to=ISaveable, cached=True)

            #### 'ISaveable' interface ########################################

            # Is the object 'dirty'?
            dirty = Bool(False)

            def save(self, output_stream):
                """ Save the object to an output stream. """

                pickle.dump(self.adaptee, output_stream)
                self.dirty = False

                return

            #### Private interface ############################################

            def _adaptee_changed(self, old, new):
                """ Static trait change handler. """

                if old is not None:
                    old.on_trait_change(self._set_dirty, remove=True)

                if new is not None:
                    new.on_trait_change(self._set_dirty)

                self._set_dirty()

                return

            def _set_dirty(self):
                """ Sets the dirty flag to True. """

                self.dirty = True

                return

        # Create some people!
        fred  = Person(name='fred', age=42)
        wilma = Person(name='wilma', age=35)

        fred_saveable = ISaveable(fred)
        self.assertEqual(True, fred_saveable.dirty)

        wilma_saveable = ISaveable(wilma)
        self.assertEqual(True, wilma_saveable.dirty)

        # Make sure that Fred and Wilma have got their own saveable.
        self.assertNotEqual(id(fred_saveable), id(wilma_saveable))

        # But make sure that their saveable's are cached.
        self.assertEqual(id(ISaveable(fred)), id(fred_saveable))
        self.assertEqual(id(ISaveable(wilma)), id(wilma_saveable))

        # Save Fred and Wilma and make sure that the dirty flag is cleared.
        fred_saveable.save(file('fred.pickle', 'w'))
        self.assertEqual(False, ISaveable(fred).dirty)

        wilma_saveable.save(file('wilma.pickle', 'w'))
        self.assertEqual(False, ISaveable(wilma).dirty)

        # Clean up.
        for path in ['fred.pickle', 'wilma.pickle']:
           if os.access(path, os.W_OK):
               os.remove(path)

        return

    def test_multiple_factories_for_type(self):
        """ multiple factories for type """

        # There was a bug that prevented more than one adapter factory being
        # registered for the same class.
        class IFoo(Interface):
            pass

        class HasTraitsToIFooAdapter(Adapter):
            adapts(HasTraits, to=IFoo, cached=True)

        class IBar(Interface):
            pass

        class HasTraitsToIBarAdapter(Adapter):
            adapts(HasTraits, to=IBar, cached=True)

        return

    def test_multiple_factories_for_interface(self):
        """ multiple factories for interfaces """

        # There was a bug that prevented more than one adapter factory being
        # registered for the same class. This test just makes sure that it
        # still works for interfaces too!
        class IBaz(Interface):
            pass

        class IFoo(Interface):
            pass

        class IBazToIFooAdapter(Adapter):
            adapts(IBaz, to=IFoo, cached=True)

        class IBar(Interface):
            pass

        class IBazToIBarAdapter(Adapter):
            adapts(IBaz, to=IBar, cached=True)

        return


# Run the unit tests (if invoked from the command line):
if __name__ == '__main__':
    unittest.main()
