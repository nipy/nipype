""" Given a list of files or a subdirectory, creates stub .info files alongside
them.
"""

import argparse
from glob import glob
import os
from os.path import isfile
import sys

from traits.util.updates.info_file import InfoFile

def build_argparser():
    parser = argparse.ArgumentParser(
            description = "Given a list of files or subdirectories, creates " \
                          "stub .info files alongside all existing files.")

    parser.add_argument("filespecs", type=str, nargs="+",
            help="Files to generate .info files for. Wildcards such as "\
                 "'*.zip' and directories with globs like 'foo/*.tgz' are "\
                 "supported")

    parser.add_argument("-a", "--all", action="store_true", default=False,
            help="Overwrite existing .info files. (By default, files with "\
                 "existing .info files are skipped.)")

    parser.add_argument("-i", "--include_info", action="store_true", default=False,
            help="Don't skip files that already end in .info. (By default, "\
                 "for ease of globbing, all files that end in .info are "\
                 "skipped.)")

    parser.add_argument("-q", "--quiet", action="store_true", default=False,
            help="Suppresses output of names of processed files")

    return parser

def main():
    parser = build_argparser()
    opts = parser.parse_args(sys.argv[1:])

    filespecs = opts.filespecs[:]
    for filespec in filespecs:
        infofile_name = filespec + ".info"

        # Regular file
        if isfile(filespec):

            # Handle .info files
            if filespec.endswith(".info") and not opts.include_info:
                continue

            if not opts.quiet:
                if isfile(infofile_name):
                    if not opts.all:
                        print "[Skip]\t\t",
                    else:
                        print "[Replaced]\t",
                else:
                    print "\t\t",
                print infofile_name

            if not isfile(infofile_name) or opts.all:
                # Create a new .info file
                try:
                    info = InfoFile.from_target_file(filespec)
                    f = file(infofile_name, "w")
                    f.write(info.to_info_str())
                    f.close()
                except IOError, e:
                    print " [Error]"
                    print str(e)
            else:
                # Skip this file
                continue

        # Handle globs
        elif ('*' in filespec) or ('?' in filespec):
            filespecs.extend(glob(filespec))



if __name__ == "__main__":
    main()

