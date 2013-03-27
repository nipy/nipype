# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Utilities to pull in documentation from command-line tools.

Examples
--------

# Instantiate bet object
from nipype.interfaces import fsl
from nipype.utils import docparse
better = fsl.Bet()
docstring = docparse.get_doc(better.cmd, better.opt_map)

"""

import subprocess
from nipype.interfaces.base import CommandLine
from nipype.utils.misc import is_container

def grab_doc(cmd, trap_error=True):
    """Run cmd without args and grab documentation.

    Parameters
    ----------
    cmd : string
        Command line string
    trap_error : boolean
        Ensure that returncode is 0

    Returns
    -------
    doc : string
        The command line documentation
    """

    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
    stdout, stderr = proc.communicate()

    if trap_error and proc.returncode:
        msg = 'Attempting to run %s. Returned Error: %s'%(cmd,stderr)
        raise IOError(msg)

    if stderr:
        # A few programs, like fast and fnirt, send their help to
        # stderr instead of stdout.
        # XXX: Test for error vs. doc in stderr
        return stderr
    return stdout

def reverse_opt_map(opt_map):
    """Reverse the key/value pairs of the option map in the interface classes.

    Parameters
    ----------
    opt_map : dict
        Dictionary mapping the attribute name to a command line flag.
        Each interface class defines these for the command it wraps.

    Returns
    -------
    rev_opt_map : dict
       Dictionary mapping the flags to the attribute name.
    """

    # For docs, we only care about the mapping from our attribute
    # names to the command-line flags.  The 'v.split()[0]' below
    # strips off the string format characters.
    # if (k != 'flags' and v) , key must not be flags as it is generic,
    # v must not be None or it cannot be parsed by this line
    revdict = {}
    for key, value in opt_map.items():
        if is_container(value):
            # The value is a tuple where the first element is the
            # format string and the second element is a docstring.
            value = value[0]
        if (key != 'flags' and value is not None):
            revdict[value.split()[0]] = key
    return revdict


def format_params(paramlist, otherlist=None):
    """Format the parameters according to the nipy style conventions.

    Since the external programs do not conform to any conventions, the
    resulting docstrings are not ideal.  But at a minimum the
    Parameters section is reasonably close.

    Parameters
    ----------
    paramlist : list
        List of strings where each list item matches exactly one
        parameter and it's description.  These items will go into the
        'Parameters' section of the docstring.
    otherlist : list
        List of strings, similar to paramlist above.  These items will
        go into the 'Other Parameters' section of the docstring.

    Returns
    -------
    doc : string
        The formatted docstring.
    """

    hdr = 'Parameters'
    delim = '----------'
    paramlist.insert(0, delim)
    paramlist.insert(0, hdr)
    params = '\n'.join(paramlist)
    otherparams = []
    doc = ''.join(params)
    if otherlist:
        hdr = 'Others Parameters'
        delim = '-----------------'
        otherlist.insert(0, delim)
        otherlist.insert(0, hdr)
        otherlist.insert(0, '\n')
        otherparams = '\n'.join(otherlist)
        doc = ''.join([doc, otherparams])
    return doc

def insert_doc(doc, new_items):
    """Insert ``new_items`` into the beginning of the ``doc``

    Docstrings in ``new_items`` will be inserted right after the
    *Parameters* header but before the existing docs.

    Parameters
    ----------
    doc : str
        The existing docstring we're inserting docmentation into.
    new_items : list
        List of strings to be inserted in the ``doc``.

    Examples
    --------
    >>> from nipype.utils.docparse import insert_doc
    >>> doc = '''Parameters
    ... ----------
    ... outline :
    ...     something about an outline'''

    >>> new_items = ['infile : str', '    The name of the input file']
    >>> new_items.extend(['outfile : str', '    The name of the output file'])
    >>> newdoc = insert_doc(doc, new_items)
    >>> print newdoc
    Parameters
    ----------
    infile : str
        The name of the input file
    outfile : str
        The name of the output file
    outline :
        something about an outline

    """

    # Insert new_items after the Parameters header
    doclist = doc.split('\n')
    tmpdoc = doclist[:2]
    # Add new_items
    tmpdoc.extend(new_items)
    # Add rest of documents
    tmpdoc.extend(doclist[2:])
    # Insert newlines
    newdoc = []
    for line in tmpdoc:
        newdoc.append(line)
        newdoc.append('\n')
    # We add one too many newlines, remove it.
    newdoc.pop(-1)
    return ''.join(newdoc)


def build_doc(doc, opts):
    """Build docstring from doc and options

    Parameters
    ----------
    rep_doc : string
        Documentation string
    opts : dict
        Dictionary of option attributes and keys.  Use reverse_opt_map
        to reverse flags and attrs from opt_map class attribute.

    Returns
    -------
    newdoc : string
        The docstring with flags replaced with attribute names and
        formated to match nipy standards (as best we can).

    """

    # Split doc into line elements.  Generally, each line is an
    # individual flag/option.
    doclist = doc.split('\n')
    newdoc = []
    flags_doc = []
    for line in doclist:
        linelist = line.split()
        if not linelist:
            # Probably an empty line
            continue
        # For lines we care about, the first item is the flag
        if ',' in linelist[0]: #sometimes flags are only seperated by comma
            flag = linelist[0].split(',')[0]
        else:
            flag = linelist[0]
        attr = opts.get(flag)
        if attr is not None:
            #newline = line.replace(flag, attr)
            # Replace the flag with our attribute name
            linelist[0] = '%s :' % str(attr)
            # Add some line formatting
            linelist.insert(1, '\n    ')
            newline = ' '.join(linelist)
            newdoc.append(newline)
        else:
            if line[0].isspace():
                # For all the docs I've looked at, the flags all have
                # indentation (spaces) at the start of the line.
                # Other parts of the docs, like 'usage' statements
                # start with alpha-numeric characters.  We only care
                # about the flags.
                flags_doc.append(line)
    return format_params(newdoc, flags_doc)

def get_doc(cmd, opt_map, help_flag=None, trap_error=True):
    """Get the docstring from our command and options map.

    Parameters
    ----------
    cmd : string
        The command whose documentation we are fetching
    opt_map : dict
        Dictionary of flags and option attributes.
    help_flag : string
        Provide additional help flag. e.g., -h
    trap_error : boolean
        Override if underlying command returns a non-zero returncode

    Returns
    -------
    doc : string
        The formated docstring

    """
    res = CommandLine('which %s' % cmd.split(' ')[0],
                      terminal_output='allatonce').run()
    cmd_path = res.runtime.stdout.strip()
    if cmd_path == '':
        raise Exception('Command %s not found'%cmd.split(' ')[0])
    if help_flag:
        cmd = ' '.join((cmd,help_flag))
    doc = grab_doc(cmd,trap_error)
    opts = reverse_opt_map(opt_map)
    return build_doc(doc, opts)

def _parse_doc(doc, style=['--']):
    """Parses a help doc for inputs

    Parameters
    ----------
    doc : string
        Documentation string
    style : string default ['--']
        The help command style (--, -)

    Returns
    -------
    optmap : dict of input parameters
    """

    # Split doc into line elements.  Generally, each line is an
    # individual flag/option.
    doclist = doc.split('\n')
    optmap = {}
    if isinstance(style,str):
        style = [style]
    for line in doclist:
        linelist = line.split()
        flag =[item for i,item in enumerate(linelist) if i<2 and \
                   any([item.startswith(s) for s in style]) and \
                   len(item)>1]
        if flag:
            if len(flag)==1:
                style_idx = [flag[0].startswith(s) for s in style].index(True)
                flag = flag[0]
            else:
                style_idx = []
                for f in flag:
                    for i,s in enumerate(style):
                        if f.startswith(s):
                            style_idx.append(i)
                            break
                flag = flag[style_idx.index(min(style_idx))]
                style_idx = min(style_idx)
            optmap[flag.split(style[style_idx])[1]] = '%s %%s'%flag
    return optmap

def get_params_from_doc(cmd, style='--', help_flag=None, trap_error=True):
    """Auto-generate option map from command line help

    Parameters
    ----------
    cmd : string
        The command whose documentation we are fetching
    style : string default ['--']
        The help command style (--, -). Multiple styles can be provided in a
        list e.g. ['--','-'].
    help_flag : string
        Provide additional help flag. e.g., -h
    trap_error : boolean
        Override if underlying command returns a non-zero returncode

    Returns
    -------
    optmap : dict
        Contains a mapping from input to command line variables

    """
    res = CommandLine('which %s' % cmd.split(' ')[0],
                      terminal_output='allatonce').run()
    cmd_path = res.runtime.stdout.strip()
    if cmd_path == '':
        raise Exception('Command %s not found'%cmd.split(' ')[0])
    if help_flag:
        cmd = ' '.join((cmd,help_flag))
    doc = grab_doc(cmd,trap_error)
    return _parse_doc(doc,style)

def replace_opts(rep_doc, opts):
    """Replace flags with parameter names.

    This is a simple operation where we replace the command line flags
    with the attribute names.

    Parameters
    ----------
    rep_doc : string
        Documentation string
    opts : dict
        Dictionary of option attributes and keys.  Use reverse_opt_map
        to reverse flags and attrs from opt_map class attribute.

    Returns
    -------
    rep_doc : string
        New docstring with flags replaces with attribute names.

    Examples
    --------
    doc = grab_doc('bet')
    opts = reverse_opt_map(fsl.Bet.opt_map)
    rep_doc = replace_opts(doc, opts)

    """

    # Replace flags with attribute names
    for key, val in opts.items():
        rep_doc = rep_doc.replace(key, val)
    return rep_doc
