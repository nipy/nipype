# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The spm module provides basic functions for interfacing with SPM  tools.

In order to use the standalone MCR version of spm, you need to ensure that
the following commands are executed at the beginning of your script::

   from nipype.interfaces import spm
   matlab_cmd = '/path/to/run_spm8.sh /path/to/Compiler_Runtime/v713/ script'
   spm.SPMCommand.set_mlab_paths(matlab_cmd=matlab_cmd, use_mcr=True)

you can test by calling::

   spm.SPMCommand().version
"""
# Standard library imports
import os
from copy import deepcopy

# Third-party imports
from nibabel import load
import numpy as np

# Local imports
from ... import logging
from ...utils import spm_docs as sd
from ..base import (
    BaseInterface,
    traits,
    Tuple,
    isdefined,
    InputMultiPath,
    BaseInterfaceInputSpec,
    Directory,
    Undefined,
    ImageFile,
    PackageInfo,
)
from ..base.traits_extension import NoDefaultSpecified
from ..matlab import MatlabCommand
from ...external.due import BibTeX

__docformat__ = "restructuredtext"
logger = logging.getLogger("nipype.interface")


def func_is_3d(in_file):
    """Checks if input functional files are 3d."""

    if isinstance(in_file, list):
        return func_is_3d(in_file[0])
    else:
        img = load(in_file)
        shape = img.shape
        return len(shape) == 3 or (len(shape) == 4 and shape[3] == 1)


def get_first_3dfile(in_files):
    if not func_is_3d(in_files):
        return None
    if isinstance(in_files[0], list):
        return in_files[0]
    return in_files


def scans_for_fname(fname):
    """Reads a nifti file and converts it to a numpy array storing
    individual nifti volumes.

    Opens images so will fail if they are not found.

    """
    if isinstance(fname, list):
        scans = np.zeros((len(fname),), dtype=object)
        for sno, f in enumerate(fname):
            scans[sno] = "%s,1" % f
        return scans
    img = load(fname)
    if len(img.shape) == 3:
        return np.array(("%s,1" % fname,), dtype=object)
    else:
        n_scans = img.shape[3]
        scans = np.zeros((n_scans,), dtype=object)
        for sno in range(n_scans):
            scans[sno] = "%s,%d" % (fname, sno + 1)
        return scans


def scans_for_fnames(fnames, keep4d=False, separate_sessions=False):
    """Converts a list of files to a concatenated numpy array for each
    volume.

    keep4d : boolean
        keeps the entries of the numpy array as 4d files instead of
        extracting the individual volumes.
    separate_sessions: boolean
        if 4d nifti files are being used, then separate_sessions
        ensures a cell array per session is created in the structure.

    """
    flist = None
    if not isinstance(fnames[0], list):
        if func_is_3d(fnames[0]):
            fnames = [fnames]
    if separate_sessions or keep4d:
        flist = np.zeros((len(fnames),), dtype=object)
    for i, f in enumerate(fnames):
        if separate_sessions:
            if keep4d:
                if isinstance(f, list):
                    flist[i] = np.array(f, dtype=object)
                else:
                    flist[i] = np.array([f], dtype=object)
            else:
                flist[i] = scans_for_fname(f)
        else:
            if keep4d:
                flist[i] = f
            else:
                scans = scans_for_fname(f)
                if flist is None:
                    flist = scans
                else:
                    flist = np.concatenate((flist, scans))
    return flist


class Info(PackageInfo):
    """Handles SPM version information

    If you use `SPMCommand.set_mlab_paths` to set alternate entries for
    matlab_cmd, paths, and use_mcr, then you will need to use the same entries
    to any call in the Info class to maintain memoization. Otherwise, it will
    default to the parameters in the `getinfo` function below.
    """

    _path = None
    _name = None
    _command = None
    _paths = None
    _version = None

    @classmethod
    def path(klass, matlab_cmd=None, paths=None, use_mcr=None):
        klass.getinfo(matlab_cmd, paths, use_mcr)
        return klass._path

    @classmethod
    def version(klass, matlab_cmd=None, paths=None, use_mcr=None):
        klass.getinfo(matlab_cmd, paths, use_mcr)
        return klass._version

    @classmethod
    def name(klass, matlab_cmd=None, paths=None, use_mcr=None):
        klass.getinfo(matlab_cmd, paths, use_mcr)
        return klass._name

    @classmethod
    def getinfo(klass, matlab_cmd=None, paths=None, use_mcr=None):
        """
        Returns the path to the SPM directory in the Matlab path
        If path not found, returns None.

        Parameters
        ----------
        matlab_cmd: str
            Sets the default matlab command. If None, the value of the
            environment variable SPMMCRCMD will be used if set and use_mcr
            is True or the environment variable FORCE_SPMMCR is set.
            If one of FORCE_SPMMCR or SPMMCRCMD is not set, the existence
            of the environment variable MATLABCMD is checked and its value
            is used as the matlab command if possible.
            If none of the above was successful, the fallback value of
            'matlab -nodesktop -nosplash' will be used.
        paths : str
            Add paths to matlab session
        use_mcr : bool
            Whether to use the MATLAB Common Runtime. In this case, the
            matlab_cmd is expected to be a valid MCR call.

        Returns
        -------
        spm_path : string representing path to SPM directory

            returns None of path not found
        """

        use_mcr = use_mcr or "FORCE_SPMMCR" in os.environ
        matlab_cmd = matlab_cmd or (
            (use_mcr and os.getenv("SPMMCRCMD"))
            or os.getenv("MATLABCMD", "matlab -nodesktop -nosplash")
        )

        if (
            klass._name
            and klass._path
            and klass._version
            and klass._command == matlab_cmd
            and klass._paths == paths
        ):
            return {"name": klass._name, "path": klass._path, "release": klass._version}
        logger.debug("matlab command or path has changed. recomputing version.")
        mlab = MatlabCommand(matlab_cmd=matlab_cmd, resource_monitor=False)
        mlab.inputs.mfile = False
        if paths:
            mlab.inputs.paths = paths
        if use_mcr:
            mlab.inputs.nodesktop = Undefined
            mlab.inputs.nosplash = Undefined
            mlab.inputs.single_comp_thread = Undefined
            mlab.inputs.mfile = True
            mlab.inputs.uses_mcr = True
        mlab.inputs.script = """
if isempty(which('spm')),
throw(MException('SPMCheck:NotFound','SPM not in matlab path'));
end;
spm_path = spm('dir');
[name, version] = spm('ver');
fprintf(1, 'NIPYPE path:%s|name:%s|release:%s', spm_path, name, version);
exit;
        """
        try:
            out = mlab.run()
        except (OSError, RuntimeError) as e:
            # if no Matlab at all -- exception could be raised
            # No Matlab -- no spm
            logger.debug("%s", e)
            klass._version = None
            klass._path = None
            klass._name = None
            klass._command = matlab_cmd
            klass._paths = paths
            return None

        out = sd._strip_header(out.runtime.stdout)
        out_dict = {}
        for part in out.split("|"):
            key, val = part.split(":")
            out_dict[key] = val

        klass._version = out_dict["release"]
        klass._path = out_dict["path"]
        klass._name = out_dict["name"]
        klass._command = matlab_cmd
        klass._paths = paths
        return out_dict


def no_spm():
    """Checks if SPM is NOT installed
    used with pytest.mark.skipif decorator to skip tests
    that will fail if spm is not installed"""

    return "NIPYPE_NO_MATLAB" in os.environ or Info.version() is None


class SPMCommandInputSpec(BaseInterfaceInputSpec):
    matlab_cmd = traits.Str(desc="matlab command to use")
    paths = InputMultiPath(Directory(), desc="Paths to add to matlabpath")
    mfile = traits.Bool(True, desc="Run m-code using m-file", usedefault=True)
    use_mcr = traits.Bool(desc="Run m-code using SPM MCR")
    use_v8struct = traits.Bool(
        True,
        min_ver="8",
        usedefault=True,
        desc=("Generate SPM8 and higher compatible jobs"),
    )


class SPMCommand(BaseInterface):
    """Extends `BaseInterface` class to implement SPM specific interfaces.

    WARNING: Pseudo prototype class, meant to be subclassed
    """

    input_spec = SPMCommandInputSpec
    _additional_metadata = ["field"]

    _jobtype = "basetype"
    _jobname = "basename"

    _matlab_cmd = None
    _paths = None
    _use_mcr = None

    _references = [
        {
            "entry": BibTeX(
                "@book{FrackowiakFristonFrithDolanMazziotta1997,"
                "author={R.S.J. Frackowiak, K.J. Friston, C.D. Frith, R.J. Dolan, and J.C. Mazziotta},"
                "title={Human Brain Function},"
                "publisher={Academic Press USA},"
                "year={1997},"
                "}"
            ),
            "description": "The fundamental text on Statistical Parametric Mapping (SPM)",
            # 'path': "nipype.interfaces.spm",
            "tags": ["implementation"],
        }
    ]

    def __init__(self, **inputs):
        super().__init__(**inputs)
        self.inputs.on_trait_change(
            self._matlab_cmd_update, ["matlab_cmd", "mfile", "paths", "use_mcr"]
        )
        self._find_mlab_cmd_defaults()
        self._check_mlab_inputs()
        self._matlab_cmd_update()

    @classmethod
    def set_mlab_paths(cls, matlab_cmd=None, paths=None, use_mcr=None):
        cls._matlab_cmd = matlab_cmd
        cls._paths = paths
        cls._use_mcr = use_mcr
        info_dict = Info.getinfo(matlab_cmd=matlab_cmd, paths=paths, use_mcr=use_mcr)

    def _find_mlab_cmd_defaults(self):
        # check if the user has set environment variables to enforce
        # the standalone (MCR) version of SPM
        if self._use_mcr or "FORCE_SPMMCR" in os.environ:
            self._use_mcr = True
            if self._matlab_cmd is None:
                try:
                    self._matlab_cmd = os.environ["SPMMCRCMD"]
                except KeyError:
                    pass

    def _matlab_cmd_update(self):
        # MatlabCommand has to be created here,
        # because matlab_cmd is not a proper input
        # and can be set only during init
        self.mlab = MatlabCommand(
            matlab_cmd=self.inputs.matlab_cmd,
            mfile=self.inputs.mfile,
            paths=self.inputs.paths,
            resource_monitor=False,
        )
        self.mlab.inputs.script_file = (
            "pyscript_%s.m" % self.__class__.__name__.split(".")[-1].lower()
        )
        if isdefined(self.inputs.use_mcr) and self.inputs.use_mcr:
            self.mlab.inputs.nodesktop = Undefined
            self.mlab.inputs.nosplash = Undefined
            self.mlab.inputs.single_comp_thread = Undefined
            self.mlab.inputs.uses_mcr = True
            self.mlab.inputs.mfile = True

    @property
    def version(self):
        info_dict = Info.getinfo(
            matlab_cmd=self.inputs.matlab_cmd,
            paths=self.inputs.paths,
            use_mcr=self.inputs.use_mcr,
        )
        if info_dict:
            return "{}.{}".format(
                info_dict["name"].split("SPM")[-1], info_dict["release"]
            )

    @property
    def jobtype(self):
        return self._jobtype

    @property
    def jobname(self):
        return self._jobname

    def _check_mlab_inputs(self):
        if not isdefined(self.inputs.matlab_cmd) and self._matlab_cmd:
            self.inputs.matlab_cmd = self._matlab_cmd
        if not isdefined(self.inputs.paths) and self._paths:
            self.inputs.paths = self._paths
        if not isdefined(self.inputs.use_mcr) and self._use_mcr:
            self.inputs.use_mcr = self._use_mcr

    def _run_interface(self, runtime):
        """Executes the SPM function using MATLAB."""
        self.mlab.inputs.script = self._make_matlab_command(
            deepcopy(self._parse_inputs())
        )
        results = self.mlab.run()
        runtime.returncode = results.runtime.returncode
        if self.mlab.inputs.uses_mcr:
            if "Skipped" in results.runtime.stdout:
                self.raise_exception(runtime)
        runtime.stdout = results.runtime.stdout
        runtime.stderr = results.runtime.stderr
        runtime.merged = results.runtime.merged
        return runtime

    def _list_outputs(self):
        """Determine the expected outputs based on inputs."""

        raise NotImplementedError

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for SPM."""
        if spec.is_trait_type(traits.Bool):
            return int(val)
        elif spec.is_trait_type(traits.BaseTuple):
            return list(val)
        else:
            return val

    def _parse_inputs(self, skip=()):
        spmdict = {}
        metadata = dict(field=lambda t: t is not None)
        for name, spec in list(self.inputs.traits(**metadata).items()):
            if skip and name in skip:
                continue
            value = getattr(self.inputs, name)
            if not isdefined(value):
                continue
            field = spec.field
            if "." in field:
                fields = field.split(".")
                dictref = spmdict
                for f in fields[:-1]:
                    if f not in list(dictref.keys()):
                        dictref[f] = {}
                    dictref = dictref[f]
                dictref[fields[-1]] = self._format_arg(name, spec, value)
            else:
                spmdict[field] = self._format_arg(name, spec, value)
        return [spmdict]

    def _reformat_dict_for_savemat(self, contents):
        """Encloses a dict representation within hierarchical lists.

        In order to create an appropriate SPM job structure, a Python
        dict storing the job needs to be modified so that each dict
        embedded in dict needs to be enclosed as a list element.

        Examples
        --------
        >>> a = SPMCommand()._reformat_dict_for_savemat(dict(a=1,
        ...                                                  b=dict(c=2, d=3)))
        >>> a == [{'a': 1, 'b': [{'c': 2, 'd': 3}]}]
        True

        """
        newdict = {}
        try:
            for key, value in list(contents.items()):
                if isinstance(value, dict):
                    if value:
                        newdict[key] = self._reformat_dict_for_savemat(value)
                    # if value is None, skip
                else:
                    newdict[key] = value

            return [newdict]
        except TypeError:
            print("Requires dict input")

    def _generate_job(self, prefix="", contents=None):
        """Recursive function to generate spm job specification as a string

        Parameters
        ----------
        prefix : string
            A string that needs to get
        contents : dict
            A non-tuple Python structure containing spm job
            information gets converted to an appropriate sequence of
            matlab commands.

        """
        jobstring = ""
        if contents is None:
            return jobstring
        if isinstance(contents, list):
            for i, value in enumerate(contents):
                if prefix.endswith(")"):
                    newprefix = "%s,%d)" % (prefix[:-1], i + 1)
                else:
                    newprefix = "%s(%d)" % (prefix, i + 1)
                jobstring += self._generate_job(newprefix, value)
            return jobstring
        if isinstance(contents, dict):
            for key, value in list(contents.items()):
                newprefix = f"{prefix}.{key}"
                jobstring += self._generate_job(newprefix, value)
            return jobstring
        if isinstance(contents, np.ndarray):
            if contents.dtype == np.dtype(object):
                if prefix:
                    jobstring += "%s = {...\n" % (prefix)
                else:
                    jobstring += "{...\n"
                for i, val in enumerate(contents):
                    if isinstance(val, np.ndarray):
                        jobstring += self._generate_job(prefix=None, contents=val)
                    elif isinstance(val, list):
                        items_format = []
                        for el in val:
                            items_format += [
                                "{}" if not isinstance(el, (str, bytes)) else "'{}'"
                            ]
                        val_format = ", ".join(items_format).format
                        jobstring += f"[{val_format(*val)}];...\n"
                    elif isinstance(val, (str, bytes)):
                        jobstring += f"'{val}';...\n"
                    else:
                        jobstring += "%s;...\n" % str(val)
                jobstring += "};\n"
            else:
                for i, val in enumerate(contents):
                    for field in val.dtype.fields:
                        if prefix:
                            newprefix = "%s(%d).%s" % (prefix, i + 1, field)
                        else:
                            newprefix = "(%d).%s" % (i + 1, field)
                        jobstring += self._generate_job(newprefix, val[field])
            return jobstring
        if isinstance(contents, (str, bytes)):
            jobstring += f"{prefix} = '{contents}';\n"
            return jobstring
        jobstring += f"{prefix} = {contents};\n"
        return jobstring

    def _make_matlab_command(self, contents, postscript=None):
        """Generates a mfile to build job structure
        Parameters
        ----------

        contents : list
            a list of dicts generated by _parse_inputs
            in each subclass

        cwd : string
            default os.getcwd()

        Returns
        -------
        mscript : string
            contents of a script called by matlab

        """
        cwd = os.getcwd()
        mscript = """
        %% Generated by nipype.interfaces.spm
        if isempty(which('spm')),
             throw(MException('SPMCheck:NotFound', 'SPM not in matlab path'));
        end
        [name, version] = spm('ver');
        fprintf('SPM version: %s Release: %s\\n',name, version);
        fprintf('SPM path: %s\\n', which('spm'));
        spm('Defaults','fMRI');

        if strcmp(name, 'SPM8') || strcmp(name(1:5), 'SPM12'),
           spm_jobman('initcfg');
           spm_get_defaults('cmdline', 1);
        end\n
        """
        if self.mlab.inputs.mfile:
            if isdefined(self.inputs.use_v8struct) and self.inputs.use_v8struct:
                mscript += self._generate_job(
                    f"jobs{{1}}.spm.{self.jobtype}.{self.jobname}", contents[0]
                )
            else:
                if self.jobname in [
                    "st",
                    "smooth",
                    "preproc",
                    "preproc8",
                    "fmri_spec",
                    "fmri_est",
                    "factorial_design",
                    "defs",
                ]:
                    # parentheses
                    mscript += self._generate_job(
                        f"jobs{{1}}.{self.jobtype}{{1}}.{self.jobname}(1)",
                        contents[0],
                    )
                else:
                    # curly brackets
                    mscript += self._generate_job(
                        f"jobs{{1}}.{self.jobtype}{{1}}.{self.jobname}{{1}}",
                        contents[0],
                    )
        else:
            from scipy.io import savemat

            jobdef = {
                "jobs": [
                    {
                        self.jobtype: [
                            {self.jobname: self.reformat_dict_for_savemat(contents[0])}
                        ]
                    }
                ]
            }
            savemat(os.path.join(cwd, "pyjobs_%s.mat" % self.jobname), jobdef)
            mscript += "load pyjobs_%s;\n\n" % self.jobname
        mscript += """
        spm_jobman(\'run\', jobs);\n
        """
        if self.inputs.use_mcr:
            mscript += """
        if strcmp(name, 'SPM8') || strcmp(name(1:5), 'SPM12'),
            close(\'all\', \'force\');
        end;
            """
        if postscript is not None:
            mscript += postscript
        return mscript


class ImageFileSPM(ImageFile):
    """Defines a trait whose value must be a NIfTI file."""

    def __init__(
        self, value=NoDefaultSpecified, exists=False, resolve=False, **metadata
    ):
        """Create an ImageFileSPM trait."""
        super().__init__(
            value=value,
            exists=exists,
            types=["nifti1", "nifti2"],
            allow_compressed=False,
            resolve=resolve,
            **metadata,
        )
