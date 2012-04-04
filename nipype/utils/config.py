# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Created on 20 Apr 2010

logging options : INFO, DEBUG
hash_method : content, timestamp

@author: Chris Filo Gorgolewski
'''

import ConfigParser
from json import load, dump
import os
import shutil
from StringIO import StringIO
from warnings import warn

from ..external import portalocker

homedir = os.environ['HOME']
default_cfg = """
[logging]
workflow_level = INFO
filemanip_level = INFO
interface_level = INFO
log_to_file = false
log_directory = %s
log_size = 16384000
log_rotate = 4

[execution]
create_report = true
crashdump_dir = %s
hash_method = timestamp
job_finished_timeout = 5
keep_inputs = false
local_hash_check = false
matplotlib_backend = Agg
plugin = Linear
remove_node_directories = false
remove_unnecessary_outputs = true
single_thread_matlab = true
stop_on_first_crash = false
stop_on_first_rerun = false
use_relative_paths = false

[check]
interval = 1209600
""" % (homedir, os.getcwd())

class NipypeConfig(object):
    """Base nipype config class
    """

    def __init__(self, *args, **kwargs):
        self._config = ConfigParser.ConfigParser()
        config_dir = os.path.expanduser('~/.nipype')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        old_config_file = os.path.expanduser('~/.nipype.cfg')
        new_config_file = os.path.join(config_dir, 'nipype.cfg')
        # To be deprecated in two releases
        if os.path.exists(old_config_file):
            if os.path.exists(new_config_file):
                msg=("Detected presence of both old (%s, used by versions "
                     "< 0.5.2) and new (%s) config files.  This version will "
                     "proceed with the new one. We advise to merge settings "
                     "and remove old config file if you are not planning to "
                     "use previous releases of nipype.") % (old_config_file,
                                                            new_config_file)
                warn(msg)
            else:
                warn("Moving old config file from: %s to %s" % (old_config_file,
                                                                new_config_file))
                shutil.move(old_config_file, new_config_file)
        self.data_file = os.path.join(config_dir, 'nipype.json')
        self._config.readfp(StringIO(default_cfg))
        self._config.read([new_config_file, old_config_file, 'nipype.cfg'])

    def set_default_config(self):
        self._config.readfp(StringIO(default_cfg))

    def enable_debug_mode(self):
        """Enables debug configuration
        """
        self._config.set('execution', 'stop_on_first_crash', 'true')
        self._config.set('execution', 'remove_unnecessary_outputs', 'false')
        self._config.set('execution', 'keep_inputs', 'true')
        self._config.set('logging', 'workflow_level', 'DEBUG')
        self._config.set('logging', 'interface_level', 'DEBUG')

    def set_log_dir(self, log_dir):
        """Sets logging directory

        This should be the first thing that is done before any nipype class
        with logging is imported.
        """
        self._config.set('logging', 'log_directory', log_dir)

    def get(self, section, option):
        return self._config.get(section, option)

    def set(self, section, option, value):
        return self._config.set(section, option, value)

    def getboolean(self, section, option):
        return self._config.getboolean(section, option)

    def has_option(self, section, option):
        return self._config.has_option(section, option)

    @property
    def _sections(self):
        return self._config._sections

    def get_data(self, key):
        if not os.path.exists(self.data_file):
            return None
        with open(self.data_file, 'rt') as file:
            portalocker.lock(file, portalocker.LOCK_EX)
            datadict = load(file)
        if key in datadict:
            return datadict[key]
        return None

    def save_data(self, key, value):
        datadict = {}
        if os.path.exists(self.data_file):
            with open(self.data_file, 'rt') as file:
                portalocker.lock(file, portalocker.LOCK_EX)
                datadict = load(file)
        with open(self.data_file, 'wt') as file:
            portalocker.lock(file, portalocker.LOCK_EX)
            datadict[key] = value
            dump(datadict, file)

    def update_config(self, config_dict):
        for section in ['execution', 'logging', 'check']:
            if section in config_dict:
                for key, val in config_dict[section].items():
                    if not key.startswith('__'):
                        self._config.set(section, key, str(val))
