#!/usr/bin/env python

import argparse
from glob import glob
import os
from os.path import isfile, isdir
import sys

from traits.util.updates.info_file import InfoFile

def build_argparser():
    parser = argparse.ArgumentParser(
            description = "Converts .info files into XML files compatible with " \
                          "the enthought.updates library.  Supports batch " \
                          "operations on directories.")
    parser.add_argument("filespecs", type=str, nargs="+",
            help="Filenames and/or directories to be searched for info files")

    parser.add_argument("-a", "--append", type=argparse.FileType("r"),
             nargs = 1,
            help = "name of output file; if it exists, append to it")

    parser.add_argument("-o", "--output", type=argparse.FileType("w"),
            nargs = 1,
            help = "name of output file; if it exists, it is overwritten")

    parser.add_argument("-r", "--recurse", action="store_true", default=False,
            help = "search all subdirectories of provided dirs for .info files")

    parser.add_argument("-l", "--location", type=str, default="",
            help = "URI to use as the 'location' XML tag of each .info file")

    return parser

def main():
    parser = build_argparser()
    opts = parser.parse_args(sys.argv[1:])

    # Process all the files
    xml_strs = []
    filespecs = opts.filespecs[:]
    for filespec in filespecs:
        # A concrete .info file:
        if isfile(filespec):
            f = InfoFile.from_info_file(filespec)
            f.location = opts.location
            xml_strs.append(f.to_xml_str())
        elif isdir(filespec):
            filespecs.extend(glob(os.path.join(filespec, "*.info")))
            if opts.recurse:
                # Also add all the subdirectories
                filespecs.extend(d for d in os.listdir(filespec) if isdir(d))

    # Output appropriately
    if getattr(opts, "append", None):
        raise NotImplementedError

    if opts.output is None:
        opts.output = "updates.xml"

    outfile = file(opts.output, "w")
    outfile.write("\n".join(xml_strs) + "\n")
    outfile.close()


if __name__ == "__main__":
    main()
