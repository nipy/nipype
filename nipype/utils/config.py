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
log_size = 254000
log_rotate = 4

[execution]
stop_on_first_crash = false
hash_method = content
single_thread_matlab = true
run_in_series = false
remove_node_directories = false
use_relative_paths = false
"""%(homedir))

config = ConfigParser.ConfigParser()
config.readfp(default_cfg)
config.read([os.path.expanduser('~/.nipype.cfg'), 'nipype.cfg'])

