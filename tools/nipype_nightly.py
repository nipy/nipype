#!/usr/bin/env python

"""Simple script to update the trunk nightly, build the docs and push
to sourceforge.
"""

from __future__ import print_function
from __future__ import unicode_literals
from builtins import open
import os
import sys
import subprocess

dirname = '/home/cburns/src/nipy-sf/nipype/trunk/'


def run_cmd(cmd):
    print(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=os.environ,
                            shell=True)
    output, error = proc.communicate()
    returncode = proc.returncode
    if returncode:
        msg = 'Running cmd: %s\n Error: %s' % (cmd, error)
        raise Exception(msg)
    print(output)


def update_repos():
    """Update svn repository."""
    os.chdir(dirname)
    cmd = 'svn update'
    run_cmd(cmd)


def build_docs():
    """Build the sphinx documentation."""
    os.chdir(os.path.join(dirname, 'doc'))
    cmd = 'make html'
    run_cmd(cmd)


def push_to_sf():
    """Push documentation to sourceforge."""
    os.chdir(dirname + 'doc')
    cmd = 'make sf_cburns'
    run_cmd(cmd)


def setup_paths():
    # Cron has no PYTHONPATH defined, so we need to add the paths to
    # all libraries we need.
    pkg_path = '/home/cburns/local/lib/python2.6/site-packages/'
    pkg_path_64 = '/home/cburns/local/lib64/python2.6/site-packages/'

    # Add the current directory to path
    sys.path.insert(0, os.curdir)
    # Add our local path, where we install nipype, to sys.path
    sys.path.insert(0, pkg_path)
    # Needed to add this to my path at one point otherwise import of
    # apigen failed.
    # sys.path.insert(2, '/home/cburns/src/nipy-sf/nipype/trunk/tools')

    # Add networkx, twisted, zope.interface and foolscap.
    # Basically we need to add all the packages we need that are
    # installed via setyptools, since it's uses the .pth files for
    # this.
    nx_path = os.path.join(pkg_path, 'networkx-0.99-py2.6.egg')
    sys.path.insert(2, nx_path)
    twisted_path = os.path.join(pkg_path_64,
                                'Twisted-8.2.0-py2.6-linux-x86_64.egg')
    sys.path.insert(2, twisted_path)
    zope_path = os.path.join(pkg_path_64,
                             'zope.interface-3.5.2-py2.6-linux-x86_64.egg')
    sys.path.insert(2, zope_path)
    foolscap_path = os.path.join(pkg_path,
                                 'foolscap-0.2.9-py2.6.egg')
    sys.path.insert(2, foolscap_path)

    # Define our PYTHONPATH variable
    os.environ['PYTHONPATH'] = ':'.join(sys.path)

if __name__ == '__main__':
    setup_paths()
    prev_dir = os.path.abspath(os.curdir)
    update_repos()
    build_docs()
    # push_to_sf()
    os.chdir(prev_dir)
