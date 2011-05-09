#-----------------------------------------------------------------------------
#
#  Copyright (c) 2006 by Enthought, Inc.
#  All rights reserved.
#
#-----------------------------------------------------------------------------

""" Provides functions that munge strings to avoid characters that would be
    problematic in certain situations.
"""

# Standard library imports.
import copy
import datetime
import keyword
import re


def clean_filename(name):
    """ Munge a string to avoid characters that might be problematic as
        a filename in some filesystems.
    """
    # The only acceptable characters are alphanumeric (in the current locale)
    # plus a period and dash.
    wordparts = re.split('[^\w\.\-]+', name)

    # Filter out empty strings at the beginning or end of the list.
    wordparts = filter(None, wordparts)

    # Make sure this is an ASCII-encoded string, not a Unicode string.
    filename = '_'.join(wordparts).encode('ascii')

    return filename


def clean_timestamp(dt=None, microseconds=False):
    """ Return a timestamp that has been cleansed of characters that might
        cause problems in filenames, namely colons.  If no datetime object
        is provided, then uses the current time.

        Description
        -----------
        The timestamp is in ISO-8601 format with the following exceptions:

        * Colons ':' are replaced by underscores '_'.
        * Microseconds are not displayed if the 'microseconds' parameter is
          False.

        Parameters
        ----------
        dt : None or datetime.datetime object
            If None, then the current time is used.
        microseconds : bool
            Display microseconds or not.

        Returns
        -------
        A string timestamp.
    """
    if dt is None:
        dt = datetime.datetime.now()
    else:
        # Operate on a copy.
        dt = copy.copy(dt)

    if not microseconds:
        # The microseconds are largely uninformative but annoying.
        dt = dt.replace(microsecond=0)

    stamp = dt.isoformat().replace(':', '_')

    return stamp


def python_name(name):
    """ Attempt to make a valid Python identifier out of a name.
    """

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


### EOF ######################################################################

