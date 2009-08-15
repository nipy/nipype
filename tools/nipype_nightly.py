#!/usr/bin/env python

"""Simple script to update the trunk nightly, build the docs and push
to sourceforge.
"""

import os
import subprocess

dirname = '/home/cburns/src/nipy-sf/nipype/trunk/'

#color_green = '\033[0;32m'
#color_null = '\033[0m'

def run_cmd(cmd):
    #print color_green + cmd + color_null
    print cmd
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    output, error = proc.communicate()
    returncode = proc.returncode
    if returncode:
        msg = 'Running cmd: %s\n Error: %s' % (cmd, error)
        raise StandardError(msg)
    print output

def update_repos():
    """Update svn repository."""
    os.chdir(dirname)
    cmd = 'svn update'
    run_cmd(cmd)

def build_docs():
    """Build the sphinx documentation."""
    os.chdir(dirname + 'doc')
    cmd = 'make html'
    run_cmd(cmd)

def push_to_sf():
    """Push documentation to sourceforge."""
    os.chdir(dirname + 'doc')
    cmd = 'make sf_cburns'
    run_cmd(cmd)


if __name__ == '__main__':
    prev_dir = os.path.abspath(os.curdir)
    update_repos()
    build_docs()
    push_to_sf()
    os.chdir(prev_dir)



