#!/usr/bin/env python
"""Script to copy brifti files from the git repos into nipype.

I stole this from nipy.tools.copy_brifti.py.  Matthew Brett is the
original author, I've hacked the script to make it work with nipype.

The script downloads the current pynifti git repository from my github
account, pulls out the nifti python modules that we include in nipype,
updates their impot paths, copies the modules into the
nipype/externals/pynifti directory, then cleans up the temporary
files/directories.

Usage:
    ./copy_brifti.py

It is assumed that this script lives in trunk/nipype/externals and
that the python modules are in a subdirectory named 'pynifti'.

"""

import os
import sys
import shutil
import tempfile
import functools
import subprocess
import re

# search replaces for imports
subs = (
    (re.compile(r'^([ >]*)(import|from) +nifti'),
     r'\1\2 nipype.externals.pynifti'),
    )

caller = functools.partial(subprocess.call, shell=True)
#git_path = 'git://github.com/cburns/pynifti.git'
# Working locally is much faster
git_path = '/home/cburns/src/pynifti.git'
git_tag = 'HEAD'

# Assume this script resides in the trunk/nipype/externals directory,
# and there is a subdirectory called pynifti where the brifti files
# live.
out_path = 'pynifti'

def create_archive(out_path, git_path, git_tag):
    out_path = os.path.abspath(out_path)
    pwd = os.path.abspath(os.curdir)
    # put git clone in a tmp directory
    tmp_path = tempfile.mkdtemp()
    os.chdir(tmp_path)
    caller('git clone ' + git_path)
    # We only want the 'nifti' directory from the git repos, we'll
    # create an archive of that directory.
    os.chdir('pynifti')
    caller('git archive %s nifti > nifti.tar' % git_tag)
    os.chdir(tmp_path)
    # extract tarball and modify files before copying into out_path
    caller('tar xvf pynifti/nifti.tar')
    # done with git repository, remove it
    shutil.rmtree('pynifti')
    # For nipype, we don't copy the tests
    shutil.rmtree('nifti/derivations')
    shutil.rmtree('nifti/testing')
    shutil.rmtree('nifti/tests')
    # Walk through the nifti directory and update the import paths to
    # nipype paths.
    for root, dirs, files in os.walk('nifti'):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            lines = file(fpath).readlines()
            outfile = file(fpath, 'wt')
            for line in lines:
                for regexp, repstr in subs:
                    if regexp.search(line):
                        line = regexp.sub(repstr, line)
                        continue
                outfile.write(line)
            outfile.close()
    # Create tarball of new files
    os.chdir('nifti')
    caller('tar cvf nifti.tar *')
    # Move the tarball to the nipype directory
    dst = os.path.join(out_path, 'nifti.tar')
    shutil.move('nifti.tar', dst)
    os.chdir(out_path)
    # Extract the tarball, overwriting existing files.
    caller('tar xvf nifti.tar')
    # Remove the tarball
    os.unlink(dst)
    # Remove temporary directory
    shutil.rmtree(tmp_path)

if __name__ == '__main__':
    create_archive(out_path, git_path, git_tag)
