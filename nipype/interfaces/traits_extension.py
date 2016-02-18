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
    """
    def __init__(self, template=None, keep_extension=True, value='',
                 filter=None, auto_set=False, entries=0, exists=False, **metadata):
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

        if template is None or not isinstance(template, string_types):
            raise TraitError('GenFile requires a valid template argument')

        self.name_source = [i[1:-1].split('!')[0].split(':')[0].split('[')[0]
                            for i in re.findall('\{.*?\}', template)]
        self.template = template.format
        self.keep_ext = keep_extension

        for nsrc in self.name_source:
            if not isinstance(nsrc, string_types):
                raise TraitError('template contains an invalid name_source '
                                 'entry (found %s).' % nsrc)
            if '%' in nsrc or len(nsrc) == 0:
                raise TraitError(
                    'invalid source field found in template \'%s\'' % nsrc)

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
        if self.value is None:
            srcvals = {}
            ext = ''
            for nsrc in self.name_source:
                IFLOGGER.debug('nsrc=%s', nsrc)
                val = getattr(obj, nsrc)
                try:
                    _, val, ext = split_filename(val)
                except:
                    pass

                if isdefined(val):
                    srcvals.update({nsrc: val})

            # Check that no source is missing
            missing = list(set(self.name_source) - set(srcvals.keys()))
            if not missing:
                retval = self.template(**srcvals)
                if self.keep_ext:
                    retval += ext
                return retval
            else:
                return Undefined
        return self.value

    def set(self, obj, name, value):
        if isdefined(value):
            self.value = value
        else:
            self.value = None


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
