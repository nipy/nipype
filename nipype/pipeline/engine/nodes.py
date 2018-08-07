# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Node` class provides core functionality for batch processing.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range, str, bytes, open

from collections import OrderedDict

import os
import os.path as op
import shutil
import socket
from copy import deepcopy
from glob import glob
from logging import INFO

from tempfile import mkdtemp
from future import standard_library

from ... import config, logging
from ...utils.misc import flatten, unflatten, str2bool, dict_diff
from ...utils.filemanip import (md5, FileNotFoundError, ensure_list,
                                simplify_list, copyfiles, fnames_presuffix,
                                loadpkl, split_filename, load_json, makedirs,
                                emptydirs, savepkl, to_str, indirectory)

from ...interfaces.base import (traits, InputMultiPath, CommandLine, Undefined,
                                DynamicTraitedSpec, Bunch, InterfaceResult,
                                Interface, isdefined)
from .utils import (
    _parameterization_dir, save_hashfile as _save_hashfile, load_resultfile as
    _load_resultfile, save_resultfile as _save_resultfile, nodelist_runner as
    _node_runner, strip_temp as _strip_temp, write_report,
    clean_working_directory, merge_dict, evaluate_connect_function)
from .base import EngineBase

standard_library.install_aliases()

logger = logging.getLogger('nipype.workflow')


class Node(EngineBase):
    """
    Wraps interface objects for use in pipeline

    A Node creates a sandbox-like directory for executing the underlying
    interface. It will copy or link inputs into this directory to ensure that
    input data are not overwritten. A hash of the input state is used to
    determine if the Node inputs have changed and whether the node needs to be
    re-executed.

    Examples
    --------

    >>> from nipype import Node
    >>> from nipype.interfaces import spm
    >>> realign = Node(spm.Realign(), 'realign')
    >>> realign.inputs.in_files = 'functional.nii'
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """

    def __init__(self,
                 interface,
                 name,
                 iterables=None,
                 itersource=None,
                 synchronize=False,
                 overwrite=None,
                 needed_outputs=None,
                 run_without_submitting=False,
                 n_procs=None,
                 mem_gb=0.20,
                 **kwargs):
        """
        Parameters
        ----------

        interface : interface object
            node specific interface (fsl.Bet(), spm.Coregister())

        name : alphanumeric string
            node specific name

        iterables : generator
            Input field and list to iterate using the pipeline engine
            for example to iterate over different frac values in fsl.Bet()
            for a single field the input can be a tuple, otherwise a list
            of tuples ::

                node.iterables = ('frac',[0.5,0.6,0.7])
                node.iterables = [('fwhm',[2,4]),('fieldx',[0.5,0.6,0.7])]

            If this node has an itersource, then the iterables values
            is a dictionary which maps an iterable source field value
            to the target iterables field values, e.g.: ::

                inputspec.iterables = ('images',['img1.nii', 'img2.nii']])
                node.itersource = ('inputspec', ['frac'])
                node.iterables = ('frac', {'img1.nii': [0.5, 0.6],
                                           'img2.nii': [0.6, 0.7]})

            If this node's synchronize flag is set, then an alternate
            form of the iterables is a [fields, values] list, where
            fields is the list of iterated fields and values is the
            list of value tuples for the given fields, e.g.: ::

                node.synchronize = True
                node.iterables = [('frac', 'threshold'),
                                  [(0.5, True),
                                   (0.6, False)]]

        itersource: tuple
            The (name, fields) iterables source which specifies the name
            of the predecessor iterable node and the input fields to use
            from that source node. The output field values comprise the
            key to the iterables parameter value mapping dictionary.

        synchronize: boolean
            Flag indicating whether iterables are synchronized.
            If the iterables are synchronized, then this iterable
            node is expanded once per iteration over all of the
            iterables values.
            Otherwise, this iterable node is expanded once per
            each permutation of the iterables values.

        overwrite : Boolean
            Whether to overwrite contents of output directory if it already
            exists. If directory exists and hash matches it
            assumes that process has been executed

        needed_outputs : list of output_names
            Force the node to keep only specific outputs. By default all
            outputs are kept. Setting this attribute will delete any output
            files and directories from the node's working directory that are
            not part of the `needed_outputs`.

        run_without_submitting : boolean
            Run the node without submitting to a job engine or to a
            multiprocessing pool

        """
        # Make sure an interface is set, and that it is an Interface
        if interface is None:
            raise IOError('Interface must be provided')
        if not isinstance(interface, Interface):
            raise IOError('interface must be an instance of an Interface')

        super(Node, self).__init__(name, kwargs.get('base_dir'))

        self._interface = interface
        self._hierarchy = None
        self._got_inputs = False
        self._originputs = None
        self._output_dir = None

        self.iterables = iterables
        self.synchronize = synchronize
        self.itersource = itersource
        self.overwrite = overwrite
        self.parameterization = []
        self.input_source = {}
        self.plugin_args = {}

        self.run_without_submitting = run_without_submitting
        self._mem_gb = mem_gb
        self._n_procs = n_procs

        # Downstream n_procs
        if hasattr(self._interface.inputs,
                   'num_threads') and self._n_procs is not None:
            self._interface.inputs.num_threads = self._n_procs

        # Initialize needed_outputs and hashes
        self._hashvalue = None
        self._hashed_inputs = None
        self._needed_outputs = []
        self.needed_outputs = needed_outputs
        self.config = None

    @property
    def interface(self):
        """Return the underlying interface object"""
        return self._interface

    @property
    def result(self):
        """Get result from result file (do not hold it in memory)"""
        return _load_resultfile(self.output_dir(), self.name)[0]

    @property
    def inputs(self):
        """Return the inputs of the underlying interface"""
        return self._interface.inputs

    @property
    def outputs(self):
        """Return the output fields of the underlying interface"""
        return self._interface._outputs()

    @property
    def needed_outputs(self):
        return self._needed_outputs

    @needed_outputs.setter
    def needed_outputs(self, new_outputs):
        """Needed outputs changes the hash, refresh if changed"""
        new_outputs = sorted(list(set(new_outputs or [])))
        if new_outputs != self._needed_outputs:
            # Reset hash
            self._hashvalue = None
            self._hashed_inputs = None
            self._needed_outputs = new_outputs

    @property
    def mem_gb(self):
        """Get estimated memory (GB)"""
        if hasattr(self._interface, 'estimated_memory_gb'):
            self._mem_gb = self._interface.estimated_memory_gb
            logger.warning(
                'Setting "estimated_memory_gb" on Interfaces has been '
                'deprecated as of nipype 1.0, please use Node.mem_gb.')

        return self._mem_gb

    @property
    def n_procs(self):
        """Get the estimated number of processes/threads"""
        if self._n_procs is not None:
            return self._n_procs
        if hasattr(self._interface.inputs, 'num_threads') and isdefined(
                self._interface.inputs.num_threads):
            return self._interface.inputs.num_threads
        return 1

    @n_procs.setter
    def n_procs(self, value):
        """Set an estimated number of processes/threads"""
        self._n_procs = value

        # Overwrite interface's dynamic input of num_threads
        if hasattr(self._interface.inputs, 'num_threads'):
            self._interface.inputs.num_threads = self._n_procs

    def output_dir(self):
        """Return the location of the output directory for the node"""
        # Output dir is cached
        if self._output_dir:
            return self._output_dir

        # Calculate & cache otherwise
        if self.base_dir is None:
            self.base_dir = mkdtemp()
        outputdir = self.base_dir
        if self._hierarchy:
            outputdir = op.join(outputdir, *self._hierarchy.split('.'))
        if self.parameterization:
            params_str = ['{}'.format(p) for p in self.parameterization]
            if not str2bool(self.config['execution']['parameterize_dirs']):
                params_str = [_parameterization_dir(p) for p in params_str]
            outputdir = op.join(outputdir, *params_str)

        self._output_dir = op.realpath(op.join(outputdir, self.name))
        return self._output_dir

    def set_input(self, parameter, val):
        """Set interface input value"""
        logger.debug('[Node] %s - setting input %s = %s', self.name, parameter,
                     to_str(val))
        setattr(self.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        """Retrieve a particular output of the node"""
        return getattr(self.result.outputs, parameter, None)

    def help(self):
        """Print interface help"""
        self._interface.help()

    def is_cached(self, rm_outdated=False):
        """
        Check if the interface has been run previously, and whether
        cached results are up-to-date.
        """
        outdir = self.output_dir()

        # Update hash
        hashed_inputs, hashvalue = self._get_hashval()

        # The output folder does not exist: not cached
        if not op.exists(outdir):
            logger.debug('[Node] Directory not found "%s".', outdir)
            return False, False

        hashfile = op.join(outdir, '_0x%s.json' % hashvalue)
        cached = op.exists(hashfile)

        # Check if updated
        globhashes = glob(op.join(outdir, '_0x*.json'))
        unfinished = [
            path for path in globhashes
            if path.endswith('_unfinished.json')
        ]
        hashfiles = list(set(globhashes) - set(unfinished))
        logger.debug('[Node] Hashes: %s, %s, %s, %s',
                     hashed_inputs, hashvalue, hashfile, hashfiles)

        # No previous hashfiles found, we're all set.
        if cached and len(hashfiles) == 1:
            assert(hashfile == hashfiles[0])
            logger.debug('[Node] Up-to-date cache found for "%s".', self.fullname)
            return True, True  # Cached and updated

        if len(hashfiles) > 1:
            if cached:
                hashfiles.remove(hashfile)  # Do not clean up the node, if cached
            logger.warning('[Node] Found %d previous hashfiles indicating that the working '
                           'directory of node "%s" is stale, deleting old hashfiles.',
                           len(hashfiles), self.fullname)
            for rmfile in hashfiles:
                os.remove(rmfile)

            hashfiles = [hashfile] if cached else []

        if not hashfiles:
            logger.debug('[Node] No hashfiles found in "%s".', outdir)
            assert(not cached)
            return False, False

        # At this point only one hashfile is in the folder
        # and we directly check whether it is updated
        updated = hashfile == hashfiles[0]
        if not updated:  # Report differences depending on log verbosity
            cached = True
            logger.info('[Node] Outdated cache found for "%s".', self.fullname)
            # If logging is more verbose than INFO (20), print diff between hashes
            loglevel = logger.getEffectiveLevel()
            if loglevel < INFO:  # Lazy logging: only < INFO
                exp_hash_file_base = split_filename(hashfiles[0])[1]
                exp_hash = exp_hash_file_base[len('_0x'):]
                logger.log(loglevel, "[Node] Old/new hashes = %s/%s",
                           exp_hash, hashvalue)
                try:
                    prev_inputs = load_json(hashfiles[0])
                except Exception:
                    pass
                else:
                    logger.log(loglevel,
                               dict_diff(prev_inputs, hashed_inputs, 10))

            if rm_outdated:
                os.remove(hashfiles[0])

        assert(cached)  # At this point, node is cached (may not be up-to-date)
        return cached, updated

    def hash_exists(self, updatehash=False):
        """
        Decorate the new `is_cached` method with hash updating
        to maintain backwards compatibility.
        """

        # Get a dictionary with hashed filenames and a hashvalue
        # of the dictionary itself.
        cached, updated = self.is_cached(rm_outdated=True)

        outdir = self.output_dir()
        hashfile = op.join(outdir, '_0x%s.json' % self._hashvalue)

        if updated:
            return True, self._hashvalue, hashfile, self._hashed_inputs

        # Update only possible if it exists
        if cached and updatehash:
            logger.debug("[Node] Updating hash: %s", self._hashvalue)
            _save_hashfile(hashfile, self._hashed_inputs)

        return cached, self._hashvalue, hashfile, self._hashed_inputs

    def run(self, updatehash=False):
        """Execute the node in its directory.

        Parameters
        ----------

        updatehash: boolean
            When the hash stored in the output directory as a result of a previous run
            does not match that calculated for this execution, updatehash=True only
            updates the hash without re-running.
        """

        if self.config is None:
            self.config = {}
        self.config = merge_dict(deepcopy(config._sections), self.config)

        outdir = self.output_dir()
        force_run = self.overwrite or (self.overwrite is None and
                                       self._interface.always_run)

        # Check hash, check whether run should be enforced
        logger.info('[Node] Setting-up "%s" in "%s".', self.fullname, outdir)
        cached, updated = self.is_cached()

        # If the node is cached, check on pklz files and finish
        if not force_run and (updated or (not updated and updatehash)):
            logger.debug("Only updating node hashes or skipping execution")
            inputs_file = op.join(outdir, '_inputs.pklz')
            if not op.exists(inputs_file):
                logger.debug('Creating inputs file %s', inputs_file)
                savepkl(inputs_file, self.inputs.get_traitsfree())

            node_file = op.join(outdir, '_node.pklz')
            if not op.exists(node_file):
                logger.debug('Creating node file %s', node_file)
                savepkl(node_file, self)

            result = self._run_interface(execute=False,
                                         updatehash=updatehash and not updated)
            logger.info('[Node] "%s" found cached%s.', self.fullname,
                        ' (and hash updated)' * (updatehash and not updated))
            return result

        if cached and updated and not isinstance(self, MapNode):
            logger.debug('[Node] Rerunning cached, up-to-date node "%s"', self.fullname)
            if not force_run and str2bool(
                    self.config['execution']['stop_on_first_rerun']):
                raise Exception(
                    'Cannot rerun when "stop_on_first_rerun" is set to True')

        # Remove any hashfile that exists at this point (re)running.
        if cached:
            for outdatedhash in glob(op.join(self.output_dir(), '_0x*.json')):
                os.remove(outdatedhash)


        # Hashfile while running
        hashfile_unfinished = op.join(
            outdir, '_0x%s_unfinished.json' % self._hashvalue)

        # Delete directory contents if this is not a MapNode or can't resume
        can_resume = not (self._interface.can_resume and op.isfile(hashfile_unfinished))
        if can_resume and not isinstance(self, MapNode):
            emptydirs(outdir, noexist_ok=True)
        else:
            logger.debug('[%sNode] Resume - hashfile=%s',
                         'Map' * int(isinstance(self, MapNode)),
                         hashfile_unfinished)

        if isinstance(self, MapNode):
            # remove old json files
            for filename in glob(op.join(outdir, '_0x*.json')):
                os.remove(filename)

        # Make sure outdir is created
        makedirs(outdir, exist_ok=True)

        # Store runtime-hashfile, pre-execution report, the node and the inputs set.
        _save_hashfile(hashfile_unfinished, self._hashed_inputs)
        write_report(
            self, report_type='preexec', is_mapnode=isinstance(self, MapNode))
        savepkl(op.join(outdir, '_node.pklz'), self)
        savepkl(op.join(outdir, '_inputs.pklz'), self.inputs.get_traitsfree())

        try:
            result = self._run_interface(execute=True)
        except Exception:
            logger.warning('[Node] Error on "%s" (%s)', self.fullname, outdir)
            # Tear-up after error
            os.remove(hashfile_unfinished)
            raise

        # Tear-up after success
        shutil.move(hashfile_unfinished,
                    hashfile_unfinished.replace('_unfinished', ''))
        write_report(
            self, report_type='postexec', is_mapnode=isinstance(self, MapNode))
        logger.info('[Node] Finished "%s".', self.fullname)
        return result

    def _get_hashval(self):
        """Return a hash of the input state"""
        self._get_inputs()
        if self._hashvalue is None and self._hashed_inputs is None:
            self._hashed_inputs, self._hashvalue = self.inputs.get_hashval(
                hash_method=self.config['execution']['hash_method'])
            rm_extra = self.config['execution']['remove_unnecessary_outputs']
            if str2bool(rm_extra) and self.needed_outputs:
                hashobject = md5()
                hashobject.update(self._hashvalue.encode())
                hashobject.update(str(self.needed_outputs).encode())
                self._hashvalue = hashobject.hexdigest()
                self._hashed_inputs.append(('needed_outputs', self.needed_outputs))
        return self._hashed_inputs, self._hashvalue

    def _get_inputs(self):
        """Retrieve inputs from pointers to results file

        This mechanism can be easily extended/replaced to retrieve data from
        other data sources (e.g., XNAT, HTTP, etc.,.)
        """
        if self._got_inputs:
            return

        logger.debug('Setting node inputs')
        for key, info in list(self.input_source.items()):
            logger.debug('input: %s', key)
            results_file = info[0]
            logger.debug('results file: %s', results_file)
            results = loadpkl(results_file)
            output_value = Undefined
            if isinstance(info[1], tuple):
                output_name = info[1][0]
                value = getattr(results.outputs, output_name)
                if isdefined(value):
                    output_value = evaluate_connect_function(
                        info[1][1], info[1][2], value)
            else:
                output_name = info[1]
                try:
                    output_value = results.outputs.trait_get()[output_name]
                except AttributeError:
                    output_value = results.outputs.dictcopy()[output_name]
            logger.debug('output: %s', output_name)
            try:
                self.set_input(key, deepcopy(output_value))
            except traits.TraitError as e:
                msg = [
                    'Error setting node input:',
                    'Node: %s' % self.name,
                    'input: %s' % key,
                    'results_file: %s' % results_file,
                    'value: %s' % str(output_value)
                ]
                e.args = (e.args[0] + "\n" + '\n'.join(msg), )
                raise

        # Successfully set inputs
        self._got_inputs = True

    def _update_hash(self):
        for outdatedhash in glob(op.join(self.output_dir(), '_0x*.json')):
            os.remove(outdatedhash)
        _save_hashfile(self._hashvalue, self._hashed_inputs)

    def _run_interface(self, execute=True, updatehash=False):
        if updatehash:
            self._update_hash()
            return self._load_results()
        return self._run_command(execute)

    def _load_results(self):
        cwd = self.output_dir()
        result, aggregate, attribute_error = _load_resultfile(cwd, self.name)
        # try aggregating first
        if aggregate:
            logger.debug('aggregating results')
            if attribute_error:
                old_inputs = loadpkl(op.join(cwd, '_inputs.pklz'))
                self.inputs.trait_set(**old_inputs)
            if not isinstance(self, MapNode):
                self._copyfiles_to_wd(linksonly=True)
                aggouts = self._interface.aggregate_outputs(
                    needed_outputs=self.needed_outputs)
                runtime = Bunch(
                    cwd=cwd,
                    returncode=0,
                    environ=dict(os.environ),
                    hostname=socket.gethostname())
                result = InterfaceResult(
                    interface=self._interface.__class__,
                    runtime=runtime,
                    inputs=self._interface.inputs.get_traitsfree(),
                    outputs=aggouts)
                _save_resultfile(result, cwd, self.name)
            else:
                logger.debug('aggregating mapnode results')
                result = self._run_interface()
        return result

    def _run_command(self, execute, copyfiles=True):
        if not execute:
            try:
                result = self._load_results()
            except (FileNotFoundError, AttributeError):
                # if aggregation does not work, rerun the node
                logger.info("[Node] Some of the outputs were not found: "
                            "rerunning node.")
                copyfiles = False  # OE: this was like this before,
                execute = True  # I'll keep them for safety
            else:
                logger.info('[Node] Cached "%s" - collecting precomputed outputs',
                            self.fullname)
                return result

        outdir = self.output_dir()
        # Run command: either execute is true or load_results failed.
        result = InterfaceResult(
            interface=self._interface.__class__,
            runtime=Bunch(
                cwd=outdir,
                returncode=1,
                environ=dict(os.environ),
                hostname=socket.gethostname()
            ),
            inputs=self._interface.inputs.get_traitsfree())

        if copyfiles:
            self._originputs = deepcopy(self._interface.inputs)
            self._copyfiles_to_wd(execute=execute)

        message = '[Node] Running "{}" ("{}.{}")'.format(
            self.name, self._interface.__module__,
            self._interface.__class__.__name__)
        if issubclass(self._interface.__class__, CommandLine):
            try:
                with indirectory(outdir):
                    cmd = self._interface.cmdline
            except Exception as msg:
                result.runtime.stderr = '{}\n\n{}'.format(
                    getattr(result.runtime, 'stderr', ''), msg)
                _save_resultfile(result, outdir, self.name)
                raise
            cmdfile = op.join(outdir, 'command.txt')
            with open(cmdfile, 'wt') as fd:
                print(cmd + "\n", file=fd)
            message += ', a CommandLine Interface with command:\n{}'.format(cmd)
        logger.info(message)
        try:
            result = self._interface.run(cwd=outdir)
        except Exception as msg:
            result.runtime.stderr = '%s\n\n%s'.format(
                getattr(result.runtime, 'stderr', ''), msg)
            _save_resultfile(result, outdir, self.name)
            raise

        dirs2keep = None
        if isinstance(self, MapNode):
            dirs2keep = [op.join(outdir, 'mapflow')]

        result.outputs = clean_working_directory(
            result.outputs,
            outdir,
            self._interface.inputs,
            self.needed_outputs,
            self.config,
            dirs2keep=dirs2keep)
        _save_resultfile(result, outdir, self.name)

        return result

    def _copyfiles_to_wd(self, execute=True, linksonly=False):
        """copy files over and change the inputs"""
        if not hasattr(self._interface, '_get_filecopy_info'):
            # Nothing to be done
            return

        logger.debug('copying files to wd [execute=%s, linksonly=%s]', execute,
                     linksonly)

        outdir = self.output_dir()
        if execute and linksonly:
            olddir = outdir
            outdir = op.join(outdir, '_tempinput')
            makedirs(outdir, exist_ok=True)

        for info in self._interface._get_filecopy_info():
            files = self.inputs.trait_get().get(info['key'])
            if not isdefined(files) or not files:
                continue

            infiles = ensure_list(files)
            if execute:
                if linksonly:
                    if not info['copy']:
                        newfiles = copyfiles(
                            infiles, [outdir],
                            copy=info['copy'],
                            create_new=True)
                    else:
                        newfiles = fnames_presuffix(infiles, newpath=outdir)
                    newfiles = _strip_temp(newfiles,
                                           op.abspath(olddir).split(
                                               op.sep)[-1])
                else:
                    newfiles = copyfiles(
                        infiles, [outdir], copy=info['copy'], create_new=True)
            else:
                newfiles = fnames_presuffix(infiles, newpath=outdir)
            if not isinstance(files, list):
                newfiles = simplify_list(newfiles)
            setattr(self.inputs, info['key'], newfiles)
        if execute and linksonly:
            emptydirs(outdir, noexist_ok=True)

    def update(self, **opts):
        """Update inputs"""
        self.inputs.update(**opts)


class JoinNode(Node):
    """Wraps interface objects that join inputs into a list.

    Examples
    --------

    >>> import nipype.pipeline.engine as pe
    >>> from nipype import Node, JoinNode, Workflow
    >>> from nipype.interfaces.utility import IdentityInterface
    >>> from nipype.interfaces import (ants, dcm2nii, fsl)
    >>> wf = Workflow(name='preprocess')
    >>> inputspec = Node(IdentityInterface(fields=['image']),
    ...                     name='inputspec')
    >>> inputspec.iterables = [('image',
    ...                        ['img1.nii', 'img2.nii', 'img3.nii'])]
    >>> img2flt = Node(fsl.ImageMaths(out_data_type='float'),
    ...                   name='img2flt')
    >>> wf.connect(inputspec, 'image', img2flt, 'in_file')
    >>> average = JoinNode(ants.AverageImages(), joinsource='inputspec',
    ...                       joinfield='images', name='average')
    >>> wf.connect(img2flt, 'out_file', average, 'images')
    >>> realign = Node(fsl.FLIRT(), name='realign')
    >>> wf.connect(img2flt, 'out_file', realign, 'in_file')
    >>> wf.connect(average, 'output_average_image', realign, 'reference')
    >>> strip = Node(fsl.BET(), name='strip')
    >>> wf.connect(realign, 'out_file', strip, 'in_file')

    """

    def __init__(self,
                 interface,
                 name,
                 joinsource,
                 joinfield=None,
                 unique=False,
                 **kwargs):
        """

        Parameters
        ----------
        interface : interface object
            node specific interface (fsl.Bet(), spm.Coregister())
        name : alphanumeric string
            node specific name
        joinsource : node name
            name of the join predecessor iterable node
        joinfield : string or list of strings
            name(s) of list input fields that will be aggregated.
            The default is all of the join node input fields.
        unique : flag indicating whether to ignore duplicate input values

        See Node docstring for additional keyword arguments.
        """
        super(JoinNode, self).__init__(interface, name, **kwargs)

        self._joinsource = None  # The member should be defined
        self.joinsource = joinsource  # Let the setter do the job
        """the join predecessor iterable node"""

        if not joinfield:
            # default is the interface fields
            joinfield = self._interface.inputs.copyable_trait_names()
        elif isinstance(joinfield, (str, bytes)):
            joinfield = [joinfield]
        self.joinfield = joinfield
        """the fields to join"""

        self._inputs = self._override_join_traits(self._interface.inputs,
                                                  self.joinfield)
        """the override inputs"""

        self._unique = unique
        """flag indicating whether to ignore duplicate input values"""

        self._next_slot_index = 0
        """the joinfield index assigned to an iterated input"""

    @property
    def joinsource(self):
        return self._joinsource

    @joinsource.setter
    def joinsource(self, value):
        """Set the joinsource property. If the given value is a Node,
        then the joinsource is set to the node name.
        """
        if isinstance(value, Node):
            value = value.name
        self._joinsource = value

    @property
    def inputs(self):
        """The JoinNode inputs include the join field overrides."""
        return self._inputs

    def _add_join_item_fields(self):
        """Add new join item fields assigned to the next iterated
        input

        This method is intended solely for workflow graph expansion.

        Examples
        --------

        >>> from nipype.interfaces.utility import IdentityInterface
        >>> import nipype.pipeline.engine as pe
        >>> from nipype import Node, JoinNode, Workflow
        >>> inputspec = Node(IdentityInterface(fields=['image']),
        ...    name='inputspec'),
        >>> join = JoinNode(IdentityInterface(fields=['images', 'mask']),
        ...    joinsource='inputspec', joinfield='images', name='join')
        >>> join._add_join_item_fields()
        {'images': 'imagesJ1'}

        Return the {base field: slot field} dictionary
        """
        # create the new join item fields
        idx = self._next_slot_index
        newfields = dict([(field, self._add_join_item_field(field, idx))
                          for field in self.joinfield])
        # increment the join slot index
        logger.debug("Added the %s join item fields %s.", self, newfields)
        self._next_slot_index += 1
        return newfields

    def _add_join_item_field(self, field, index):
        """Add new join item fields qualified by the given index

        Return the new field name
        """
        # the new field name
        name = "%sJ%d" % (field, index + 1)
        # make a copy of the join trait
        trait = self._inputs.trait(field, False, True)
        # add the join item trait to the override traits
        self._inputs.add_trait(name, trait)

        return name

    def _override_join_traits(self, basetraits, fields):
        """Convert the given join fields to accept an input that
        is a list item rather than a list. Non-join fields
        delegate to the interface traits.

        Return the override DynamicTraitedSpec
        """
        dyntraits = DynamicTraitedSpec()
        if fields is None:
            fields = basetraits.copyable_trait_names()
        else:
            # validate the fields
            for field in fields:
                if not basetraits.trait(field):
                    raise ValueError("The JoinNode %s does not have a field"
                                     " named %s" % (self.name, field))
        for name, trait in list(basetraits.items()):
            # if a join field has a single inner trait, then the item
            # trait is that inner trait. Otherwise, the item trait is
            # a new Any trait.
            if name in fields and len(trait.inner_traits) == 1:
                item_trait = trait.inner_traits[0]
                dyntraits.add_trait(name, item_trait)
                setattr(dyntraits, name, Undefined)
                logger.debug(
                    "Converted the join node %s field %s trait type from %s to %s",
                    self, name, trait.trait_type.info(), item_trait.info())
            else:
                dyntraits.add_trait(name, traits.Any)
                setattr(dyntraits, name, Undefined)
        return dyntraits

    def _run_command(self, execute, copyfiles=True):
        """Collates the join inputs prior to delegating to the superclass."""
        self._collate_join_field_inputs()
        return super(JoinNode, self)._run_command(execute, copyfiles)

    def _collate_join_field_inputs(self):
        """
        Collects each override join item field into the interface join
        field input."""
        for field in self.inputs.copyable_trait_names():
            if field in self.joinfield:
                # collate the join field
                val = self._collate_input_value(field)
                try:
                    setattr(self._interface.inputs, field, val)
                except Exception as e:
                    raise ValueError(">>JN %s %s %s %s %s: %s" %
                                     (self, field, val,
                                      self.inputs.copyable_trait_names(),
                                      self.joinfield, e))
            elif hasattr(self._interface.inputs, field):
                # copy the non-join field
                val = getattr(self._inputs, field)
                if isdefined(val):
                    setattr(self._interface.inputs, field, val)
        logger.debug("Collated %d inputs into the %s node join fields",
                     self._next_slot_index, self)

    def _collate_input_value(self, field):
        """
        Collects the join item field values into a list or set value for
        the given field, as follows:

        - If the field trait is a Set, then the values are collected into
        a set.

        - Otherwise, the values are collected into a list which preserves
        the iterables order. If the ``unique`` flag is set, then duplicate
        values are removed but the iterables order is preserved.
        """
        val = [
            self._slot_value(field, idx)
            for idx in range(self._next_slot_index)
        ]
        basetrait = self._interface.inputs.trait(field)
        if isinstance(basetrait.trait_type, traits.Set):
            return set(val)

        if self._unique:
            return list(OrderedDict.fromkeys(val))

        return val

    def _slot_value(self, field, index):
        slot_field = "%sJ%d" % (field, index + 1)
        try:
            return getattr(self._inputs, slot_field)
        except AttributeError as e:
            raise AttributeError(
                "The join node %s does not have a slot field %s"
                " to hold the %s value at index %d: %s" % (self, slot_field,
                                                           field, index, e))


class MapNode(Node):
    """Wraps interface objects that need to be iterated on a list of inputs.

    Examples
    --------

    >>> from nipype import MapNode
    >>> from nipype.interfaces import fsl
    >>> realign = MapNode(fsl.MCFLIRT(), 'in_file', 'realign')
    >>> realign.inputs.in_file = ['functional.nii',
    ...                           'functional2.nii',
    ...                           'functional3.nii']
    >>> realign.run() # doctest: +SKIP

    """

    def __init__(self,
                 interface,
                 iterfield,
                 name,
                 serial=False,
                 nested=False,
                 **kwargs):
        """

        Parameters
        ----------
        interface : interface object
            node specific interface (fsl.Bet(), spm.Coregister())
        iterfield : string or list of strings
            name(s) of input fields that will receive a list of whatever kind
            of input they take. the node will be run separately for each
            value in these lists. for more than one input, the values are
            paired (i.e. it does not compute a combinatorial product).
        name : alphanumeric string
            node specific name
        serial : boolean
            flag to enforce executing the jobs of the mapnode in a serial
            manner rather than parallel
        nested : boolean
            support for nested lists. If set, the input list will be flattened
            before running and the nested list structure of the outputs will
            be resored.

        See Node docstring for additional keyword arguments.
        """

        super(MapNode, self).__init__(interface, name, **kwargs)
        if isinstance(iterfield, (str, bytes)):
            iterfield = [iterfield]
        self.iterfield = iterfield
        self.nested = nested
        self._inputs = self._create_dynamic_traits(
            self._interface.inputs, fields=self.iterfield)
        self._inputs.on_trait_change(self._set_mapnode_input)
        self._got_inputs = False
        self._serial = serial

    def _create_dynamic_traits(self, basetraits, fields=None, nitems=None):
        """Convert specific fields of a trait to accept multiple inputs
        """
        output = DynamicTraitedSpec()
        if fields is None:
            fields = basetraits.copyable_trait_names()
        for name, spec in list(basetraits.items()):
            if name in fields and ((nitems is None) or (nitems > 1)):
                logger.debug('adding multipath trait: %s', name)
                if self.nested:
                    output.add_trait(name, InputMultiPath(traits.Any()))
                else:
                    output.add_trait(name, InputMultiPath(spec.trait_type))
            else:
                output.add_trait(name, traits.Trait(spec))
            setattr(output, name, Undefined)
            value = getattr(basetraits, name)
            if isdefined(value):
                setattr(output, name, value)
            value = getattr(output, name)
        return output

    def set_input(self, parameter, val):
        """
        Set interface input value or nodewrapper attribute
        Priority goes to interface.
        """
        logger.debug('setting nodelevel(%s) input %s = %s', to_str(self),
                     parameter, to_str(val))
        self._set_mapnode_input(parameter, deepcopy(val))

    def _set_mapnode_input(self, name, newvalue):
        logger.debug('setting mapnode(%s) input: %s -> %s', to_str(self), name,
                     to_str(newvalue))
        if name in self.iterfield:
            setattr(self._inputs, name, newvalue)
        else:
            setattr(self._interface.inputs, name, newvalue)

    def _get_hashval(self):
        """Compute hash including iterfield lists."""
        self._get_inputs()

        if self._hashvalue is not None and self._hashed_inputs is not None:
            return self._hashed_inputs, self._hashvalue

        self._check_iterfield()
        hashinputs = deepcopy(self._interface.inputs)
        for name in self.iterfield:
            hashinputs.remove_trait(name)
            hashinputs.add_trait(
                name,
                InputMultiPath(
                    self._interface.inputs.traits()[name].trait_type))
            logger.debug('setting hashinput %s-> %s', name,
                         getattr(self._inputs, name))
            if self.nested:
                setattr(hashinputs, name, flatten(getattr(self._inputs, name)))
            else:
                setattr(hashinputs, name, getattr(self._inputs, name))
        hashed_inputs, hashvalue = hashinputs.get_hashval(
            hash_method=self.config['execution']['hash_method'])
        rm_extra = self.config['execution']['remove_unnecessary_outputs']
        if str2bool(rm_extra) and self.needed_outputs:
            hashobject = md5()
            hashobject.update(hashvalue.encode())
            sorted_outputs = sorted(self.needed_outputs)
            hashobject.update(str(sorted_outputs).encode())
            hashvalue = hashobject.hexdigest()
            hashed_inputs.append(('needed_outputs', sorted_outputs))
        self._hashed_inputs, self._hashvalue = hashed_inputs, hashvalue
        return self._hashed_inputs, self._hashvalue

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        if self._interface._outputs():
            return Bunch(self._interface._outputs().trait_get())

    def _make_nodes(self, cwd=None):
        if cwd is None:
            cwd = self.output_dir()
        if self.nested:
            nitems = len(
                flatten(
                    ensure_list(getattr(self.inputs, self.iterfield[0]))))
        else:
            nitems = len(
                ensure_list(getattr(self.inputs, self.iterfield[0])))
        for i in range(nitems):
            nodename = '_%s%d' % (self.name, i)
            node = Node(
                deepcopy(self._interface),
                n_procs=self._n_procs,
                mem_gb=self._mem_gb,
                overwrite=self.overwrite,
                needed_outputs=self.needed_outputs,
                run_without_submitting=self.run_without_submitting,
                base_dir=op.join(cwd, 'mapflow'),
                name=nodename)
            node.plugin_args = self.plugin_args
            node.interface.inputs.trait_set(
                **deepcopy(self._interface.inputs.trait_get()))
            node.interface.resource_monitor = self._interface.resource_monitor
            for field in self.iterfield:
                if self.nested:
                    fieldvals = flatten(
                        ensure_list(getattr(self.inputs, field)))
                else:
                    fieldvals = ensure_list(getattr(self.inputs, field))
                logger.debug('setting input %d %s %s', i, field, fieldvals[i])
                setattr(node.inputs, field, fieldvals[i])
            node.config = self.config
            yield i, node

    def _collate_results(self, nodes):
        finalresult = InterfaceResult(
            interface=[],
            runtime=[],
            provenance=[],
            inputs=[],
            outputs=self.outputs)
        returncode = []
        for i, nresult, err in nodes:
            finalresult.runtime.insert(i, None)
            returncode.insert(i, err)

            if nresult:
                if hasattr(nresult, 'runtime'):
                    finalresult.interface.insert(i, nresult.interface)
                    finalresult.inputs.insert(i, nresult.inputs)
                    finalresult.runtime[i] = nresult.runtime
                if hasattr(nresult, 'provenance'):
                    finalresult.provenance.insert(i, nresult.provenance)

            if self.outputs:
                for key, _ in list(self.outputs.items()):
                    rm_extra = (
                        self.config['execution']['remove_unnecessary_outputs'])
                    if str2bool(rm_extra) and self.needed_outputs:
                        if key not in self.needed_outputs:
                            continue
                    values = getattr(finalresult.outputs, key)
                    if not isdefined(values):
                        values = []
                    if nresult and nresult.outputs:
                        values.insert(i, nresult.outputs.trait_get()[key])
                    else:
                        values.insert(i, None)
                    defined_vals = [isdefined(val) for val in values]
                    if any(defined_vals) and finalresult.outputs:
                        setattr(finalresult.outputs, key, values)

        if self.nested:
            for key, _ in list(self.outputs.items()):
                values = getattr(finalresult.outputs, key)
                if isdefined(values):
                    values = unflatten(values,
                                       ensure_list(
                                           getattr(self.inputs,
                                                   self.iterfield[0])))
                setattr(finalresult.outputs, key, values)

        if returncode and any([code is not None for code in returncode]):
            msg = []
            for i, code in enumerate(returncode):
                if code is not None:
                    msg += ['Subnode %d failed' % i]
                    msg += ['Error: %s' % str(code)]
            raise Exception('Subnodes of node: %s failed:\n%s' %
                            (self.name, '\n'.join(msg)))

        return finalresult

    def get_subnodes(self):
        """Generate subnodes of a mapnode and write pre-execution report"""
        self._get_inputs()
        self._check_iterfield()
        write_report(self, report_type='preexec', is_mapnode=True)
        return [node for _, node in self._make_nodes()]

    def num_subnodes(self):
        """Get the number of subnodes to iterate in this MapNode"""
        self._get_inputs()
        self._check_iterfield()
        if self._serial:
            return 1
        if self.nested:
            return len(
                ensure_list(
                    flatten(getattr(self.inputs, self.iterfield[0]))))
        return len(ensure_list(getattr(self.inputs, self.iterfield[0])))

    def _get_inputs(self):
        old_inputs = self._inputs.trait_get()
        self._inputs = self._create_dynamic_traits(
            self._interface.inputs, fields=self.iterfield)
        self._inputs.trait_set(**old_inputs)
        super(MapNode, self)._get_inputs()

    def _check_iterfield(self):
        """Checks iterfield

        * iterfield must be in inputs
        * number of elements must match across iterfield
        """
        for iterfield in self.iterfield:
            if not isdefined(getattr(self.inputs, iterfield)):
                raise ValueError(("Input %s was not set but it is listed "
                                  "in iterfields.") % iterfield)
        if len(self.iterfield) > 1:
            first_len = len(
                ensure_list(getattr(self.inputs, self.iterfield[0])))
            for iterfield in self.iterfield[1:]:
                if first_len != len(
                        ensure_list(getattr(self.inputs, iterfield))):
                    raise ValueError(
                        ("All iterfields of a MapNode have to "
                         "have the same length. %s") % str(self.inputs))

    def _run_interface(self, execute=True, updatehash=False):
        """Run the mapnode interface

        This is primarily intended for serial execution of mapnode. A parallel
        execution requires creation of new nodes that can be spawned
        """
        self._check_iterfield()
        cwd = self.output_dir()
        if not execute:
            return self._load_results()

        # Set up mapnode folder names
        if self.nested:
            nitems = len(
                ensure_list(
                    flatten(getattr(self.inputs, self.iterfield[0]))))
        else:
            nitems = len(
                ensure_list(getattr(self.inputs, self.iterfield[0])))
        nnametpl = '_%s{}' % self.name
        nodenames = [nnametpl.format(i) for i in range(nitems)]

        # Run mapnode
        result = self._collate_results(
            _node_runner(
                self._make_nodes(cwd),
                updatehash=updatehash,
                stop_first=str2bool(
                    self.config['execution']['stop_on_first_crash'])))
        # And store results
        _save_resultfile(result, cwd, self.name)
        # remove any node directories no longer required
        dirs2remove = []
        for path in glob(op.join(cwd, 'mapflow', '*')):
            if op.isdir(path):
                if path.split(op.sep)[-1] not in nodenames:
                    dirs2remove.append(path)
        for path in dirs2remove:
            logger.debug('[MapNode] Removing folder "%s".', path)
            shutil.rmtree(path)

        return result
