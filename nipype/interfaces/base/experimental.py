"""Experimental Nipype 1.99 interfaces."""
import os
import sys
import platform
import json
from io import StringIO
from string import Formatter
from contextlib import AbstractContextManager
from copy import deepcopy
from datetime import datetime as dt
from dateutil.parser import parse as parseutc

from ... import config, logging
from ...utils.misc import str2bool, rgetcwd
from ...utils.provenance import write_provenance

from .support import Bunch, InterfaceResult
from .traits_extension import isdefined


iflogger = logging.getLogger("nipype.interface")


class Interface:
    """An abstract definition for interfaces."""

    _input_spec = None
    """A traited input specification"""
    _output_spec = None
    """A traited output specification"""
    _redirect_x = False

    @classmethod
    def exec(cls, **inputs):
        """Instantiate the interface and run it."""
        return cls(**inputs).run()

    def __init__(self, from_file=None, resource_monitor=None, **inputs):
        """Initialize an interface."""
        if self._input_spec is None:
            raise TypeError(
                "Input specification type not set for interface "
                '"%s"' % self.__class__.__name__)
        if self._output_spec is None:
            raise TypeError(
                "Output specification type not set for interface "
                '"%s"' % self.__class__.__name__)

        self._resource_monitor = config.resource_monitor
        if resource_monitor is not None:
            self._resource_monitor = self._resource_monitor and bool(resource_monitor)

        # Initialize input object
        self.inputs = self._input_spec(**inputs)

        # Initialize inputs from JSON file
        if from_file is not None:
            self.from_json(from_file, overwrite=True)

            for name, value in list(inputs.items()):
                setattr(self.inputs, name, value)

    def run(self, cwd=None):
        """
        Execute this interface.

        This interface will not raise an exception if runtime.returncode is
        non-zero.

        Parameters
        ----------
        cwd : specify a folder where the interface should be run
        inputs : allows the interface settings to be updated

        Returns
        -------
        results :  :obj:`nipype.interfaces.base.support.InterfaceResult`
            A copy of the instance that was executed, provenance information and,
            if successful, results

        """
        from ...utils.profiler import ResourceMonitor

        # Tear-up: get current and prev directories
        syscwd = rgetcwd(error=False)  # Recover when wd does not exist
        if cwd is None:
            cwd = syscwd

        os.chdir(cwd)  # Change to the interface wd
        env = deepcopy(dict(os.environ))
        if self._redirect_x:
            env["DISPLAY"] = config.get_display()

        runtime = Bunch(
            cwd=cwd,
            prevcwd=syscwd,
            returncode=None,
            duration=None,
            environ=env,
            startTime=dt.isoformat(dt.utcnow()),
            endTime=None,
            platform=platform.platform(),
            hostname=platform.node(),
        )
        runtime_attrs = set(runtime.dictcopy())
        runtime = self._pre_run_hook(runtime)

        mon_sp = None
        if self._resource_monitor:
            mon_freq = float(config.get("execution", "resource_monitor_frequency", 1))
            proc_pid = os.getpid()
            iflogger.debug(
                "Creating a ResourceMonitor on a %s interface, PID=%d.",
                self.__class__.__name__,
                proc_pid,
            )
            mon_sp = ResourceMonitor(proc_pid, freq=mon_freq)
            mon_sp.start()

        # Grab inputs now, as they should not change during execution
        inputs = self.inputs.get_traitsfree()
        stdout = StringIO()
        stderr = StringIO()
        try:
            with RedirectStandardStreams(stdout, stderr=stderr):
                runtime = self._run_interface(runtime)
        except Exception as e:
            import traceback

            # Retrieve the maximum info fast
            runtime.traceback = traceback.format_exc()
            # Gather up the exception arguments and append nipype info.
            exc_args = e.args if getattr(e, "args") else tuple()
            exc_args += (
                "An exception of type %s occurred while running interface %s."
                % (type(e).__name__, self.__class__.__name__),
            )
            if config.get("logging", "interface_level", "info").lower() == "debug":
                exc_args += ("Inputs: %s" % str(self.inputs),)

            runtime.traceback_args = ("\n".join(["%s" % arg for arg in exc_args]),)

            stderr.write("Nipype captured error:\n\n%s" % runtime.traceback)
            raise
        else:
            # Execute post-hook only if successful
            runtime = self._post_run_hook(runtime)
        finally:
            if runtime is None or runtime_attrs - set(runtime.dictcopy()):
                raise RuntimeError(
                    "{} interface failed to return valid "
                    "runtime object".format(self.__class__.__name__)
                )

            # This needs to be done always
            runtime.endTime = dt.isoformat(dt.utcnow())
            timediff = parseutc(runtime.endTime) - parseutc(runtime.startTime)
            runtime.duration = (
                timediff.days * 86400 + timediff.seconds + timediff.microseconds / 1e6
            )
            results = InterfaceResult(
                self.__class__, runtime, inputs=inputs, outputs=None, provenance=None
            )

            # Add provenance (if required)
            if str2bool(config.get("execution", "write_provenance", "false")):
                # Provenance will only throw a warning if something went wrong
                results.provenance = write_provenance(results)

            # Make sure runtime profiler is shut down
            if self._resource_monitor:
                import numpy as np

                mon_sp.stop()

                runtime.mem_peak_gb = None
                runtime.cpu_percent = None

                # Read .prof file in and set runtime values
                vals = np.loadtxt(mon_sp.fname, delimiter=",")
                if vals.size:
                    vals = np.atleast_2d(vals)
                    runtime.mem_peak_gb = vals[:, 2].max() / 1024
                    runtime.cpu_percent = vals[:, 1].max()

                    runtime.prof_dict = {
                        "time": vals[:, 0].tolist(),
                        "cpus": vals[:, 1].tolist(),
                        "rss_GiB": (vals[:, 2] / 1024).tolist(),
                        "vms_GiB": (vals[:, 3] / 1024).tolist(),
                    }
                results.runtime = runtime

            # Store captured outputs
            runtime.stdout = stdout.getvalue()
            runtime.stderr = stderr.getvalue()

            del stdout
            del stderr

            results.outputs = self._find_outputs(runtime)
            os.chdir(syscwd)

        return results

    def from_json(self, json_file, overwrite=True):
        """Import inputs from a JSON file."""
        with open(json_file) as fhandle:
            inputs_dict = json.load(fhandle)

        def_inputs = set()
        if not overwrite:
            def_inputs = {i for i in self.inputs.get_traitsfree().keys()}

        new_inputs = set(inputs_dict.keys()) - def_inputs
        for key in new_inputs:
            if hasattr(self.inputs, key):
                setattr(self.inputs, key, inputs_dict[key])

    def _run_interface(self, runtime):
        """Execute the body of this interface."""
        raise NotImplementedError

    def _find_outputs(self, runtime):
        """
        Automagically fill in output fields.

        Returns
        -------
        outputs : :obj:`traits.HasTraits`
            Collected outputs

        """
        outputs = self._output_spec()
        inputs = self.inputs.get_traitsfree()

        for name, spec in list(outputs.traits(transient=None).items()):
            if spec.stdout is True:
                setattr(outputs, name, runtime.stdout)
                continue
            elif callable(spec.stdout):
                setattr(outputs, name, spec.stdout(runtime.stdout))
                continue

            if spec.stderr is True:
                setattr(outputs, name, runtime.stderr)
                continue
            elif callable(spec.stderr):
                setattr(outputs, name, spec.stderr(runtime.stderr))
                continue

            out_template = getattr(outputs, name)
            if not isdefined(out_template):
                continue

            template_fields = {pat[1] for pat in Formatter().parse(out_template)
                               if pat[1] and not pat[1].isdigit()}

            if template_fields.intersection(inputs.keys()):
                fields = {}
                for field in template_fields:
                    fname = os.path.basename(inputs[field])
                    fname, ext = os.path.splitext(fname)
                    if ext == '.gz':
                        fname, ext0 = os.path.splitext(fname)
                        ext = ''.join((ext0, ext))
                    fields[field] = fname

                # Only the last extension is kept, if several template
                # names
                setattr(outputs, name,
                        ''.join((out_template.format(**fields), ext)))
        return outputs

    def _pre_run_hook(self, runtime):
        """
        Perform any pre-_run_interface() processing.

        Subclasses may override this function to modify ``runtime`` object or
        interface state

        MUST return runtime object
        """
        return runtime

    def _post_run_hook(self, runtime):
        """
        Perform any post-_run_interface() processing.

        Subclasses may override this function to modify ``runtime`` object or
        interface state

        MUST return runtime object
        """
        return runtime


class RedirectStandardStreams(AbstractContextManager):
    """
    Context that redirects standard out/err.

    Examples
    --------
    >>> f = StringIO()
    >>> with RedirectStandardStreams(f):
    ...     print("1")
    ...     print("2", file=sys.stderr)
    >>> captured = f.getvalue()
    >>> "1" in captured
    True
    >>> "2" in captured
    True

    >>> out = StringIO()
    >>> err = StringIO()
    >>> with RedirectStandardStreams(out, err):
    ...     print("1")
    ...     print("2", file=sys.stderr)
    >>> captured_out = out.getvalue()
    >>> "1" in captured_out
    True
    >>> "2" in captured_out
    False
    >>> captured_err = err.getvalue()
    >>> "1" in captured_err
    False
    >>> "2" in captured_err
    True

    """

    _defaults = (sys.stdout, sys.stderr)

    def __init__(self, stdout, stderr=None):
        """Redirect standard streams."""
        self._out_target = stdout
        self._err_target = stderr

    def __enter__(self):
        sys.stdout = self._out_target
        sys.stderr = self._err_target
        if self._err_target is None:
            sys.stderr = self._out_target
            return self._out_target
        return self._out_target, self._err_target

    def __exit__(self, exctype, excinst, exctb):
        sys.stdout, sys.stderr = self._defaults
