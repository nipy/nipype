#-----------------------------------------------------------------------------
#
#  Copyright (c) 2006 by Enthought, Inc.
#  All rights reserved.
#
#  Author: Dave Peterson <dpeterson@enthought.com>
#
#-----------------------------------------------------------------------------

""" Provides the capability to format a string to a valid python name.

    DEPRECATED: Please use the traits.util.clean_strings module instead.
"""

# Standard library imports.
import keyword
import warnings


def python_name(name):
    """ Attempt to make a valid Python identifier out of a name.

        DEPRECATED: Please use the traits.util.clean_strings.python_name
        function instead.
    """
    warnings.warn('traits.util.python_name has been ' + \
        'deprecated in favor of traits.util.clean_strings',
        DeprecationWarning)

    if len(name) > 0:
        # Replace spaces with underscores.
        name = name.replace(' ', '_').lower()

        # If the name is a Python keyword then prefix it with an
        # underscore.
        if keyword.iskeyword(name):
            name = '_' + name

        # If the name starts with a digit then prefix it with an
        # underscore.
        if name[0].isdigit():
            name = '_' + name

    return name


#### EOF #####################################################################

