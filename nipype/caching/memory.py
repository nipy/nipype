# -*- coding: utf-8 -*-
"""
Using nipype with persistence and lazy recomputation but without explicit
name-steps pipeline: getting back scope in command-line based programming.
"""
import os
import hashlib
import pickle
import time
import shutil
import glob

from ..interfaces.base import BaseInterface
from ..pipeline.engine import Node
from ..pipeline.engine.utils import modify_paths

###############################################################################
# PipeFunc object: callable interface to nipype.interface objects


class PipeFunc(object):
    """ Callable interface to nipype.interface objects

        Use this to wrap nipype.interface object and call them
        specifying their input with keyword arguments::

            fsl_merge = PipeFunc(fsl.Merge, base_dir='.')
            out = fsl_merge(in_files=files, dimension='t')
    """

    def __init__(self, interface, base_dir, callback=None):
        """

            Parameters
            ===========
            interface: a nipype interface class
                The interface class to wrap
            base_dir: a string
                The directory in which the computation will be
                stored
            callback: a callable
                An optional callable called each time after the function
                is called.
        """
        if not (isinstance(interface, type) and issubclass(interface, BaseInterface)):
            raise ValueError(
                "the interface argument should be a nipype "
                "interface class, but %s (type %s) was passed."
                % (interface, type(interface))
            )
        self.interface = interface
        base_dir = os.path.abspath(base_dir)
        if not os.path.exists(base_dir) and os.path.isdir(base_dir):
            raise ValueError("base_dir should be an existing directory")
        self.base_dir = base_dir
        doc = "%s\n%s" % (self.interface.__doc__, self.interface.help(returnhelp=True))
        self.__doc__ = doc
        self.callback = callback

    def __call__(self, **kwargs):
        kwargs = modify_paths(kwargs, relative=False)
        interface = self.interface()
        # Set the inputs early to get some argument checking
        interface.inputs.trait_set(**kwargs)
        # Make a name for our node
        inputs = interface.inputs.get_hashval()
        hasher = hashlib.new("md5")
        hasher.update(pickle.dumps(inputs))
        dir_name = "%s-%s" % (
            interface.__class__.__module__.replace(".", "-"),
            interface.__class__.__name__,
        )
        job_name = hasher.hexdigest()
        node = Node(interface, name=job_name)
        node.base_dir = os.path.join(self.base_dir, dir_name)

        cwd = os.getcwd()
        try:
            out = node.run()
        finally:
            # node.run() changes to the node directory - if something goes
            # wrong before it cds back you would end up in strange places
            os.chdir(cwd)
        if self.callback is not None:
            self.callback(dir_name, job_name)
        return out

    def __repr__(self):
        return "{}({}.{}), base_dir={})".format(
            self.__class__.__name__,
            self.interface.__module__,
            self.interface.__name__,
            self.base_dir,
        )


###############################################################################
# Memory manager: provide some tracking about what is computed when, to
# be able to flush the disk


def read_log(filename, run_dict=None):
    if run_dict is None:
        run_dict = dict()

    with open(filename, "r") as logfile:
        for line in logfile:
            dir_name, job_name = line[:-1].split("/")
            jobs = run_dict.get(dir_name, set())
            jobs.add(job_name)
            run_dict[dir_name] = jobs
    return run_dict


def rm_all_but(base_dir, dirs_to_keep, warn=False):
    """ Remove all the sub-directories of base_dir, but those listed

        Parameters
        ============
        base_dir: string
            The base directory
        dirs_to_keep: set
            The names of the directories to keep
    """
    try:
        all_dirs = os.listdir(base_dir)
    except OSError:
        "Dir has been deleted"
        return
    all_dirs = [d for d in all_dirs if not d.startswith("log.")]
    dirs_to_rm = list(dirs_to_keep.symmetric_difference(all_dirs))
    for dir_name in dirs_to_rm:
        dir_name = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_name):
            if warn:
                print("removing directory: %s" % dir_name)
            shutil.rmtree(dir_name)


class _MemoryCallback(object):
    "An object to avoid closures and have everything pickle"

    def __init__(self, memory):
        self.memory = memory

    def __call__(self, dir_name, job_name):
        self.memory._log_name(dir_name, job_name)


class Memory(object):
    """ Memory context to provide caching for interfaces

        Parameters
        ==========
        base_dir: string
            The directory name of the location for the caching

        Methods
        =======
        cache
            Creates a cacheable function from an nipype Interface class
        clear_previous_runs
            Removes from the disk all the runs that where not used after
            the creation time of the specific Memory instance
        clear_previous_runs
            Removes from the disk all the runs that where not used after
            the given time
    """

    def __init__(self, base_dir):
        base_dir = os.path.join(os.path.abspath(base_dir), "nipype_mem")
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
        elif not os.path.isdir(base_dir):
            raise ValueError("base_dir should be a directory")
        self.base_dir = base_dir
        open(os.path.join(base_dir, "log.current"), "a").close()

    def cache(self, interface):
        """ Returns a callable that caches the output of an interface

            Parameters
            ==========
            interface: nipype interface
                The nipype interface class to be wrapped and cached

            Returns
            =======
            pipe_func: a PipeFunc callable object
                An object that can be used as a function to apply the
                interface to arguments. Inputs of the interface are given
                as keyword arguments, bearing the same name as the name
                in the inputs specs of the interface.

            Examples
            ========

            >>> from tempfile import mkdtemp
            >>> mem = Memory(mkdtemp())
            >>> from nipype.interfaces import fsl

            Here we create a callable that can be used to apply an
            fsl.Merge interface to files

            >>> fsl_merge = mem.cache(fsl.Merge)

            Now we apply it to a list of files. We need to specify the
            list of input files and the dimension along which the files
            should be merged.

            >>> results = fsl_merge(in_files=['a.nii', 'b.nii'],
            ...                     dimension='t') # doctest: +SKIP

            We can retrieve the resulting file from the outputs:
            >>> results.outputs.merged_file # doctest: +SKIP
            '...'
        """
        return PipeFunc(interface, self.base_dir, _MemoryCallback(self))

    def _log_name(self, dir_name, job_name):
        """ Increment counters tracking which cached function get executed.
        """
        base_dir = self.base_dir
        # Every counter is a file opened in append mode and closed
        # immediately to avoid race conditions in parallel computing:
        # file appends are atomic
        with open(os.path.join(base_dir, "log.current"), "a") as currentlog:
            currentlog.write("%s/%s\n" % (dir_name, job_name))

        t = time.localtime()
        year_dir = os.path.join(base_dir, "log.%i" % t.tm_year)
        try:
            os.mkdir(year_dir)
        except OSError:
            "Dir exists"
        month_dir = os.path.join(year_dir, "%02i" % t.tm_mon)
        try:
            os.mkdir(month_dir)
        except OSError:
            "Dir exists"

        with open(os.path.join(month_dir, "%02i.log" % t.tm_mday), "a") as rotatefile:
            rotatefile.write("%s/%s\n" % (dir_name, job_name))

    def clear_previous_runs(self, warn=True):
        """ Remove all the cache that where not used in the latest run of
            the memory object: i.e. since the corresponding Python object
            was created.

            Parameters
            ==========
            warn: boolean, optional
                If true, echoes warning messages for all directory
                removed
        """
        base_dir = self.base_dir
        latest_runs = read_log(os.path.join(base_dir, "log.current"))
        self._clear_all_but(latest_runs, warn=warn)

    def clear_runs_since(self, day=None, month=None, year=None, warn=True):
        """ Remove all the cache that where not used since the given date

            Parameters
            ==========
            day, month, year: integers, optional
                The integers specifying the latest day (in localtime) that
                a node should have been accessed to be kept. If not
                given, the current date is used.
            warn: boolean, optional
                If true, echoes warning messages for all directory
                removed
        """
        t = time.localtime()
        day = day if day is not None else t.tm_mday
        month = month if month is not None else t.tm_mon
        year = year if year is not None else t.tm_year
        base_dir = self.base_dir
        cut_off_file = "%s/log.%i/%02i/%02i.log" % (base_dir, year, month, day)
        logs_to_flush = list()
        recent_runs = dict()
        for log_name in glob.glob("%s/log.*/*/*.log" % base_dir):
            if log_name < cut_off_file:
                logs_to_flush.append(log_name)
            else:
                recent_runs = read_log(log_name, recent_runs)
        self._clear_all_but(recent_runs, warn=warn)
        for log_name in logs_to_flush:
            os.remove(log_name)

    def _clear_all_but(self, runs, warn=True):
        """ Remove all the runs appart from those given to the function
            input.
        """
        rm_all_but(self.base_dir, set(runs.keys()), warn=warn)
        for dir_name, job_names in list(runs.items()):
            rm_all_but(os.path.join(self.base_dir, dir_name), job_names, warn=warn)

    def __repr__(self):
        return "{}(base_dir={})".format(self.__class__.__name__, self.base_dir)
