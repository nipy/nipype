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
keep_inputs = false
hash_method = timestamp
single_thread_matlab = true
remove_node_directories = false
remove_unnecessary_outputs = true
use_relative_paths = false
matplotlib_backend = Agg
"""%(homedir))

class NipypeConfig(ConfigParser.ConfigParser):
    """Base nipype config class
    """

    def enable_debug_mode(self):
        """Enables debug configuration
        """
        config.set('execution', 'stop_on_first_crash', 'true')
        config.set('execution', 'remove_unnecessary_outputs', 'false')
        config.set('logging', 'workflow_level', 'DEBUG')
        config.set('logging', 'interface_level', 'DEBUG')

    def set_log_dir(self, log_dir):
        """Sets logging directory

        This should be the first thing that is done before any nipype class
        with logging is imported.
        """
        config.set('logging', 'log_directory', log_dir)

"""
Initialize the config object in module load
"""

config = NipypeConfig()
config.readfp(default_cfg)
config.read([os.path.expanduser('~/.nipype.cfg'), 'nipype.cfg'])