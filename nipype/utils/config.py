# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Created on 20 Apr 2010

logging options : INFO, DEBUG
hash_method : content, timestamp

@author: Chris Filo Gorgolewski
'''
import ConfigParser, os
from StringIO import StringIO
import os

homedir = os.environ['HOME']
default_cfg = StringIO("""
[logging]
workflow_level = INFO
filemanip_level = INFO
interface_level = INFO
log_directory = %s
log_size = 16384000
log_rotate = 4

[execution]
plugin = Linear
stop_on_first_crash = false
stop_on_first_rerun = false
hash_method = timestamp
single_thread_matlab = true
remove_node_directories = false
remove_unnecessary_outputs = true
use_relative_paths = false
matplotlib_backend = Agg
"""%(homedir))

config = ConfigParser.ConfigParser()
config.readfp(default_cfg)
config.read([os.path.expanduser('~/.nipype.cfg'), 'nipype.cfg'])

