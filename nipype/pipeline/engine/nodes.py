#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Node` class provides core functionality for batch processing.

  .. testsetup::
     # Change directory to provide relative paths for doctests
     import os
     filepath = os.path.dirname(os.path.realpath( __file__ ))
     datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
     os.chdir(datadir)

"""
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import range, object, str, bytes, open

from future import standard_library
standard_library.install_aliases()
from collections import OrderedDict

from copy import deepcopy
import pickle
from glob import glob
import gzip
import os
import os.path as op
import shutil
import errno
import socket
from shutil import rmtree
import sys
from tempfile import mkdtemp
from hashlib import sha1

from ... import config, logging
from ...utils.misc import (flatten, unflatten, str2bool)
from ...utils.filemanip import (save_json, FileNotFoundError,
                                filename_to_list, list_to_filename,
                                copyfiles, fnames_presuffix, loadpkl,
                                split_filename, load_json, savepkl,
                                write_rst_header, write_rst_dict,
                                write_rst_list, to_str)
from ...interfaces.base import (traits, InputMultiPath, CommandLine,
                                Undefined, TraitedSpec, DynamicTraitedSpec,
                                Bunch, InterfaceResult, md5, Interface,
                                TraitDictObject, TraitListObject, isdefined,
                                runtime_profile)
from .utils import (generate_expanded_graph, modify_paths,
                    export_graph, make_output_dir, write_workflow_prov,
                    clean_working_directory, format_dot, topological_sort,
                    get_print_name, merge_dict, evaluate_connect_function)
from .base import EngineBase

logger = logging.getLogger('workflow')

class Node(EngineBase):
    """Wraps interface objects for use in pipeline

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

    def __init__(self, interface, name, iterables=None, itersource=None,
                 synchronize=False, overwrite=None, needed_outputs=None,
                 run_without_submitting=False, n_procs=1, mem_gb=None,
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
        base_dir = None
        if 'base_dir' in kwargs:
            base_dir = kwargs['base_dir']
        super(Node, self).__init__(name, base_dir)
        if interface is None:
            raise IOError('Interface must be provided')
        if not isinstance(interface, Interface):
            raise IOError('interface must be an instance of an Interface')
        self._interface = interface
        self.name = name
        self._result = None
        self.iterables = iterables
        self.synchronize = synchronize
        self.itersource = itersource
        self.overwrite = overwrite
        self.parameterization = None
        self.run_without_submitting = run_without_submitting
        self.input_source = {}
        self.needed_outputs = []
        self.plugin_args = {}

        self._interface.num_threads = n_procs
        if mem_gb is not None:
            self._interface.estimated_memory_gb = mem_gb

        if needed_outputs:
            self.needed_outputs = sorted(needed_outputs)
        self._got_inputs = False

    @property
    def interface(self):
        """Return the underlying interface object"""
        return self._interface

    @property
    def result(self):
        if self._result:
            return self._result
        else:
            cwd = self.output_dir()
            result, _, _ = self._load_resultfile(cwd)
            return result

    @property
    def inputs(self):
        """Return the inputs of the underlying interface"""
        return self._interface.inputs

    @property
    def outputs(self):
        """Return the output fields of the underlying interface"""
        return self._interface._outputs()

    def output_dir(self):
        """Return the location of the output directory for the node"""
        if self.base_dir is None:
            self.base_dir = mkdtemp()
        outputdir = self.base_dir
        if self._hierarchy:
            outputdir = op.join(outputdir, *self._hierarchy.split('.'))
        if self.parameterization:
            params_str = ['{}'.format(p) for p in self.parameterization]
            if not str2bool(self.config['execution']['parameterize_dirs']):
                params_str = [self._parameterization_dir(p) for p in params_str]
            outputdir = op.join(outputdir, *params_str)
        return op.abspath(op.join(outputdir, self.name))

    def set_input(self, parameter, val):
        """ Set interface input value"""
        logger.debug('setting nodelevel(%s) input %s = %s',
                     self.name, parameter, to_str(val))
        setattr(self.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        """Retrieve a particular output of the node"""
        val = None
        if self._result:
            val = getattr(self._result.outputs, parameter)
        else:
            cwd = self.output_dir()
            result, _, _ = self._load_resultfile(cwd)
            if result and result.outputs:
                val = getattr(result.outputs, parameter)
        return val

    def help(self):
        """ Print interface help"""
        self._interface.help()

    def hash_exists(self, updatehash=False):
        # Get a dictionary with hashed filenames and a hashvalue
        # of the dictionary itself.
        hashed_inputs, hashvalue = self._get_hashval()
        outdir = self.output_dir()
        if op.exists(outdir):
            logger.debug('Output dir: %s', to_str(os.listdir(outdir)))
        hashfiles = glob(op.join(outdir, '_0x*.json'))
        logger.debug('Found hashfiles: %s', to_str(hashfiles))
        if len(hashfiles) > 1:
            logger.info(hashfiles)
            logger.info('Removing multiple hashfiles and forcing node to rerun')
            for hashfile in hashfiles:
                os.unlink(hashfile)
        hashfile = op.join(outdir, '_0x%s.json' % hashvalue)
        logger.debug('Final hashfile: %s', hashfile)
        if updatehash and op.exists(outdir):
            logger.debug("Updating hash: %s", hashvalue)
            for file in glob(op.join(outdir, '_0x*.json')):
                os.remove(file)
            self._save_hashfile(hashfile, hashed_inputs)
        return op.exists(hashfile), hashvalue, hashfile, hashed_inputs

    def run(self, updatehash=False):
        """Execute the node in its directory.

        Parameters
        ----------

        updatehash: boolean
            Update the hash stored in the output directory
        """
        # check to see if output directory and hash exist
        if self.config is None:
            self.config = deepcopy(config._sections)
        else:
            self.config = merge_dict(deepcopy(config._sections), self.config)
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        outdir = self.output_dir()
        logger.info("Executing node %s in dir: %s", self._id, outdir)
        if op.exists(outdir):
            logger.debug('Output dir: %s', to_str(os.listdir(outdir)))
        hash_info = self.hash_exists(updatehash=updatehash)
        hash_exists, hashvalue, hashfile, hashed_inputs = hash_info
        logger.debug(
            'updatehash=%s, overwrite=%s, always_run=%s, hash_exists=%s',
            updatehash, self.overwrite, self._interface.always_run, hash_exists)
        if (not updatehash and (((self.overwrite is None and
                                  self._interface.always_run) or
                                 self.overwrite) or not
                                hash_exists)):
            logger.debug("Node hash: %s", hashvalue)

            # by rerunning we mean only nodes that did finish to run previously
            json_pat = op.join(outdir, '_0x*.json')
            json_unfinished_pat = op.join(outdir, '_0x*_unfinished.json')
            need_rerun = (op.exists(outdir) and not
                          isinstance(self, MapNode) and
                          len(glob(json_pat)) != 0 and
                          len(glob(json_unfinished_pat)) == 0)
            if need_rerun:
                logger.debug(
                    "Rerunning node:\n"
                    "updatehash = %s, self.overwrite = %s, self._interface.always_run = %s, "
                    "os.path.exists(%s) = %s, hash_method = %s", updatehash, self.overwrite,
                    self._interface.always_run, hashfile, op.exists(hashfile),
                    self.config['execution']['hash_method'].lower())
                log_debug = config.get('logging', 'workflow_level') == 'DEBUG'
                if log_debug and not op.exists(hashfile):
                    exp_hash_paths = glob(json_pat)
                    if len(exp_hash_paths) == 1:
                        split_out = split_filename(exp_hash_paths[0])
                        exp_hash_file_base = split_out[1]
                        exp_hash = exp_hash_file_base[len('_0x'):]
                        logger.debug("Previous node hash = %s", exp_hash)
                        try:
                            prev_inputs = load_json(exp_hash_paths[0])
                        except:
                            pass
                        else:
                            logging.logdebug_dict_differences(prev_inputs,
                                                              hashed_inputs)
                cannot_rerun = (str2bool(
                    self.config['execution']['stop_on_first_rerun']) and not
                    (self.overwrite is None and self._interface.always_run))
                if cannot_rerun:
                    raise Exception(("Cannot rerun when 'stop_on_first_rerun' "
                                     "is set to True"))
            hashfile_unfinished = op.join(outdir,
                                          '_0x%s_unfinished.json' %
                                          hashvalue)
            if op.exists(hashfile):
                os.remove(hashfile)
            rm_outdir = (op.exists(outdir) and not
                         (op.exists(hashfile_unfinished) and
                             self._interface.can_resume) and not
                         isinstance(self, MapNode))
            if rm_outdir:
                logger.debug("Removing old %s and its contents", outdir)
                try:
                    rmtree(outdir)
                except OSError as ex:
                    outdircont = os.listdir(outdir)
                    if ((ex.errno == errno.ENOTEMPTY) and (len(outdircont) == 0)):
                        logger.warn(
                            'An exception was raised trying to remove old %s, but the path '
                            'seems empty. Is it an NFS mount?. Passing the exception.', outdir)
                    elif ((ex.errno == errno.ENOTEMPTY) and (len(outdircont) != 0)):
                        logger.debug(
                            'Folder contents (%d items): %s', len(outdircont), outdircont)
                        raise ex
                    else:
                        raise ex

            else:
                logger.debug(
                    "%s found and can_resume is True or Node is a MapNode - resuming execution",
                    hashfile_unfinished)
                if isinstance(self, MapNode):
                    # remove old json files
                    for filename in glob(op.join(outdir, '_0x*.json')):
                        os.unlink(filename)
            outdir = make_output_dir(outdir)
            self._save_hashfile(hashfile_unfinished, hashed_inputs)
            self.write_report(report_type='preexec', cwd=outdir)
            savepkl(op.join(outdir, '_node.pklz'), self)
            savepkl(op.join(outdir, '_inputs.pklz'),
                    self.inputs.get_traitsfree())
            try:
                self._run_interface()
            except:
                os.remove(hashfile_unfinished)
                raise
            shutil.move(hashfile_unfinished, hashfile)
            self.write_report(report_type='postexec', cwd=outdir)
        else:
            if not op.exists(op.join(outdir, '_inputs.pklz')):
                logger.debug('%s: creating inputs file', self.name)
                savepkl(op.join(outdir, '_inputs.pklz'),
                        self.inputs.get_traitsfree())
            if not op.exists(op.join(outdir, '_node.pklz')):
                logger.debug('%s: creating node file', self.name)
                savepkl(op.join(outdir, '_node.pklz'), self)
            logger.debug("Hashfile exists. Skipping execution")
            self._run_interface(execute=False, updatehash=updatehash)
        logger.debug('Finished running %s in dir: %s\n', self._id, outdir)
        return self._result

    # Private functions
    def _parameterization_dir(self, param):
        """
        Returns the directory name for the given parameterization string as follows:
            - If the parameterization is longer than 32 characters, then
              return the SHA-1 hex digest.
            - Otherwise, return the parameterization unchanged.
        """
        if len(param) > 32:
            return sha1(param.encode()).hexdigest()
        else:
            return param

    def _get_hashval(self):
        """Return a hash of the input state"""
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        hashed_inputs, hashvalue = self.inputs.get_hashval(
            hash_method=self.config['execution']['hash_method'])
        rm_extra = self.config['execution']['remove_unnecessary_outputs']
        if str2bool(rm_extra) and self.needed_outputs:
            hashobject = md5()
            hashobject.update(hashvalue.encode())
            sorted_outputs = sorted(self.needed_outputs)
            hashobject.update(str(sorted_outputs).encode())
            hashvalue = hashobject.hexdigest()
            hashed_inputs.append(('needed_outputs', sorted_outputs))
        return hashed_inputs, hashvalue

    def _save_hashfile(self, hashfile, hashed_inputs):
        try:
            save_json(hashfile, hashed_inputs)
        except (IOError, TypeError):
            err_type = sys.exc_info()[0]
            if err_type is TypeError:
                # XXX - SG current workaround is to just
                # create the hashed file and not put anything
                # in it
                with open(hashfile, 'wt') as fd:
                    fd.writelines(str(hashed_inputs))

                logger.debug(
                    'Unable to write a particular type to the json file')
            else:
                logger.critical('Unable to open the file in write mode: %s',
                                hashfile)

    def _get_inputs(self):
        """Retrieve inputs from pointers to results file

        This mechanism can be easily extended/replaced to retrieve data from
        other data sources (e.g., XNAT, HTTP, etc.,.)
        """
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
                    output_value = evaluate_connect_function(info[1][1],
                                                             info[1][2],
                                                             value)
            else:
                output_name = info[1]
                try:
                    output_value = results.outputs.get()[output_name]
                except TypeError:
                    output_value = results.outputs.dictcopy()[output_name]
            logger.debug('output: %s', output_name)
            try:
                self.set_input(key, deepcopy(output_value))
            except traits.TraitError as e:
                msg = ['Error setting node input:',
                       'Node: %s' % self.name,
                       'input: %s' % key,
                       'results_file: %s' % results_file,
                       'value: %s' % str(output_value)]
                e.args = (e.args[0] + "\n" + '\n'.join(msg),)
                raise

    def _run_interface(self, execute=True, updatehash=False):
        if updatehash:
            return
        old_cwd = os.getcwd()
        os.chdir(self.output_dir())
        self._result = self._run_command(execute)
        os.chdir(old_cwd)

    def _save_results(self, result, cwd):
        resultsfile = op.join(cwd, 'result_%s.pklz' % self.name)
        if result.outputs:
            try:
                outputs = result.outputs.get()
            except TypeError:
                outputs = result.outputs.dictcopy()  # outputs was a bunch
            result.outputs.set(**modify_paths(outputs, relative=True,
                                              basedir=cwd))

        savepkl(resultsfile, result)
        logger.debug('saved results in %s', resultsfile)

        if result.outputs:
            result.outputs.set(**outputs)

    def _load_resultfile(self, cwd):
        """Load results if it exists in cwd

        Parameter
        ---------

        cwd : working directory of node

        Returns
        -------

        result : InterfaceResult structure
        aggregate : boolean indicating whether node should aggregate_outputs
        attribute error : boolean indicating whether there was some mismatch in
            versions of traits used to store result and hence node needs to
            rerun
        """
        aggregate = True
        resultsoutputfile = op.join(cwd, 'result_%s.pklz' % self.name)
        result = None
        attribute_error = False
        if op.exists(resultsoutputfile):
            pkl_file = gzip.open(resultsoutputfile, 'rb')
            try:
                result = pickle.load(pkl_file)
            except UnicodeDecodeError:
                # Was this pickle created with Python 2.x?
                pickle.load(pkl_file, fix_imports=True, encoding='utf-8')
                logger.warn('Successfully loaded pickle in compatibility mode')
            except (traits.TraitError, AttributeError, ImportError,
                    EOFError) as err:
                if isinstance(err, (AttributeError, ImportError)):
                    attribute_error = True
                    logger.debug('attribute error: %s probably using '
                                 'different trait pickled file', str(err))
                else:
                    logger.debug(
                        'some file does not exist. hence trait cannot be set')
            else:
                if result.outputs:
                    try:
                        outputs = result.outputs.get()
                    except TypeError:
                        outputs = result.outputs.dictcopy()  # outputs == Bunch
                    try:
                        result.outputs.set(**modify_paths(outputs,
                                                          relative=False,
                                                          basedir=cwd))
                    except FileNotFoundError:
                        logger.debug('conversion to full path results in '
                                     'non existent file')
                aggregate = False
            pkl_file.close()
        logger.debug('Aggregate: %s', aggregate)
        return result, aggregate, attribute_error

    def _load_results(self, cwd):
        result, aggregate, attribute_error = self._load_resultfile(cwd)
        # try aggregating first
        if aggregate:
            logger.debug('aggregating results')
            if attribute_error:
                old_inputs = loadpkl(op.join(cwd, '_inputs.pklz'))
                self.inputs.set(**old_inputs)
            if not isinstance(self, MapNode):
                self._copyfiles_to_wd(cwd, True, linksonly=True)
                aggouts = self._interface.aggregate_outputs(
                    needed_outputs=self.needed_outputs)
                runtime = Bunch(cwd=cwd,
                                returncode=0,
                                environ=dict(os.environ),
                                hostname=socket.gethostname())
                result = InterfaceResult(
                    interface=self._interface.__class__,
                    runtime=runtime,
                    inputs=self._interface.inputs.get_traitsfree(),
                    outputs=aggouts)
                self._save_results(result, cwd)
            else:
                logger.debug('aggregating mapnode results')
                self._run_interface()
                result = self._result
        return result

    def _run_command(self, execute, copyfiles=True):
        cwd = os.getcwd()
        if execute and copyfiles:
            self._originputs = deepcopy(self._interface.inputs)
        if execute:
            runtime = Bunch(returncode=1,
                            environ=dict(os.environ),
                            hostname=socket.gethostname())
            result = InterfaceResult(
                interface=self._interface.__class__,
                runtime=runtime,
                inputs=self._interface.inputs.get_traitsfree())
            self._result = result
            logger.debug('Executing node')
            if copyfiles:
                self._copyfiles_to_wd(cwd, execute)
            if issubclass(self._interface.__class__, CommandLine):
                try:
                    cmd = self._interface.cmdline
                except Exception as msg:
                    self._result.runtime.stderr = msg
                    raise
                cmdfile = op.join(cwd, 'command.txt')
                fd = open(cmdfile, 'wt')
                fd.writelines(cmd + "\n")
                fd.close()
                logger.info('Running: %s' % cmd)
            try:
                result = self._interface.run()
            except Exception as msg:
                self._save_results(result, cwd)
                self._result.runtime.stderr = msg
                raise

            dirs2keep = None
            if isinstance(self, MapNode):
                dirs2keep = [op.join(cwd, 'mapflow')]
            result.outputs = clean_working_directory(result.outputs, cwd,
                                                     self._interface.inputs,
                                                     self.needed_outputs,
                                                     self.config,
                                                     dirs2keep=dirs2keep)
            self._save_results(result, cwd)
        else:
            logger.info("Collecting precomputed outputs")
            try:
                result = self._load_results(cwd)
            except (FileNotFoundError, AttributeError):
                # if aggregation does not work, rerun the node
                logger.info(("Some of the outputs were not found: "
                             "rerunning node."))
                result = self._run_command(execute=True, copyfiles=False)
        return result

    def _strip_temp(self, files, wd):
        out = []
        for f in files:
            if isinstance(f, list):
                out.append(self._strip_temp(f, wd))
            else:
                out.append(f.replace(op.join(wd, '_tempinput'), wd))
        return out

    def _copyfiles_to_wd(self, outdir, execute, linksonly=False):
        """ copy files over and change the inputs"""
        if hasattr(self._interface, '_get_filecopy_info'):
            logger.debug('copying files to wd [execute=%s, linksonly=%s]',
                         str(execute), str(linksonly))
            if execute and linksonly:
                olddir = outdir
                outdir = op.join(outdir, '_tempinput')
                os.makedirs(outdir)
            for info in self._interface._get_filecopy_info():
                files = self.inputs.get().get(info['key'])
                if not isdefined(files):
                    continue
                if files:
                    infiles = filename_to_list(files)
                    if execute:
                        if linksonly:
                            if not info['copy']:
                                newfiles = copyfiles(infiles,
                                                     [outdir],
                                                     copy=info['copy'],
                                                     create_new=True)
                            else:
                                newfiles = fnames_presuffix(infiles,
                                                            newpath=outdir)
                            newfiles = self._strip_temp(
                                newfiles,
                                op.abspath(olddir).split(op.sep)[-1])
                        else:
                            newfiles = copyfiles(infiles,
                                                 [outdir],
                                                 copy=info['copy'],
                                                 create_new=True)
                    else:
                        newfiles = fnames_presuffix(infiles, newpath=outdir)
                    if not isinstance(files, list):
                        newfiles = list_to_filename(newfiles)
                    setattr(self.inputs, info['key'], newfiles)
            if execute and linksonly:
                rmtree(outdir)

    def update(self, **opts):
        self.inputs.update(**opts)

    def write_report(self, report_type=None, cwd=None):
        if not str2bool(self.config['execution']['create_report']):
            return
        report_dir = op.join(cwd, '_report')
        report_file = op.join(report_dir, 'report.rst')
        if not op.exists(report_dir):
            os.makedirs(report_dir)
        if report_type == 'preexec':
            logger.debug('writing pre-exec report to %s', report_file)
            fp = open(report_file, 'wt')
            fp.writelines(write_rst_header('Node: %s' % get_print_name(self),
                                           level=0))
            fp.writelines(write_rst_list(['Hierarchy : %s' % self.fullname,
                                          'Exec ID : %s' % self._id]))
            fp.writelines(write_rst_header('Original Inputs', level=1))
            fp.writelines(write_rst_dict(self.inputs.get()))
        if report_type == 'postexec':
            logger.debug('writing post-exec report to %s', report_file)
            fp = open(report_file, 'at')
            fp.writelines(write_rst_header('Execution Inputs', level=1))
            fp.writelines(write_rst_dict(self.inputs.get()))
            exit_now = (not hasattr(self.result, 'outputs') or
                        self.result.outputs is None)
            if exit_now:
                return
            fp.writelines(write_rst_header('Execution Outputs', level=1))
            if isinstance(self.result.outputs, Bunch):
                fp.writelines(write_rst_dict(self.result.outputs.dictcopy()))
            elif self.result.outputs:
                fp.writelines(write_rst_dict(self.result.outputs.get()))
            if isinstance(self, MapNode):
                fp.close()
                return
            fp.writelines(write_rst_header('Runtime info', level=1))
            # Init rst dictionary of runtime stats
            rst_dict = {'hostname' : self.result.runtime.hostname,
                        'duration' : self.result.runtime.duration}
            # Try and insert memory/threads usage if available
            if runtime_profile:
                try:
                    rst_dict['runtime_memory_gb'] = self.result.runtime.runtime_memory_gb
                    rst_dict['runtime_threads'] = self.result.runtime.runtime_threads
                except AttributeError:
                    logger.info('Runtime memory and threads stats unavailable')
            if hasattr(self.result.runtime, 'cmdline'):
                rst_dict['command'] = self.result.runtime.cmdline
                fp.writelines(write_rst_dict(rst_dict))
            else:
                fp.writelines(write_rst_dict(rst_dict))
            if hasattr(self.result.runtime, 'merged'):
                fp.writelines(write_rst_header('Terminal output', level=2))
                fp.writelines(write_rst_list(self.result.runtime.merged))
            if hasattr(self.result.runtime, 'environ'):
                fp.writelines(write_rst_header('Environment', level=2))
                fp.writelines(write_rst_dict(self.result.runtime.environ))
        fp.close()


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

    def __init__(self, interface, name, joinsource, joinfield=None,
                 unique=False, **kwargs):
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

        self.joinsource = joinsource
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
        >>> join._add_join_item_fields() # doctest: +ALLOW_UNICODE
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
        name = self._join_item_field_name(field, index)
        # make a copy of the join trait
        trait = self._inputs.trait(field, False, True)
        # add the join item trait to the override traits
        self._inputs.add_trait(name, trait)

        return name

    def _join_item_field_name(self, field, index):
        """Return the field suffixed by the index + 1"""
        return "%sJ%d" % (field, index + 1)

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
                    raise ValueError(">>JN %s %s %s %s %s: %s" % (self, field, val, self.inputs.copyable_trait_names(), self.joinfield, e))
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
        val = [self._slot_value(field, idx)
               for idx in range(self._next_slot_index)]
        basetrait = self._interface.inputs.trait(field)
        if isinstance(basetrait.trait_type, traits.Set):
            return set(val)
        elif self._unique:
            return list(OrderedDict.fromkeys(val))
        else:
            return val

    def _slot_value(self, field, index):
        slot_field = self._join_item_field_name(field, index)
        try:
            return getattr(self._inputs, slot_field)
        except AttributeError as e:
            raise AttributeError("The join node %s does not have a slot field %s"
                                 " to hold the %s value at index %d: %s"
                                 % (self, slot_field, field, index, e))


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

    def __init__(self, interface, iterfield, name, serial=False, nested=False, **kwargs):
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
            flag to enforce executing the jobs of the mapnode in a serial manner rather than parallel
        nested : boolea
            support for nested lists, if set the input list will be flattened before running, and the
            nested list structure of the outputs will be resored
        See Node docstring for additional keyword arguments.
        """

        super(MapNode, self).__init__(interface, name, **kwargs)
        if isinstance(iterfield, (str, bytes)):
            iterfield = [iterfield]
        self.iterfield = iterfield
        self.nested = nested
        self._inputs = self._create_dynamic_traits(self._interface.inputs,
                                                   fields=self.iterfield)
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
        """ Set interface input value or nodewrapper attribute

        Priority goes to interface.
        """
        logger.debug('setting nodelevel(%s) input %s = %s',
                     to_str(self), parameter, to_str(val))
        self._set_mapnode_input(self.inputs, parameter, deepcopy(val))

    def _set_mapnode_input(self, object, name, newvalue):
        logger.debug('setting mapnode(%s) input: %s -> %s',
                     to_str(self), name, to_str(newvalue))
        if name in self.iterfield:
            setattr(self._inputs, name, newvalue)
        else:
            setattr(self._interface.inputs, name, newvalue)

    def _get_hashval(self):
        """ Compute hash including iterfield lists."""
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        self._check_iterfield()
        hashinputs = deepcopy(self._interface.inputs)
        for name in self.iterfield:
            hashinputs.remove_trait(name)
            hashinputs.add_trait(
                name,
                InputMultiPath(
                    self._interface.inputs.traits()[name].trait_type))
            logger.debug('setting hashinput %s-> %s',
                         name, getattr(self._inputs, name))
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
        return hashed_inputs, hashvalue

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        if self._interface._outputs():
            return Bunch(self._interface._outputs().get())
        else:
            return None

    def _make_nodes(self, cwd=None):
        if cwd is None:
            cwd = self.output_dir()
        if self.nested:
            nitems = len(flatten(filename_to_list(getattr(self.inputs, self.iterfield[0]))))
        else:
            nitems = len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
        for i in range(nitems):
            nodename = '_' + self.name + str(i)
            node = Node(deepcopy(self._interface),
                        n_procs=self._interface.num_threads,
                        mem_gb=self._interface.estimated_memory_gb,
                        overwrite=self.overwrite,
                        needed_outputs=self.needed_outputs,
                        run_without_submitting=self.run_without_submitting,
                        base_dir=op.join(cwd, 'mapflow'),
                        name=nodename)
            node.plugin_args = self.plugin_args
            node._interface.inputs.set(
                **deepcopy(self._interface.inputs.get()))
            for field in self.iterfield:
                if self.nested:
                    fieldvals = flatten(filename_to_list(getattr(self.inputs, field)))
                else:
                    fieldvals = filename_to_list(getattr(self.inputs, field))
                logger.debug('setting input %d %s %s', i, field, fieldvals[i])
                setattr(node.inputs, field, fieldvals[i])
            node.config = self.config
            yield i, node

    def _node_runner(self, nodes, updatehash=False):
        old_cwd = os.getcwd()
        for i, node in nodes:
            err = None
            try:
                node.run(updatehash=updatehash)
            except Exception as this_err:
                err = this_err
                if str2bool(self.config['execution']['stop_on_first_crash']):
                    raise
            finally:
                os.chdir(old_cwd)
                yield i, node, err

    def _collate_results(self, nodes):
        self._result = InterfaceResult(interface=[], runtime=[],
                                       provenance=[], inputs=[],
                                       outputs=self.outputs)
        returncode = []
        for i, node, err in nodes:
            self._result.runtime.insert(i, None)
            if node.result:
                if hasattr(node.result, 'runtime'):
                    self._result.interface.insert(i, node.result.interface)
                    self._result.inputs.insert(i, node.result.inputs)
                    self._result.runtime[i] = node.result.runtime
                if hasattr(node.result, 'provenance'):
                    self._result.provenance.insert(i, node.result.provenance)
            returncode.insert(i, err)
            if self.outputs:
                for key, _ in list(self.outputs.items()):
                    rm_extra = (self.config['execution']
                                ['remove_unnecessary_outputs'])
                    if str2bool(rm_extra) and self.needed_outputs:
                        if key not in self.needed_outputs:
                            continue
                    values = getattr(self._result.outputs, key)
                    if not isdefined(values):
                        values = []
                    if node.result.outputs:
                        values.insert(i, node.result.outputs.get()[key])
                    else:
                        values.insert(i, None)
                    defined_vals = [isdefined(val) for val in values]
                    if any(defined_vals) and self._result.outputs:
                        setattr(self._result.outputs, key, values)

        if self.nested:
            for key, _ in list(self.outputs.items()):
                values = getattr(self._result.outputs, key)
                if isdefined(values):
                    values = unflatten(values, filename_to_list(getattr(self.inputs, self.iterfield[0])))
                setattr(self._result.outputs, key, values)

        if returncode and any([code is not None for code in returncode]):
            msg = []
            for i, code in enumerate(returncode):
                if code is not None:
                    msg += ['Subnode %d failed' % i]
                    msg += ['Error:', str(code)]
            raise Exception('Subnodes of node: %s failed:\n%s' %
                            (self.name, '\n'.join(msg)))

    def write_report(self, report_type=None, cwd=None):
        if not str2bool(self.config['execution']['create_report']):
            return
        if report_type == 'preexec':
            super(MapNode, self).write_report(report_type=report_type, cwd=cwd)
        if report_type == 'postexec':
            super(MapNode, self).write_report(report_type=report_type, cwd=cwd)
            report_dir = op.join(cwd, '_report')
            report_file = op.join(report_dir, 'report.rst')
            fp = open(report_file, 'at')
            fp.writelines(write_rst_header('Subnode reports', level=1))
            nitems = len(filename_to_list(
                getattr(self.inputs, self.iterfield[0])))
            subnode_report_files = []
            for i in range(nitems):
                nodename = '_' + self.name + str(i)
                subnode_report_files.insert(i, 'subnode %d' % i + ' : ' +
                                               op.join(cwd,
                                                       'mapflow',
                                                       nodename,
                                                       '_report',
                                                       'report.rst'))
            fp.writelines(write_rst_list(subnode_report_files))
            fp.close()

    def get_subnodes(self):
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        self._check_iterfield()
        self.write_report(report_type='preexec', cwd=self.output_dir())
        return [node for _, node in self._make_nodes()]

    def num_subnodes(self):
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        self._check_iterfield()
        if self._serial:
            return 1
        else:
            if self.nested:
                return len(filename_to_list(flatten(getattr(self.inputs, self.iterfield[0]))))
            else:
                return len(filename_to_list(getattr(self.inputs, self.iterfield[0])))

    def _get_inputs(self):
        old_inputs = self._inputs.get()
        self._inputs = self._create_dynamic_traits(self._interface.inputs,
                                                   fields=self.iterfield)
        self._inputs.set(**old_inputs)
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
            first_len = len(filename_to_list(getattr(self.inputs,
                                                     self.iterfield[0])))
            for iterfield in self.iterfield[1:]:
                if first_len != len(filename_to_list(getattr(self.inputs,
                                                             iterfield))):
                    raise ValueError(("All iterfields of a MapNode have to "
                                      "have the same length. %s") %
                                     str(self.inputs))

    def _run_interface(self, execute=True, updatehash=False):
        """Run the mapnode interface

        This is primarily intended for serial execution of mapnode. A parallel
        execution requires creation of new nodes that can be spawned
        """
        old_cwd = os.getcwd()
        cwd = self.output_dir()
        os.chdir(cwd)
        self._check_iterfield()
        if execute:
            if self.nested:
                nitems = len(filename_to_list(flatten(getattr(self.inputs,
                                                              self.iterfield[0]))))
            else:
                nitems = len(filename_to_list(getattr(self.inputs,
                                                      self.iterfield[0])))
            nodenames = ['_' + self.name + str(i) for i in range(nitems)]
            self._collate_results(self._node_runner(self._make_nodes(cwd),
                                                    updatehash=updatehash))
            self._save_results(self._result, cwd)
            # remove any node directories no longer required
            dirs2remove = []
            for path in glob(op.join(cwd, 'mapflow', '*')):
                if op.isdir(path):
                    if path.split(op.sep)[-1] not in nodenames:
                        dirs2remove.append(path)
            for path in dirs2remove:
                shutil.rmtree(path)
        else:
            self._result = self._load_results(cwd)
        os.chdir(old_cwd)
