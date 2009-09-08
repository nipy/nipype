"""Module testing code to pull in documentation from command-line tools."""

import sys
import subprocess

from nipype.interfaces import fsl

def grab_doc(cmd):
    # We need to redirect stderr to stdout for this.  Some of the
    # docs, like Fast, print the help to stderr instead of stdout.
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
    stdout, stderr = proc.communicate()
    if stderr:
        # A few programs, like fast and fnirt, send their help to
        # stderr instead of stdout.
        return stderr
    return stdout

def fsl_opts():
    for item in dir(fsl):
        intrfc = getattr(fsl, item)
        if hasattr(intrfc, 'opt_map'):
            print 'Object %s has opt_map:' % str(intrfc)
            #print '  ', getattr(intrfc, 'opt_map')

def reverse_opt_map(opt_map):
    # For docs, we only care about the mapping from our attribute
    # names to the command-line flags.  The 'v.split()[0]' below
    # strips off the string format characters.
    return dict((v.split()[0], k) for k, v in opt_map.iteritems()
                if k != 'flags')

def print_parameters(linelist):
    # print list of documentation lines
    print 'Parameters\n----------\n',
    for i in linelist:
        print i

def print_other_parameters(linelist):
    # print list of documentation lines
    print 'Others Parameters\n-----------------\n',
    for i in linelist:
        print i

def format_params(paramlist, otherlist=None):
    #paramlist = copy(paramlist)
    #otherlist = copy(otherlist)
    hdr = 'Parameters'
    delim = '----------'
    paramlist.insert(0, delim)
    paramlist.insert(0, hdr)
    params = '\n'.join(paramlist)
    otherparams = []
    if otherlist:
        hdr = 'Others Parameters'
        delim = '-----------------'
        otherlist.insert(0, delim)
        otherlist.insert(0, hdr)
        otherlist.insert(0, '\n')
        otherparams = '\n'.join(otherlist)
    return ''.join([params, otherparams])

def replace_opts(rep_doc, opts):
    """Replace flags with parameter names.
    
    Parameters
    ----------
    rep_doc : string
        Documentation string
    opts : dict
        Dictionary of option attributes and keys
    """

    # Replace flags with attribute names
    for key, val in opts.iteritems():
        rep_doc = rep_doc.replace(key, val)

def build_doc(doc, opts):
    """Build docstring from doc and options

    Parameters
    ----------
    rep_doc : string
        Documentation string
    opts : dict
        Dictionary of option attributes and keys.  Use reverse_opt_map
        to reverse flags and attrs from opt_map class attribute.

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
    res = format_params(newdoc, flags_doc)
    return res

def fsl_docs():
    """Process all the fsl docs we have so far"""
    cmdlist = [('bet', 'fsl.Bet'), 
               ('fast', 'fsl.Fast'),
               ('flirt', 'fsl.Flirt'),
               ('mcflirt', 'fsl.McFlirt'),
               ('fnirt', 'fsl.Fnirt')]

    fsl_doc_list = []
    for cmd in cmdlist:
        doc = grab_doc(cmd[0])
        opt_map = cmd[1] + '.opt_map'
        opts = reverse_opt_map(eval(opt_map))
        res = build_doc(doc, opts)
        fsl_doc_list.append((cmd[0], res))
    return fsl_doc_list

def betdoc():
    """Generate docs for bet."""
    cmd = 'bet'
    doc = grab_doc(cmd)
    opts = reverse_opt_map(fsl.Bet.opt_map)
    res = build_doc(doc, opts)
    return res

if __name__ == '__main__':
    #rep_doc = replace_opts(doc, opts)
    bet_docs = betdoc()
    
