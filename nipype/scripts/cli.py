#!python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import click


@click.group()
def cli():
    pass


@cli.command()
@click.argument('logdir', type=str)
@click.option('-r', '--regex', type=str, default='*',
              help='Regular expression to be searched in each traceback.')
def search(logdir, regex):
    """Search for tracebacks content.

    Search for traceback inside a folder of nipype crash log files that match
    a given regular expression.

    Examples:
    nipype search -d nipype/wd/log -r '.*subject123.*'
    """
    import re
    from .crash_files import iter_tracebacks

    rex = re.compile(regex, re.IGNORECASE)
    for file, trace in iter_tracebacks(logdir):
        if rex.search(trace):
            click.echo("-" * len(file))
            click.echo(file)
            click.echo("-" * len(file))
            click.echo(trace)


@cli.command()
@click.argument('crashfile', type=str)
@click.option('-r', '--rerun', is_flag=True, flag_value=True,
              help='Rerun crashed node.')
@click.option('-d', '--debug', is_flag=True, flag_value=True,
              help='Enable Python debugger when re-executing.')
@click.option('-i', '--ipydebug', is_flag=True, flag_value=True,
              help='Enable IPython debugger when re-executing.')
@click.option('--dir', type=str,
              help='Directory where to run the node in.')
def crash(crashfile, rerun, debug, ipydebug, directory):
    """Display Nipype crash files.

    For certain crash files, one can rerun a failed node in a temp directory.

    Examples:
    nipype crash crashfile.pklz
    nipype crash crashfile.pklz -r -i
    nipype crash crashfile.pklz -r -i
    """
    from .crash_files import display_crash_file

    debug = 'ipython' if ipydebug else debug
    if debug == 'ipython':
        import sys
        from IPython.core import ultratb
        sys.excepthook = ultratb.FormattedTB(mode='Verbose',
                                             color_scheme='Linux',
                                             call_pdb=1)
    display_crash_file(crashfile, rerun, debug, directory)


@cli.command()
@click.argument('pklz_file', type=str)
def show(pklz_file):
    """Print the content of Nipype node .pklz file.

    Examples:
    nipype show node.pklz
    """
    from pprint import pprint
    from ..utils.filemanip import loadpkl

    pkl_data = loadpkl(pklz_file)
    pprint(pkl_data)
