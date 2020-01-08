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

from ... import config, logging, LooseVersion
from ...utils.misc import str2bool, rgetcwd
from ...utils.provenance import write_provenance

from .core import Interface
from .specs import (
    BaseInterfaceInputSpec
)
from .support import Bunch, InterfaceResult
from .traits_extension import isdefined


iflogger = logging.getLogger("nipype.interface")


class AutoOutputInterface(Interface):
    """
    Implement common interface functionality.

    * Initializes inputs/outputs from input_spec/output_spec
    * Provides help based on input_spec and output_spec
    * Checks for mandatory inputs before running an interface
    * Runs an interface and returns results
    * Determines which inputs should be copied or linked to cwd

    This class does not implement output_spec.
    These should be defined by derived classes.

    This class cannot be instantiated.

    Attributes
    ----------
    input_spec: :obj:`nipype.interfaces.base.specs.TraitedSpec`
        points to the traited class for the inputs
    output_spec: :obj:`nipype.interfaces.base.specs.TraitedSpec`
        points to the traited class for the outputs
    _redirect_x: bool
        should be set to ``True`` when the interface requires
        connecting to a ``$DISPLAY`` (default is ``False``).
    resource_monitor: bool
        If ``False``, prevents resource-monitoring this interface
        If ``True`` monitoring will be enabled IFF the general
        Nipype config is set on (``resource_monitor = true``).

    """

    input_spec = BaseInterfaceInputSpec
    _version = None
    _additional_metadata = []
    _redirect_x = False
    references_ = []
    resource_monitor = True  # Enabled for this interface IFF enabled in the config
    _etelemetry_version_data = None

    def __init__(
        self, from_file=None, resource_monitor=None, ignore_exception=False, **inputs
    ):
        if config.getboolean("execution", "check_version"):
            from ... import check_latest_version

            if AutoOutputInterface._etelemetry_version_data is None:
                AutoOutputInterface._etelemetry_version_data = check_latest_version()

        if not self.input_spec:
            raise Exception("No input_spec in class: %s" % self.__class__.__name__)

        self.inputs = self.input_spec(**inputs)
        self.ignore_exception = ignore_exception

        if resource_monitor is not None:
            self.resource_monitor = resource_monitor

        if from_file is not None:
            self.load_inputs_from_json(from_file, overwrite=True)

            for name, value in list(inputs.items()):
                setattr(self.inputs, name, value)

    def _outputs(self):
        """ Returns a bunch containing output fields for the class
        """
        outputs = None
        if self.output_spec:
            outputs = self.output_spec()

        return outputs

    def _check_requires(self, spec, name, value):
        """ check if required inputs are satisfied
        """
        if spec.requires:
            values = [
                not isdefined(getattr(self.inputs, field)) for field in spec.requires
            ]
            if any(values) and isdefined(value):
                if len(values) > 1:
                    fmt = (
                        "%s requires values for inputs %s because '%s' is set. "
                        "For a list of required inputs, see %s.help()"
                    )
                else:
                    fmt = (
                        "%s requires a value for input %s because '%s' is set. "
                        "For a list of required inputs, see %s.help()"
                    )
                msg = fmt % (
                    self.__class__.__name__,
                    ", ".join("'%s'" % req for req in spec.requires),
                    name,
                    self.__class__.__name__,
                )
                raise ValueError(msg)

    def _check_xor(self, spec, name, value):
        """ check if mutually exclusive inputs are satisfied
        """
        if spec.xor:
            values = [isdefined(getattr(self.inputs, field)) for field in spec.xor]
            if not any(values) and not isdefined(value):
                msg = (
                    "%s requires a value for one of the inputs '%s'. "
                    "For a list of required inputs, see %s.help()"
                    % (
                        self.__class__.__name__,
                        ", ".join(spec.xor),
                        self.__class__.__name__,
                    )
                )
                raise ValueError(msg)

    def _check_mandatory_inputs(self):
        """ Raises an exception if a mandatory input is Undefined
        """
        for name, spec in list(self.inputs.traits(mandatory=True).items()):
            value = getattr(self.inputs, name)
            self._check_xor(spec, name, value)
            if not isdefined(value) and spec.xor is None:
                msg = (
                    "%s requires a value for input '%s'. "
                    "For a list of required inputs, see %s.help()"
                    % (self.__class__.__name__, name, self.__class__.__name__)
                )
                raise ValueError(msg)
            if isdefined(value):
                self._check_requires(spec, name, value)
        for name, spec in list(
            self.inputs.traits(mandatory=None, transient=None).items()
        ):
            self._check_requires(spec, name, getattr(self.inputs, name))

    def _check_version_requirements(self, trait_object, raise_exception=True):
        """ Raises an exception on version mismatch
        """
        unavailable_traits = []
        # check minimum version
        check = dict(min_ver=lambda t: t is not None)
        names = trait_object.trait_names(**check)

        if names and self.version:
            version = LooseVersion(str(self.version))
            for name in names:
                min_ver = LooseVersion(str(trait_object.traits()[name].min_ver))
                if min_ver > version:
                    unavailable_traits.append(name)
                    if not isdefined(getattr(trait_object, name)):
                        continue
                    if raise_exception:
                        raise Exception(
                            "Trait %s (%s) (version %s < required %s)"
                            % (name, self.__class__.__name__, version, min_ver)
                        )

        # check maximum version
        check = dict(max_ver=lambda t: t is not None)
        names = trait_object.trait_names(**check)
        if names and self.version:
            version = LooseVersion(str(self.version))
            for name in names:
                max_ver = LooseVersion(str(trait_object.traits()[name].max_ver))
                if max_ver < version:
                    unavailable_traits.append(name)
                    if not isdefined(getattr(trait_object, name)):
                        continue
                    if raise_exception:
                        raise Exception(
                            "Trait %s (%s) (version %s > required %s)"
                            % (name, self.__class__.__name__, version, max_ver)
                        )
        return unavailable_traits

    def _run_interface(self, runtime):
        """ Core function that executes interface
        """
        raise NotImplementedError

    def run(self, cwd=None, ignore_exception=None, **inputs):
        """Execute this interface.

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

        # if ignore_exception is not provided, taking self.ignore_exception
        if ignore_exception is None:
            ignore_exception = self.ignore_exception

        # Tear-up: get current and prev directories
        syscwd = rgetcwd(error=False)  # Recover when wd does not exist
        if cwd is None:
            cwd = syscwd

        os.chdir(cwd)  # Change to the interface wd

        enable_rm = config.resource_monitor and self.resource_monitor
        self.inputs.trait_set(**inputs)
        self._check_mandatory_inputs()
        self._check_version_requirements(self.inputs)
        interface = self.__class__

        # initialize provenance tracking
        store_provenance = str2bool(
            config.get("execution", "write_provenance", "false")
        )
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
            version=self.version,
        )
        runtime_attrs = set(runtime.dictcopy())

        mon_sp = None
        if enable_rm:
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
            runtime = self._pre_run_hook(runtime)
            with RedirectStandardStreams(stdout, stderr=stderr):
                runtime = self._run_interface(runtime)
            runtime = self._post_run_hook(runtime)
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

            if not ignore_exception:
                raise
        finally:
            if runtime is None or runtime_attrs - set(runtime.dictcopy()):
                raise RuntimeError(
                    "{} interface failed to return valid "
                    "runtime object".format(interface.__class__.__name__)
                )

            # This needs to be done always
            runtime.endTime = dt.isoformat(dt.utcnow())
            timediff = parseutc(runtime.endTime) - parseutc(runtime.startTime)
            runtime.duration = (
                timediff.days * 86400 + timediff.seconds + timediff.microseconds / 1e6
            )
            results = InterfaceResult(
                interface, runtime, inputs=inputs, outputs=None, provenance=None
            )

            # Add provenance (if required)
            if store_provenance:
                # Provenance will only throw a warning if something went wrong
                results.provenance = write_provenance(results)

            # Make sure runtime profiler is shut down
            if enable_rm:
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

            results.outputs = self._find_outputs(runtime)
            os.chdir(syscwd)

        return results

    @property
    def version(self):
        if self._version is None:
            if str2bool(config.get("execution", "stop_on_unknown_version")):
                raise ValueError(
                    "Interface %s has no version information" % self.__class__.__name__
                )
        return self._version

    def load_inputs_from_json(self, json_file, overwrite=True):
        """
        A convenient way to load pre-set inputs from a JSON file.
        """

        with open(json_file) as fhandle:
            inputs_dict = json.load(fhandle)

        def_inputs = []
        if not overwrite:
            def_inputs = list(self.inputs.get_traitsfree().keys())

        new_inputs = list(set(list(inputs_dict.keys())) - set(def_inputs))
        for key in new_inputs:
            if hasattr(self.inputs, key):
                setattr(self.inputs, key, inputs_dict[key])

    def save_inputs_to_json(self, json_file):
        """
        A convenient way to save current inputs to a JSON file.
        """
        inputs = self.inputs.get_traitsfree()
        iflogger.debug("saving inputs %s", inputs)
        with open(json_file, "w") as fhandle:
            json.dump(inputs, fhandle, indent=4, ensure_ascii=False)

    def _pre_run_hook(self, runtime):
        """
        Perform any pre-_run_interface() processing

        Subclasses may override this function to modify ``runtime`` object or
        interface state

        MUST return runtime object
        """
        return runtime

    def _post_run_hook(self, runtime):
        """
        Perform any post-_run_interface() processing

        Subclasses may override this function to modify ``runtime`` object or
        interface state

        MUST return runtime object
        """
        return runtime

    def _find_outputs(self, runtime):
        """
        Automagically fill in output fields.

        Returns
        -------
        outputs : :obj:`traits.HasTraits`
            Collected outputs

        """
        outputs = self.output_spec()
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
