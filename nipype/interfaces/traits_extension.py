# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module contains Trait classes that we've pulled from the
traits source and fixed due to various bugs.  File and Directory are
redefined as the release version had dependencies on TraitsUI, which
we do not want Nipype to depend on.  At least not yet.

Undefined class was missing the __len__ operator, causing edit_traits
and configure_traits to fail on List objects.  Even though we don't
require TraitsUI, this bug was the only thing preventing us from
popping up GUIs which users like.

These bugs have been in Traits v3.3.0 and v3.2.1.  We have reported
all of these bugs and they've been fixed in enthought svn repository
(usually by Robert Kern).

"""
import os
import re
import itertools as itools

from ast import literal_eval
from ..external.six import string_types
# perform all external trait imports here
import traits
if traits.__version__ < '3.7.0':
    raise ImportError('Traits version 3.7.0 or higher must be installed')
import traits.api as traits
from traits.trait_handlers import TraitDictObject, TraitListObject
from traits.trait_errors import TraitError
from traits.trait_base import _Undefined

from ..utils.filemanip import split_filename

from .. import logging
IFLOGGER = logging.getLogger('interface')

class BaseFile (traits.BaseStr):
    """ Defines a trait whose value must be the name of a file.
    """

    # A description of the type of value this trait accepts:
    info_text = 'a file name'

    def __init__(self, value='', filter=None, auto_set=False,
                 entries=0, exists=False, **metadata):
        """ Creates a File trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        filter : string
            A wildcard string to filter filenames in the file dialog box used by
            the attribute trait editor.
        auto_set : boolean
            Indicates whether the file editor updates the trait value after
            every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing file or
            not.

        Default Value
        -------------
        *value* or ''
        """
        self.filter = filter
        self.auto_set = auto_set
        self.entries = entries
        self.exists = exists

        if exists:
            self.info_text = 'an existing file name'

        super(BaseFile, self).__init__(value, **metadata)

    def validate(self, object, name, value):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        validated_value = super(BaseFile, self).validate(object, name, value)
        if not self.exists:
            return validated_value
        elif os.path.isfile(value):
            return validated_value

        self.error(object, name, value)


class File (BaseFile):
    """ Defines a trait whose value must be the name of a file using a C-level
        fast validator.
    """

    def __init__(self, value='', filter=None, auto_set=False,
                 entries=0, exists=False, **metadata):
        """ Creates a File trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        filter : string
            A wildcard string to filter filenames in the file dialog box used by
            the attribute trait editor.
        auto_set : boolean
            Indicates whether the file editor updates the trait value after
            every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing file or
            not.

        Default Value
        -------------
        *value* or ''
        """
        if not exists:
            # Define the C-level fast validator to use:
            fast_validate = (11, str)

        super(File, self).__init__(value, filter, auto_set, entries, exists,
                                   **metadata)


class GenFile(File):
    """ A file which default name is automatically generated from other
    traits.

    >>> # The traits start undefined
    >>> from nipype.interfaces.base import GenFile, Undefined
    >>> class A(TraitedSpec):
    ...     src = File(exists=False)
    ...     foo = GenFile(template='{src}_foo')
    >>> a = A()
    >>> a.src
    <undefined>
    >>> a.foo
    <undefined>

    >>> # If the source trait is set, foo can be sourced ...
    >>> a.src = '/software/temp/src.txt'
    >>> a.foo
    'src_foo.txt'

    >>> # ... and updates with the update of src ...
    >>> a.src = '/software/temp/foo.txt'
    >>> a.foo
    'foo_foo.txt'

    >>> # ... util it is explicitly set.
    >>> a.foo = '/software/temp/goo.txt'
    >>> a.foo
    '/software/temp/goo.txt'

    >>> # Setting it Undefined will restore the sourcing behavior
    >>> a.foo = Undefined
    >>> a.foo
    'foo_foo.txt'

    """

    def __init__(self, template=None, keep_extension=False, value='',
                 filter=None, auto_set=False, entries=0, exists=False, **metadata):
        """ Creates a GenFile trait. """

        if template is None or not isinstance(template, string_types):
            raise TraitError('GenFile requires a valid template argument')

        self.name_source = list(_parse_name_source(template))
        # Remove range indexing tokens (not allowed by string.Formatter)
        for _, itoken, _ in self.name_source:
            if itoken:
                template = template.replace(itoken, '')

        self.template = template
        self.keep_ext = keep_extension
        super(GenFile, self).__init__(value, filter, auto_set, entries, exists,
                                      **metadata)


    def validate(self, object, name, value):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        # Allow unsetting the input
        if not isdefined(value):
            return value

        validated_value = super(GenFile, self).validate(object, name, value)
        if not self.exists:
            return validated_value
        elif os.path.isfile(value):
            return validated_value

        self.error(object, name, value)

    def get(self, obj, name):
        # Compute expected name iff trait is not set
        template = self.template
        if self.value is None:
            srcvals = {}
            ext = ''
            final_nsrcs = []
            for nsrc_list, indexing, fstr in self.name_source:
                for nel in nsrc_list:
                    srcvalue = getattr(obj, nel)
                    if isdefined(srcvalue):
                        nsrc = nel
                        break

                if not isdefined(srcvalue):
                    return Undefined

                template = template.replace('|'.join(nsrc_list), nsrc)
                IFLOGGER.debug('replacing %s with %s. Result=%s', '|'.join(nsrc_list), nsrc, template)
                final_nsrcs.append(nsrc)

                if isinstance(srcvalue, string_types):
                    vallist = [srcvalue]
                else:
                    vallist = list(srcvalue)

                outvals = []

                isfile = obj.trait(nsrc).is_trait_type((
                    File, MultiPath, GenMultiFile))
                for val in vallist:
                    if isfile:
                        _, val, ext = split_filename(val)
                    elif indexing:
                        # eval should be safe since we only
                        # accept indexing elements with format [n:n]
                        val = eval('val%s' % indexing) # pylint: disable=W0123
                    if isdefined(val):
                        outvals.append(val)

                if not outvals:
                    continue

                if isinstance(srcvalue, string_types):
                    srcvals.update({nsrc: outvals[0]})
                elif isinstance(srcvalue, tuple):
                    srcvals.update({nsrc: tuple(outvals)})
                else:
                    srcvals.update({nsrc: outvals})

            # Check that no source is missing
            IFLOGGER.debug('Final sources: %s and values %s', final_nsrcs, srcvals)
            missing = list(set(final_nsrcs) - set(srcvals.keys()))
            if not missing:
                retval = template.format(**srcvals)
                if self.keep_ext:
                    retval += ext
                return retval
            else:
                return Undefined
        return self.get_value(obj, name)

    def set(self, obj, name, value):
        self.set_value(obj, name, value)


class MultiPath(traits.List):
    """ Abstract class - shared functionality of input and output MultiPath
    """

    def validate(self, obj, name, value):
        if not isdefined(value) or \
                (isinstance(value, list) and len(value) == 0):
            return Undefined
        newvalue = value

        if not isinstance(value, list) \
            or (self.inner_traits() and
                isinstance(self.inner_traits()[0].trait_type,
                           traits.List) and not
                isinstance(self.inner_traits()[0].trait_type,
                           InputMultiPath) and
                isinstance(value, list) and
                value and not
                isinstance(value[0], list)):
            newvalue = [value]
        value = super(MultiPath, self).validate(obj, name, newvalue)

        if len(value) > 0:
            return value

        self.error(obj, name, value)


class GenMultiFile(traits.List):
    """ Traits to generate lists of files.

    >>> # The traits start undefined
    >>> from nipype.interfaces.base import GenFile, Undefined, traits
    >>> class A(TraitedSpec):
    ...     src = InputMultiPath(File(exists=False))
    ...     foo = GenMultiFile(template='{src}_foo')
    >>> a = A()
    >>> a.src
    <undefined>
    >>> a.foo
    <undefined>

    >>> # If the source trait is set, foo can be sourced ...
    >>> a.src = ['/software/temp/src1.txt', '/software/temp/src2.txt']
    >>> a.foo
    ['src1_foo.txt', 'src2_foo.txt']

    >>> # ... and updates with the update of src ...
    >>> a.src = ['/software/temp/foo1.txt', '/software/temp/foo2.txt']
    >>> a.foo
    ['foo1_foo.txt', 'foo2_foo.txt']

    >>> # ... util it is explicitly set.
    >>> a.foo = ['/software/temp/goo1.txt', '/software/temp/goo2.txt']
    >>> a.foo
    ['/software/temp/goo1.txt', '/software/temp/goo2.txt']

    >>> # Setting it Undefined will restore the sourcing behavior
    >>> a.foo = Undefined
    >>> a.foo
    ['foo1_foo.txt', 'foo2_foo.txt']

    >>> # It works with several replacements and defining ranges
    >>> class B(TraitedSpec):
    ...     src = File(exists=False)
    ...     num = traits.Int()
    ...     foo = GenMultiFile(template='{src}_foo_{num:03d}', range_source='num')
    >>> a.src = '/software/temp/source.txt'
    >>> a.num = 3
    >>> a.foo
    ['source_foo_000.txt', 'source_foo_001.txt', 'source_foo_002.txt']

    >>> # And altogether with InputMultiPaths
    >>> class B(TraitedSpec):
    ...     src = InputMultiPath(File(exists=False))
    ...     num = traits.Int()
    ...     foo = GenMultiFile(template='{src}_foo_{num:03d}', range_source='num')
    >>> a.src = ['/software/temp/source.txt', '/software/temp/alt.txt']
    >>> a.num = 2
    >>> a.foo
    ['source_foo_000.txt', 'alt_foo_000.txt', 'source_foo_001.txt', 'alt_foo_001.txt']


    """
    def __init__(self, template=None, keep_extension=False, range_source=None, **metadata):
        if template is None or not isinstance(template, string_types):
            raise TraitError('GenMultiFile requires a valid template argument')

        self.name_source = list(_parse_name_source(template))
        # Remove range indexing tokens (not allowed by string.Formatter)
        for _, itoken, _ in self.name_source:
            if itoken:
                template = template.replace(itoken, '')
        self.template = template
        self.keep_ext = keep_extension
        self.range_source = None
        if range_source is not None:
            if not isinstance(range_source, string_types):
                raise TraitError(
                    'range_source is not valid (found %s).' % range_source)

            try:
                range_source, offset = range_source.split('+')
                self.offset = int(offset)
            except ValueError:
                self.offset = 0

            if range_source not in [n for nsrc in self.name_source for n in nsrc[0]]:
                raise TraitError(
                    'range_source field should also be found in the'
                    ' template (valid fields = %s).' % self.name_source)
            self.range_source = range_source

        super(GenMultiFile, self).__init__(**metadata)

    def validate(self, obj, name, value):
        if not isdefined(value) or \
                (isinstance(value, list) and len(value) == 0):
            return Undefined
        newvalue = value

        if not isinstance(value, list) \
            or (self.inner_traits() and
                isinstance(self.inner_traits()[0].trait_type,
                           traits.List) and not
                isinstance(self.inner_traits()[0].trait_type,
                           InputMultiPath) and
                isinstance(value, list) and
                value and not
                isinstance(value[0], list)):
            newvalue = [value]
        value = super(GenMultiFile, self).validate(obj, name, newvalue)

        if len(value) > 0:
            return value

        self.error(obj, name, value)

    def get(self, obj, name):
        # Compute expected name iff trait is not set
        value = self.get_value(obj, name)
        template = self.template
        if not isdefined(value) or not value:
            srcvals = {}
            ext = ''

            final_nsrcs = []
            for nsrc_list, indexing, fstr in self.name_source:
                for nel in nsrc_list:
                    srcvalue = getattr(obj, nel)
                    if isdefined(srcvalue):
                        nsrc = nel
                        break

                if not isdefined(srcvalue):
                    return Undefined

                template = template.replace('|'.join(nsrc_list), nsrc)
                IFLOGGER.debug('replacing %s with %s. Result=%s', '|'.join(nsrc_list), nsrc, template)
                final_nsrcs.append(nsrc)

                IFLOGGER.debug('Autogenerating output for: %s (%s=%s)', name, nsrc, srcvalue)
                IFLOGGER.debug('range_source=%s', self.range_source)
                if self.range_source is not None and nsrc == self.range_source:
                    srcvalue = range(self.offset, int(srcvalue) + self.offset)
                    vallist = srcvalue
                    IFLOGGER.debug('Generating range of outputs: %s', vallist)

                if isinstance(srcvalue, string_types):
                    vallist = [srcvalue]
                else:
                    vallist = list(srcvalue)

                outvals = []

                isfile = obj.trait(nsrc).is_trait_type((
                    File, MultiPath, GenMultiFile))
                for val in vallist:
                    if isfile:
                        _, val, ext = split_filename(val)

                    if isdefined(val):
                        outvals.append(val)

                if outvals:
                    srcvals.update({nsrc: outvals})

            IFLOGGER.debug('Final sources: %s and values %s', final_nsrcs, srcvals)
            # Check that no source is missing
            missing = list(set(final_nsrcs) - set(srcvals.keys()))
            if not missing:
                results = []
                combs = list(itools.product(*tuple(srcvals[k] for k in final_nsrcs)))

                # Get the formatting dictionaries ready
                dlist = [{final_nsrcs[i]: v for i, v in enumerate(kvalues)}
                          for kvalues in combs]
                # ... and create a formatted entry for each of them
                for fmtdict in dlist:
                    retval = template.format(**fmtdict)
                    if self.keep_ext:
                        retval += ext
                    results.append(retval)

                if results:
                    if len(results) == 1:
                        return results[0]
                    return results

            return Undefined

        if len(value) == 0:
            return Undefined
        elif len(value) == 1:
            return value[0]
        else:
            return value

    def set(self, obj, name, value):
        self.set_value(obj, name, value)


class OutputMultiPath(MultiPath):
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the output version which
    return a single string whenever possible (when it was set to a
    single value or a list of length 1). Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import OutputMultiPath
    >>> class A(TraitedSpec):
    ...     foo = OutputMultiPath(File(exists=False))
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """

    def get(self, obj, name):
        value = self.get_value(obj, name)
        if len(value) == 0:
            return Undefined
        elif len(value) == 1:
            return value[0]
        else:
            return value

    def set(self, obj, name, value):
        self.set_value(obj, name, value)


class InputMultiPath(MultiPath):
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the input version which
    always returns a list. Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import InputMultiPath
    >>> class A(TraitedSpec):
    ...     foo = InputMultiPath(File(exists=False))
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """
    pass


# -------------------------------------------------------------------------------
#  'BaseDirectory' and 'Directory' traits:
# -------------------------------------------------------------------------------


class BaseDirectory (traits.BaseStr):
    """ Defines a trait whose value must be the name of a directory.
    """

    # A description of the type of value this trait accepts:
    info_text = 'a directory name'

    def __init__(self, value='', auto_set=False, entries=0,
                 exists=False, **metadata):
        """ Creates a BaseDirectory trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        auto_set : boolean
            Indicates whether the directory editor updates the trait value
            after every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing directory or
            not.

        Default Value
        -------------
        *value* or ''
        """
        self.entries = entries
        self.auto_set = auto_set
        self.exists = exists

        if exists:
            self.info_text = 'an existing directory name'

        super(BaseDirectory, self).__init__(value, **metadata)

    def validate(self, object, name, value):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        validated_value = super(BaseDirectory, self).validate(object, name, value)
        if not self.exists:
            return validated_value

        if os.path.isdir(value):
            return validated_value

        self.error(object, name, value)


class Directory (BaseDirectory):
    """ Defines a trait whose value must be the name of a directory using a
        C-level fast validator.
    """

    def __init__(self, value='', auto_set=False, entries=0,
                 exists=False, **metadata):
        """ Creates a Directory trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        auto_set : boolean
            Indicates whether the directory editor updates the trait value
            after every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing directory or
            not.

        Default Value
        -------------
        *value* or ''
        """
        # Define the C-level fast validator to use if the directory existence
        # test is not required:
        if not exists:
            self.fast_validate = (11, str)

        super(Directory, self).__init__(value, auto_set, entries, exists,
                                        **metadata)


"""
The functions that pop-up the Traits GUIs, edit_traits and
configure_traits, were failing because all of our inputs default to
Undefined deep and down in traits/ui/wx/list_editor.py it checks for
the len() of the elements of the list.  The _Undefined class in traits
does not define the __len__ method and would error.  I tried defining
our own Undefined and even sublassing Undefined, but both of those
failed with a TraitError in our initializer when we assign the
Undefined to the inputs because of an incompatible type:

TraitError: The 'vertical_gradient' trait of a BetInputSpec instance must be a float, but a value of <undefined> <class 'nipype.interfaces.traits._Undefined'> was specified.

So... in order to keep the same type but add the missing method, I
monkey patched.
"""


def length(self):
    return 0

##########################################################################
# Apply monkeypatch here
_Undefined.__len__ = length
##########################################################################

Undefined = _Undefined()


def isdefined(object):
    return not isinstance(object, _Undefined)


def has_metadata(trait, metadata, value=None, recursive=True):
    """
    Checks if a given trait has a metadata (and optionally if it is set to particular value)
    """
    count = 0
    if hasattr(trait, "_metadata") and metadata in list(trait._metadata.keys()) and (trait._metadata[metadata] == value or value is None):
        count += 1
    if recursive:
        if hasattr(trait, 'inner_traits'):
            for inner_trait in trait.inner_traits():
                count += has_metadata(inner_trait.trait_type, metadata, recursive)
        if hasattr(trait, 'handlers') and trait.handlers is not None:
            for handler in trait.handlers:
                count += has_metadata(handler, metadata, recursive)

    return count > 0

def _parse_name_source(name_source):
    """Parse template strings"""
    format_str = [i[1:-1] for i in re.findall(r'\{.*?\}', name_source)]

    for fchunk in format_str:
        indexing = [i for i in re.findall(r'\[[0-9]*:[0-9]*\]', fchunk)]
        # Only one complex indexing replacement is allowed
        if indexing:
            indexing = indexing[0]

        name = fchunk.split('.')[0].split('!')[0].split(':')[0].split('[')[0]
        yield (name.split('|'), indexing, fchunk)


