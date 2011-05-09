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
""" Live updating of objects in system from module reloads.

    The main function exposed by this module is::

      refresh(logger=None)

    Check for edited python files for modules that are live in the
    system.  If one or more are found, reload the module in such
    a way that its new class and function definitions are used
    by all pre-existing objects in the system.  This differs from
    a simple reload(module) which makes no attempt to provide the
    freshly loaded implementations of classes to objects created
    with a previous (outdated) version of the class.

    This feature allows you to make edits to a module
    while a program is running and not have to restart the
    program to get the new behavior in the system.  It is
    particularly handy when working on large GUI applications
    where you want to update the core code in the system
    without a lengthy restart.

    Example::

        # foo.py
        class Foo:
            def method(self):
                print "hello"

        $ python
        >>> from foo import Foo
        >>> obj = Foo()
        >>> obj.method()
        hello
        #<edit file>
        # foo.py
        class Foo:
            def method(self):
                print "goodbye"
        #<end edit>
        >>> import refresh
        >>> refresh.refresh()
        # obj will now have the behavior of the updated Foo classes.
        >>> obj.method()
        goodbye

    How It works
    ------------

    In python, classes and functions are mutable objects.  Importing
    a module instantiates an instance of all the classes and functions
    defined in the module.

    Any objects instantiated from the classes have a obj.__class__
    attribute the points to the class they are based upon.  When
    you call a method on the object in your code like so::

        obj.method()

    python actually calls the method othe __class__ object like so::

        obj.__class__.method(obj)

    with obj passed in as the "self" argument.  This indirection allows
    us to dynamically change the implementation of method().

    When you edit a python module and then reload it in a python session,
    any classes within the module are reinstantiated within that module
    and any newly created objects created with a call to module.class()
    will have the behavior and methods of your freshly edited code.  But
    what about objects that are already "live" in the system that were
    created with a previous version of module.class?  Their __class__
    attribute is still pointing at the old version of the class, and so
    they will have the old behavior.  The quickest way to fix this is
    to find the old class object in the system and replace its attributes
    and methods with those of the freshly imported class.  This will
    instantly give all old objects in the system the new behavior.

    Functions are updated in a similar way.  All old versions of
    functions have their internals (func_code, etc.) replaced with
    those of the freshly loaded implementation.

    Caveats
    -------

    Their are multiple issues with trying insert a new class definition
    back into classes.  Doing this clobbers and class scope variables that
    were set at runtime.  Also, this implementation cleans out old classes
    completely before inserting new method/attributes.  That means that
    any methods dynamically added to a class are also clobbered.  There
    are ways to potentially get around this, but it isn't clear that
    it is worth the effort (at least for Enthought applications) as such
    tricks are not used very often in classes that are often edited.  When
    you do (or anytime you notice suspicious behavior), restart your
    application.

    Enthought people: While refresh() can save you time for working with
    applications, ALWAYS do a fresh restart and check that everything is
    working properly before checking edited code in.

    Questions
    ---------
    * Check out why traits classes aren't cleaned up correctly.

    * Should we get rid of functions/classes that were in old version of module
      but aren't in new one?  This could prevent problems with stale functions
      left around that really weren't meant to be, but it might also delete
      functions that "hooked" into a module...

      fix me: I think we should to prevent refactor errors.

    :copyright: 2005, Enthought, Inc.
    :author:    Eric Jones
    :license:   BSD

"""

# General Imports
import os
import sys
import gc
import logging
import compiler
from types import UnboundMethodType, FunctionType, ClassType
import linecache


#############################################################################
# Public functions
#############################################################################

def refresh(logger=None):
    """ Reload edited modules & update existing objects to new versions

        Check for edited python files for modules that are live in the
        system.  If one or more are found, reload the module in such a way
        that its new class and function definitions are used by all
        pre-existing objects in the system.  This differs from a simple
        reload(module) which makes no attempt to provide the freshly loaded
        implementations of classes to objects created with a
        previous (outdated) version of the class.

        This feature allows you to make edits to a module while a program is
        running and not have to restart the program to get the new behavior in
        the system.  It is particularly handy when working on large GUI
        applications where you want to update the core code in the system
        without a lengthy restart.

    """
    refresher = Refresher(logger)
    refresher.refresh()

#############################################################################
# Public classes
#############################################################################

class Refresher(object):
    """ Implementation of refresh().  See referesher.refresh() function for
        more information.
    """

    def __init__(self, logger=None):
        """ Create a Refesher class. If logger is None, logging.root is used.
        """
        if logger is None:
            self.logger = logging.root
        else:
            self.logger = logger


    #########################################################################
    # Public Refresh interface
    #########################################################################

    def refresh(self):
        """ Find all out-of-date modules and reload functions and classes.
        """

        # 1. Find outdated modules in sys.modules with out_of_date_modules()
        modules = out_of_date_modules()


        if not modules:
            # If there aren't any out of date modules, don't do anything...
            return

        # 2. find all the functions and clases in the system
        #    Note: Do this before you do any reloads!  Some of the
        #          sub-functions rely on reloaded functions not being
        #          in this list.
        objects = gc.get_objects()
        all_functions, all_classes = filter_functions_and_classes(objects)

        for module in modules:

            # 3. Find classes and functions that need to be updated.
            #    Note: This causes a reload of the module.
            updated_functions, updated_classes = \
                     new_functions_and_classes_for_module(module, self.logger)

            if updated_functions or updated_classes:
                # 4. now update the functions and classes affected by the refresh

                self.logger.info("Refresh module: %s" % module.__name__)
                self.logger.debug("Refresh file: %s" % module.__file__)

                self._refresh_functions(all_functions, updated_functions)
                self._refresh_classes(all_classes, updated_classes)

            # 5. Clear out the linecache used by some shells (pycrust, idle)
            #    because we just updated some modules, and they will report
            #    the wrong line numbers on exceptions.
            linecache.clearcache()

    #########################################################################
    # Private interface
    #########################################################################

    def _refresh_classes(self, all_classes, updated_classes):
        """ Replace classes from all_classes with implementation found in
            updated_classes.
        """

        for new_class in updated_classes:
            # are their any classes with the same name and module?
            matched_classes = [klass for klass in all_classes if
                                    klass.__name__ == new_class.__name__
                                and klass.__module__ == new_class.__module__]


            if len(matched_classes) == 0:
                # if no old versions are found, don't do anything...
                pass

            elif len(matched_classes) >= 1:

                # plug reloaded methods/attrs from new class into old class
                for old_class in matched_classes:

                    self.logger.debug("    %s" % old_class)

                    # We delete everything previously defined in the class.
                    # While this could delete static class scope variables
                    # set at runtime or methods dynamically attached to the
                    # class at runtime, it also cleans out any
                    # methods/attributes from previous class definitions.
                    # This prevents the chance of external code erroneously
                    # calling a method from the old class definition that
                    # isn't defined in the reloaded class.
                    #
                    # fixme: Revisit this, as there are ways to check the old
                    #        pyc files for methods that were defined in the
                    #        class and comparing that to the actual old class
                    #        to identify dynamically attached methods that
                    #        might need to remain attached.

                    new_attrs = set(new_class.__dict__.keys())
                    old_attrs = set(old_class.__dict__.keys())

                    # attributes in old_class that aren't in new class.
                    # and get rid of them.
                    clobber_attrs = old_attrs.difference(new_attrs)
                    for attr in clobber_attrs:
                        delattr(old_class, attr)

                    # some class __dict__ objects are dictproxy objects that
                    # don't support update and del correctly.  The following
                    # won't work.
                    # old_class.__dict__.update(new_class.__dict__)

                    for attr in new_attrs:

                        if (isinstance(old_class, object) and
                            attr in ["__dict__", "__doc__"]):
                            # new style classes return __dict__ as an attr
                            # and it can't be updated.
                            continue

                        new_value = getattr(new_class, attr)
                        old_value = getattr(old_class, attr, None)

                        if (isinstance(old_value, UnboundMethodType) and
                            isinstance(new_value, UnboundMethodType)):

                            # ensure that old_value is a method defined on
                            # old_class and not one of its base classes before
                            # we change it.
                            if (old_value.im_class.__name__ ==
                                old_class.__name__ and
                                old_value.im_class.__module__ ==
                                old_class.__module__):

                                # when replacing a method with a new method,
                                # update the old methods innards instead of
                                # replacing it directly in the dict.  This
                                # helps lets trait properties (and probably
                                # other things) work correctly.

                                msg = "        %s method updated" % attr
                                self.logger.debug(msg)

                                # update the functions innards.
                                self._update_function(old_value.im_func,
                                                      new_value.im_func)

                            else:

                                # The old_class.attr method was on a base
                                # class.  Don't replace its innards.  Instead
                                # overwrite it in the dict.
                                msg = "        %s updated" % attr
                                setattr(old_class, attr, new_value)

                        else:
                            self.logger.debug("        %s updated" % attr)
                            setattr(old_class, attr, new_value)

                    # The old class is now equivalent to the new class
                    # definition.  Overwrite the new class definition with
                    # the old one so that the new one becomes unused and can
                    # be garbage collected.  While not entirely necessary, it
                    # does keep things tidier.
                    mod = sys.modules[new_class.__module__]
                    name = new_class.__name__
                    setattr(mod, name, old_class)

    def _refresh_functions(self, all_functions, updated_functions):
        """ Replace functions from all_functions with implementation found in
            updated_functions.
        """

        for new_function in updated_functions:

            # Skip new_function if it doesn't have a name...
            #
            # note: added check for __name__ because a generator
            # (enthought.plugins.text_editor.editor.text_editor._id_generator)
            # was sneaking through as new_function [ I believe because of the
            # reassignment of it].  Doesn't look like there is an intelligent
            # way to handle this...
            if not hasattr(new_function,'__name__'):
                continue

            # are their any functions with the same name and module?
            matched_functions = [func for func in all_functions if
                                   func.__name__ == new_function.__name__ and
                                   func.__module__ == new_function.__module__]

            for old_function in matched_functions:
                self.logger.debug("    %s" % old_function)

                # replace old function contents with new function contents
                self._update_function(old_function, new_function)

                # The old function is now equivalent to the new function
                # definition.  Overwrite the new definition with the old
                # one so that the new one becomes unused and can
                # be garbage collected.  While not entirely necessary, it
                # does keep things tidier.
                mod = sys.modules[new_function.__module__]
                name = new_function.__name__
                setattr(mod, name, old_function)

    def _update_function(self, old_function, new_function):
        """ Update thbe old_function to have the same implementation
            code as new_function.  old_function is modified inplace !
        """

        # fix me: Does this handle closures correctly? Can we?
        #         readonly: func_closure, func_globals
        old_function.func_code = new_function.func_code
        old_function.func_defaults = new_function.func_defaults
        old_function.func_dict = new_function.func_dict
        old_function.func_doc = new_function.func_doc


#############################################################################
# Functions for finding class and function definitions within a module.
#############################################################################

def new_functions_and_classes_for_module(mod, logger=None):
    """ Return a list of the new class within a module

        Note that this reloads the module in the process.
    """
    # fix me: Is it really valuable to use this parsing technique
    #         instead of just searching the modules namespace for
    #         classes?  Perhaps so to prevent getting old classes...
    function_names, class_names = function_and_class_names_in_module(mod)

    # fixme: The try/except here was added because something strange
    #        is happening with Envisage *plugin_definition.py files.
    #        Python reports that they are not in sys.modules when you
    #        try to reload() them, but if you look in sys.modules, they
    #        are there.  I'm guessing that this has something to do
    #        with Martin's special import hook for loading modules, but
    #        I am not sure.  I'll talk with Martin and try to fix this
    #        correctly instead of handling it with this hack.

    if logger is None:
        logger = logging.root

    ignore_as_plugin = False
    ignore_as_instance = False

    try:
        import fnmatch, types
        if fnmatch.fnmatch(mod.__name__, "*plugin_definition*"):
            # fixme: This is soo ugly I feel good blaming it on Martin...
            # fixme: this really should be logged.
            #print "ignoring plugin definition: ", mod.__name__
            ignore_as_plugin = True

        elif (type(mod) is types.InstanceType):
            # this is added to get around scipy's delayed import.
            # fixme: this really should be logged.
            #print 'not reloading because it is instance type:', mod
            ignore_as_instance = True

        else:
            reload(mod)

    except ImportError:
        # ignore plugin_definition failures.  Report all others, but
        # continue.
        import fnmatch
        if not fnmatch.fnmatch(mod.__name__, "*plugin_definition*"):
            #print "unexpected reload error.  Module: %s", mod.__name__
            pass
        else:
            ignore_as_plugin = True

    # logging
    if not (ignore_as_plugin):
        logger.debug("Refresh ignoring plugin (ok): %s" % mod.__file__)
    if not (ignore_as_instance):
        logger.debug("Refresh ignoring Instance (ok): %s" % mod.__file__)

    if not (ignore_as_plugin or ignore_as_instance):
        function_list = [getattr(mod, name) for name in function_names]
        class_list = [getattr(mod, name) for name in class_names]
    else:
        function_list = []
        class_list = []

    return function_list, class_list


def function_and_class_names_in_module(mod):
    """ Parse .py file associated with module for class names (full path).

        The returned list contains class names without their module name
        prefix.  For example if the foo module contains a Bar class, this
        method would return ['Bar']

        Nested classes are not currently supported.
    """
    classes = []
    functions = []

    file_name = source_file_for_module(mod)
    if file_name:
        functions, classes = function_and_class_names_in_file(file_name)

    return functions, classes

def function_and_class_names_in_file(file_name):
    """ Find the names of classes contained within a file.

        fix me: This currently only finds top level classes.  Nested
        classes are ignored. ?? Does this really matter much ??

        Example::

            # foo.py
            class Foo:
                pass

            class Bar:
                pass

            >>> import traits.util.refresh
            >>> refresh.function_and_class_names_in_file('foo.py')
            [], ['Foo', 'Bar']
    """
    mod_ast = compiler.parseFile(file_name)

    class_names = []
    function_names = []
    for node in mod_ast.node.nodes:
        if node.__class__ is compiler.ast.Class:
            class_names.append(node.name)
        elif node.__class__ is compiler.ast.Function:
            function_names.append(node.name)

    return function_names, class_names

def source_file_for_module(module):
    """ Find the .py file that cooresponds to the module.
    """

    if hasattr(module,'__file__'):
        base,ext = os.path.splitext(module.__file__)
        file_name = base+'.py'
    else:
        file_name = None

    return file_name

#############################################################################
# Functions for filtering function and class objects out of a list.
#############################################################################

def filter_functions_and_classes(items):
    """ Filter items for all class and functions objects.

        Returns two lists: (functions, classes)

        This function is faster than calling filter_functions
        and filter_classes separately because it only traverses
        the entire list once to create a sub-list containing
        both functions and classes.  This (usually much shorter)
        sublist is then traversed again to divide it into functions
        and classes
    """

    # fix me: inspect.isclass checks for __bases__.  Do we need
    #         to do this for python classes, or is this only
    #         needed for classes declared in C?  Adding bases
    #         finds about 6000 classes compared to 2000 from
    #         the envisage interpeter.
    sub_items = [item for item in items if
                    isinstance(item, (FunctionType, ClassType, type))
                    #or hasattr(item,'__bases__')
                ]

    functions = filter_functions(sub_items)
    classes = filter_classes(sub_items)

    return functions, classes

def filter_functions(items):
    """ Filter items for all function objects (not instances mind you)
    """
    return [item for item in items if isinstance(item, FunctionType)]

def filter_classes(items):
    """ Filter items for all class objects (not instances mind you)
    """
    return [item for item in items if isinstance(item, (ClassType, type))]

#############################################################################
# Functions for searching for modules that have been updated on disk.
#############################################################################

def out_of_date_modules():
    """ Find loaded modules that have been modified since they were loaded.

        Searches the modules in sys.modules looks for py files that have
        a newer timestamp than the associated pyc file.  Extension modules
        are ignored.
    """
    out_of_date = []

    for mod_name, mod in sys.modules.items():
        if mod_name == "__main__":
            continue

        if hasattr(mod,'__file__'):
            base,ext = os.path.splitext(mod.__file__)
        else:
            # fixme: why would this happen...
            ext = None

        # pyd, dll, and so files are all ignored
        if ext in ['.pyc','.py']:
            py_time = _timestamp(base+'.py')
            pyc_time = _timestamp(base+'.pyc')

            if py_time is None:
                # strange case where someone has deleted the py file.
                pass
            else:
                if pyc_time is None:
                    # case where pyc file has been deleted.
                    out_of_date.append(mod)
                elif pyc_time <= py_time:
                    # module out of date
                    out_of_date.append(mod)

    return out_of_date

def _timestamp(pathname):
    """Return the file modification time as a Long.
    """
    try:
        s = os.stat(pathname)
    except OSError:
        return None
    return long(s.st_mtime)

