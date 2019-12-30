# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Created on 20 Apr 2010

logging options : INFO, DEBUG
hash_method : content, timestamp

@author: Chris Filo Gorgolewski
"""
import os
import sys
import errno
import atexit
from warnings import warn
from distutils.version import LooseVersion
import configparser
import numpy as np

from simplejson import load, dump

from .misc import str2bool
from filelock import SoftFileLock

CONFIG_DEPRECATIONS = {
    "profile_runtime": ("monitoring.enabled", "1.0"),
    "filemanip_level": ("logging.utils_level", "1.0"),
}


DEFAULT_CONFIG_TPL = """\
[logging]
workflow_level = INFO
utils_level = INFO
interface_level = INFO
log_to_file = false
log_directory = {log_dir}
log_size = 16384000
log_rotate = 4

[execution]
create_report = true
crashdump_dir = {crashdump_dir}
hash_method = timestamp
job_finished_timeout = 5
keep_inputs = false
local_hash_check = true
matplotlib_backend = Agg
plugin = Linear
remove_node_directories = false
remove_unnecessary_outputs = true
try_hard_link_datasink = true
single_thread_matlab = true
crashfile_format = pklz
stop_on_first_crash = false
stop_on_first_rerun = false
use_relative_paths = false
stop_on_unknown_version = false
write_provenance = false
parameterize_dirs = true
poll_sleep_duration = 2
xvfb_max_wait = 10
check_version = true

[monitoring]
enabled = false
sample_frequency = 1
summary_append = true

[check]
interval = 1209600
"""


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class NipypeConfig(object):
    """Base nipype config class"""

    def __init__(self, *args, **kwargs):
        self._config = configparser.ConfigParser()
        self._cwd = None

        config_dir = os.path.expanduser(
            os.getenv("NIPYPE_CONFIG_DIR", default="~/.nipype")
        )
        self.data_file = os.path.join(config_dir, "nipype.json")

        self.set_default_config()
        self._display = None
        self._resource_monitor = None

        self._config.read([os.path.join(config_dir, "nipype.cfg"), "nipype.cfg"])

        for option in CONFIG_DEPRECATIONS:
            for section in ["execution", "logging", "monitoring"]:
                if self.has_option(section, option):
                    new_section, new_option = CONFIG_DEPRECATIONS[option][0].split(".")
                    if not self.has_option(new_section, new_option):
                        # Warn implicit in get
                        self.set(new_section, new_option, self.get(section, option))

    @property
    def cwd(self):
        """Cache current working directory ASAP"""
        # Run getcwd only once, preventing multiproc to finish
        # with error having changed to the wrong path
        if self._cwd is None:
            try:
                self._cwd = os.getcwd()
            except OSError:
                warn(
                    'Trying to run Nipype from a nonexistent directory "{}".'.format(
                        os.getenv("PWD", "unknown")
                    ),
                    RuntimeWarning,
                )
                raise
        return self._cwd

    def set_default_config(self):
        """Read default settings template and set into config object"""
        default_cfg = DEFAULT_CONFIG_TPL.format(
            log_dir=os.path.expanduser("~"),  # Get $HOME in a platform-agnostic way
            crashdump_dir=self.cwd,  # Read cached cwd
        )

        try:
            self._config.read_string(default_cfg)  # Python >= 3.2
        except AttributeError:
            from io import StringIO

            self._config.readfp(StringIO(default_cfg))

    def enable_debug_mode(self):
        """Enables debug configuration"""
        from .. import logging

        self._config.set("execution", "stop_on_first_crash", "true")
        self._config.set("execution", "remove_unnecessary_outputs", "false")
        self._config.set("execution", "keep_inputs", "true")
        self._config.set("logging", "workflow_level", "DEBUG")
        self._config.set("logging", "interface_level", "DEBUG")
        self._config.set("logging", "utils_level", "DEBUG")
        logging.update_logging(self._config)

    def set_log_dir(self, log_dir):
        """Sets logging directory

        This should be the first thing that is done before any nipype class
        with logging is imported.
        """
        self._config.set("logging", "log_directory", log_dir)

    def get(self, section, option, default=None):
        """Get an option"""
        if option in CONFIG_DEPRECATIONS:
            msg = (
                'Config option "%s" has been deprecated as of nipype %s. '
                'Please use "%s" instead.'
            ) % (option, CONFIG_DEPRECATIONS[option][1], CONFIG_DEPRECATIONS[option][0])
            warn(msg)
            section, option = CONFIG_DEPRECATIONS[option][0].split(".")

        if self._config.has_option(section, option):
            return self._config.get(section, option)
        return default

    def set(self, section, option, value):
        """Set new value on option"""
        if isinstance(value, bool):
            value = str(value)

        if option in CONFIG_DEPRECATIONS:
            msg = (
                'Config option "%s" has been deprecated as of nipype %s. '
                'Please use "%s" instead.'
            ) % (option, CONFIG_DEPRECATIONS[option][1], CONFIG_DEPRECATIONS[option][0])
            warn(msg)
            section, option = CONFIG_DEPRECATIONS[option][0].split(".")

        return self._config.set(section, option, value)

    def getboolean(self, section, option):
        """Get a boolean option from section"""
        return self._config.getboolean(section, option)

    def has_option(self, section, option):
        """Check if option exists in section"""
        return self._config.has_option(section, option)

    @property
    def _sections(self):
        return self._config._sections

    def get_data(self, key):
        """Read options file"""
        if not os.path.exists(self.data_file):
            return None
        with SoftFileLock("%s.lock" % self.data_file):
            with open(self.data_file, "rt") as file:
                datadict = load(file)
        if key in datadict:
            return datadict[key]
        return None

    def save_data(self, key, value):
        """Store config flie"""
        datadict = {}
        if os.path.exists(self.data_file):
            with SoftFileLock("%s.lock" % self.data_file):
                with open(self.data_file, "rt") as file:
                    datadict = load(file)
        else:
            dirname = os.path.dirname(self.data_file)
            if not os.path.exists(dirname):
                mkdir_p(dirname)
        with SoftFileLock("%s.lock" % self.data_file):
            with open(self.data_file, "wt") as file:
                datadict[key] = value
                dump(datadict, file)

    def update_config(self, config_dict):
        """Extend internal dictionary with config_dict"""
        for section in ["execution", "logging", "check"]:
            if section in config_dict:
                for key, val in list(config_dict[section].items()):
                    if not key.startswith("__"):
                        self._config.set(section, key, str(val))

    def update_matplotlib(self):
        """Set backend on matplotlib from options"""
        import matplotlib

        matplotlib.use(self.get("execution", "matplotlib_backend"))

    def enable_provenance(self):
        """Sets provenance storing on"""
        self._config.set("execution", "write_provenance", "true")
        self._config.set("execution", "hash_method", "content")

    @property
    def resource_monitor(self):
        """Check if resource_monitor is available"""
        if self._resource_monitor is not None:
            return self._resource_monitor

        # Cache config from nipype config
        self.resource_monitor = (
            str2bool(self._config.get("monitoring", "enabled")) or False
        )
        return self._resource_monitor

    @resource_monitor.setter
    def resource_monitor(self, value):
        # Accept string true/false values
        if isinstance(value, (str, bytes)):
            value = str2bool(value.lower())

        if value is False:
            self._resource_monitor = False
        elif value is True:
            if not self._resource_monitor:
                # Before setting self._resource_monitor check psutil
                # availability
                self._resource_monitor = False
                try:
                    import psutil

                    self._resource_monitor = LooseVersion(
                        psutil.__version__
                    ) >= LooseVersion("5.0")
                except ImportError:
                    pass
                finally:
                    if not self._resource_monitor:
                        warn(
                            "Could not enable the resource monitor: "
                            "psutil>=5.0 could not be imported."
                        )
                    self._config.set(
                        "monitoring", "enabled", ("%s" % self._resource_monitor).lower()
                    )

    def enable_resource_monitor(self):
        """Sets the resource monitor on"""
        self.resource_monitor = True

    def disable_resource_monitor(self):
        """Sets the resource monitor off"""
        self.resource_monitor = False

    def get_display(self):
        """Returns the first display available"""

        # Check if an Xorg server is listening
        # import subprocess as sp
        # if not hasattr(sp, 'DEVNULL'):
        #     setattr(sp, 'DEVNULL', os.devnull)
        # x_listening = bool(sp.call('ps au | grep -v grep | grep -i xorg',
        #                    shell=True, stdout=sp.DEVNULL))

        if self._display is not None:
            return ":%d" % self._display.new_display

        sysdisplay = None
        if self._config.has_option("execution", "display_variable"):
            sysdisplay = self._config.get("execution", "display_variable")

        sysdisplay = sysdisplay or os.getenv("DISPLAY")
        if sysdisplay:
            from collections import namedtuple

            def _mock():
                pass

            # Store a fake Xvfb object. Format - <host>:<display>[.<screen>]
            ndisp = sysdisplay.split(":")[-1].split(".")[0]
            Xvfb = namedtuple("Xvfb", ["new_display", "stop"])
            self._display = Xvfb(int(ndisp), _mock)
            return self.get_display()
        else:
            if "darwin" in sys.platform:
                raise RuntimeError(
                    "Xvfb requires root permissions to run in OSX. Please "
                    "make sure that an X server is listening and set the "
                    "appropriate config on either $DISPLAY or nipype's "
                    '"display_variable" config. Valid X servers include '
                    "VNC, XQuartz, or manually started Xvfb."
                )

            # If $DISPLAY is empty, it confuses Xvfb so unset
            if sysdisplay == "":
                del os.environ["DISPLAY"]
            try:
                from xvfbwrapper import Xvfb
            except ImportError:
                raise RuntimeError(
                    "A display server was required, but $DISPLAY is not "
                    "defined and Xvfb could not be imported."
                )

            self._display = Xvfb(nolisten="tcp")
            self._display.start()

            # Older versions of xvfbwrapper used vdisplay_num
            if not hasattr(self._display, "new_display"):
                setattr(self._display, "new_display", self._display.vdisplay_num)
            return self.get_display()

    def stop_display(self):
        """Closes the display if started"""
        if self._display is not None:
            from .. import logging

            self._display.stop()
            logging.getLogger("nipype.interface").debug("Closing display (if virtual)")


@atexit.register
def free_display():
    """Stop virtual display (if it is up)"""
    from .. import config

    config.stop_display()
