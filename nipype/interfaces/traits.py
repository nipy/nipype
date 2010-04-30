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

import enthought.traits.api as traits
import os

class BaseFile ( traits.BaseStr ):
    """ Defines a trait whose value must be the name of a file.
    """
	
    # A description of the type of value this trait accepts:
    info_text = 'a file name'
	
    def __init__ ( self, value = '', filter = None, auto_set = False,
                   entries = 0, exists = False, **metadata ):
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
	
        super( BaseFile, self ).__init__( value, **metadata )
	
    def validate ( self, object, name, value ):
        """ Validates that a specified value is valid for this trait.
        
        Note: The 'fast validator' version performs this check in C.
        """
        if not self.exists:
            return super( BaseFile, self ).validate( object, name, value )
        
        if os.path.isfile( value ):
            return value
        
        self.error( object, name, value )
 

    
class File ( BaseFile ):
    """ Defines a trait whose value must be the name of a file using a C-level
    fast validator.
    """
    
    def __init__ ( self, value = '', filter = None, auto_set = False,
                   entries = 0, exists = False, **metadata ):
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
            fast_validate = ( 11, basestring )
	
        super( File, self ).__init__( value, filter, auto_set, entries, exists,
                                      **metadata )
	

class BaseDirectory ( traits.BaseStr ):
    """ Defines a trait whose value must be the name of a directory.
    """
    
    # A description of the type of value this trait accepts:
    info_text = 'a directory name'
    
    def __init__ ( self, value = '', auto_set = False, entries = 0,
                   exists = False, **metadata ):
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

        super( BaseDirectory, self ).__init__( value, **metadata )

    def validate ( self, object, name, value ):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        if not self.exists:
            return super( BaseDirectory, self ).validate( object, name, value )

        if os.path.isdir( value ):
            return value

        self.error( object, name, value )

    def create_editor(self):
        from .ui.editors.directory_editor import DirectoryEditor
        editor = DirectoryEditor(
            auto_set = self.auto_set,
            entries = self.entries,
        )
        return editor


class Directory ( BaseDirectory ):
    """ Defines a trait whose value must be the name of a directory using a
        C-level fast validator.
    """

    def __init__ ( self, value = '', auto_set = False, entries = 0,
                         exists = False, **metadata ):
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
            self.fast_validate = ( 11, basestring )

        super( Directory, self ).__init__( value, auto_set, entries, exists,
                                           **metadata )

#-------------------------------------------------------------------------------
#  Singleton 'Undefined' object (used as undefined trait name and/or value):
#-------------------------------------------------------------------------------

class _Undefined ( object ):

    def __repr__ ( self ):
        return '<undefined>'

    def __eq__( self, other ):
        return type(self) is type(other)

    def __ne__( self, other ):
        return type(self) is not type(other)

    def __len__(self):
        return 0

# Singleton object that indicates that a trait attribute has not yet had a
# value set (i.e., its value is undefined). This object is used instead of
# None, because None often has other meanings, such as that a value is not 
# used. When a trait attribute is first assigned a value, and its associated
# trait notification handlers are called, Undefined is passed as the *old* 
# parameter, to indicate that the attribute previously had no value.
Undefined = _Undefined()
