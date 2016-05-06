#!/usr/bin/env python
"""Search for tracebacks inside a folder of nipype crash
log files that match a given regular expression.

Examples:
nipype_crash_search -d nipype/wd/log -r '.*subject123.*'
"""
import re
import os.path as op
from glob import glob

from traits.trait_errors import TraitError
from nipype.utils.filemanip import loadcrash


def load_pklz_traceback(crash_filepath):
    """ Return the traceback message in the given crash file."""
    try:
        data = loadcrash(crash_filepath)
    except TraitError as te:
        return str(te)
    except:
        raise
    else:
        return '\n'.join(data['traceback'])


def iter_tracebacks(logdir):
    """ Return an iterator over each file path and
    traceback field inside `logdir`.
    Parameters
    ----------
    logdir: str
        Path to the log folder.

    field: str
        Field name to be read from the crash file.

    Yields
    ------
    path_file: str

    traceback: str
    """
    crash_files = sorted(glob(op.join(logdir, '*.pkl*')))

    for cf in crash_files:
        yield cf, load_pklz_traceback(cf)


def display_crash_search(logdir, regex):
    rex = re.compile(regex, re.IGNORECASE)
    for file, trace in iter_tracebacks(logdir):
        if rex.search(trace):
            print("-" * len(file))
            print(file)
            print("-" * len(file))
            print(trace)


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    defstr = ' (default %(default)s)'
    parser = ArgumentParser(prog='nipype_crash_search',
                            description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-l','--logdir', type=str, dest='logdir',
                        action="store", default=None,
                        help='The working directory log file.' + defstr)
    parser.add_argument('-r', '--regex', dest='regex',
                        default='*',
                        help='Regular expression to be searched in each traceback.' + defstr)

    args = parser.parse_args()

    display_crash_search(args.logdir, args.regex)
