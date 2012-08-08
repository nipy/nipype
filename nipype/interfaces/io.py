# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" Set of interfaces that allow interaction with data. Currently
    available interfaces are:

    DataSource: Generic nifti to named Nifti interface
    DataSink: Generic named output from interfaces to data store
    XNATSource: preliminary interface to XNAT

    To come :
    XNATSink

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

"""
import glob
import os
import shutil
import re
import tempfile
from warnings import warn

import sqlite3

try:
    import pyxnat
except:
    pass

from nipype.interfaces.base import (TraitedSpec, traits, File, Directory,
                                    BaseInterface, InputMultiPath, isdefined,
                                    OutputMultiPath, DynamicTraitedSpec,
                                    Undefined, BaseInterfaceInputSpec)
from nipype.utils.filemanip import (copyfile, list_to_filename,
                                    filename_to_list)

from .. import logging
iflogger = logging.getLogger('interface')


def copytree(src, dst):
    """Recursively copy a directory tree using
    nipype.utils.filemanip.copyfile()

    This is not a thread-safe routine. However, in the case of creating new
    directories, it checks to see if a particular directory has already been
    created by another process.
    """
    names = os.listdir(src)
    try:
        os.makedirs(dst)
    except OSError, why:
        if 'File exists' in why:
            pass
        else:
            raise why
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname)
            else:
                copyfile(srcname, dstname, True, hashmethod='content')
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Exception, err:
            errors.extend(err.args[0])
    if errors:
        raise Exception, errors

def add_traits(base, names, trait_type=None):
    """ Add traits to a traited class.

    All traits are set to Undefined by default
    """
    if trait_type is None:
        trait_type = traits.Any
    undefined_traits = {}
    for key in names:
        base.add_trait(key, trait_type)
        undefined_traits[key] = Undefined
    base.trait_set(trait_change_notify=False, **undefined_traits)
    # access each trait
    for key in names:
        _ = getattr(base, key)
    return base

class IOBase(BaseInterface):

    def _run_interface(self,runtime):
        return runtime

    def _list_outputs(self):
        raise NotImplementedError

    def _outputs(self):
        return self._add_output_traits(super(IOBase, self)._outputs())

    def _add_output_traits(self, base):
        return base

class DataSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    base_directory = Directory(
        desc='Path to the base directory for storing data.')
    container = traits.Str(desc = 'Folder within base directory in which to store output')
    parameterization = traits.Bool(True, usedefault=True,
                                   desc='store output in parametrized structure')
    strip_dir = Directory(desc='path to strip out of filename')
    substitutions = InputMultiPath(traits.Tuple(traits.Str,traits.Str),
                                   desc=('List of 2-tuples reflecting string '
                                         'to substitute and string to replace '
                                         'it with'))
    regexp_substitutions = InputMultiPath(traits.Tuple(traits.Str,traits.Str),
                                   desc=('List of 2-tuples reflecting a pair '
                                         'of a Python regexp pattern and a '
                                         'replacement string. Invoked after '
                                         'string `substitutions`'))

    _outputs = traits.Dict(traits.Str, value={}, usedefault=True)
    remove_dest_dir = traits.Bool(False, usedefault=True,
                                  desc='remove dest directory when copying dirs')

    def __setattr__(self, key, value):
        if key not in self.copyable_trait_names():
            if not isdefined(value):
                super(DataSinkInputSpec, self).__setattr__(key, value)
            self._outputs[key] = value
        else:
            if key in self._outputs:
                self._outputs[key] = value
            super(DataSinkInputSpec, self).__setattr__(key, value)

class DataSink(IOBase):
    """ Generic datasink module to store structured outputs

        Primarily for use within a workflow. This interface allows arbitrary
        creation of input attributes. The names of these attributes define the
        directory structure to create for storage of the files or directories.

        The attributes take the following form:

        string[[.[@]]string[[.[@]]string]] ...

        where parts between [] are optional.

        An attribute such as contrasts.@con will create a 'contrasts' directory
        to store the results linked to the attribute. If the @ is left out, such
        as in 'contrasts.con', a subdirectory 'con' will be created under
        'contrasts'.

        the general form of the output is::

           'base_directory/container/parameterization/destloc/filename'

           destloc = string[[.[@]]string[[.[@]]string]] and
           filename comesfrom the input to the connect statement.

        .. warning::

            This is not a thread-safe node because it can write to a common
            shared location. It will not complain when it overwrites a file.

        .. note::

            If both substitutions and regexp_substitutions are used, then
            substitutions are applied first followed by regexp_substitutions.

            This interface **cannot** be used in a MapNode as the inputs are
            defined only when the connect statement is executed.

        Examples
        --------

        >>> ds = DataSink()
        >>> ds.inputs.base_directory = 'results_dir'
        >>> ds.inputs.container = 'subject'
        >>> ds.inputs.structural = 'structural.nii'
        >>> setattr(ds.inputs, 'contrasts.@con', ['cont1.nii', 'cont2.nii'])
        >>> setattr(ds.inputs, 'contrasts.alt', ['cont1a.nii', 'cont2a.nii'])
        >>> ds.run() # doctest: +SKIP

        To use DataSink in a MapNode, its inputs have to be defined at the
        time the interface is created.

        >>> ds = DataSink(infields=['contasts.@con'])
        >>> ds.inputs.base_directory = 'results_dir'
        >>> ds.inputs.container = 'subject'
        >>> ds.inputs.structural = 'structural.nii'
        >>> setattr(ds.inputs, 'contrasts.@con', ['cont1.nii', 'cont2.nii'])
        >>> setattr(ds.inputs, 'contrasts.alt', ['cont1a.nii', 'cont2a.nii'])
        >>> ds.run() # doctest: +SKIP

    """
    input_spec = DataSinkInputSpec

    def __init__(self, infields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created
        """

        super(DataSink, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                self.inputs._outputs[key] = Undefined
                undefined_traits[key] = Undefined
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _get_dst(self, src):
        ## If path is directory with trailing os.path.sep,
        ## then remove that for a more robust behavior
        src = src.rstrip(os.path.sep)
        path, fname = os.path.split(src)
        if self.inputs.parameterization:
            dst = path
            if isdefined(self.inputs.strip_dir):
                dst = dst.replace(self.inputs.strip_dir, '')
            folders = [folder for folder in dst.split(os.path.sep) if
                       folder.startswith('_')]
            dst = os.path.sep.join(folders)
            if fname:
                dst = os.path.join(dst, fname)
        else:
            if fname:
                dst = fname
            else:
                dst = path.split(os.path.sep)[-1]
        if dst[0] == os.path.sep:
            dst = dst[1:]
        return dst

    def _substitute(self, pathstr):
        pathstr_ = pathstr
        if isdefined(self.inputs.substitutions):
            for key, val in self.inputs.substitutions:
                oldpathstr = pathstr
                pathstr = pathstr.replace(key, val)
                if pathstr != oldpathstr:
                    iflogger.debug('sub.str: %s -> %s using %r -> %r'
                                   % (oldpathstr, pathstr, key, val))
        if isdefined(self.inputs.regexp_substitutions):
            for key, val in self.inputs.regexp_substitutions:
                oldpathstr = pathstr
                pathstr, _ = re.subn(key, val, pathstr)
                if pathstr != oldpathstr:
                    iflogger.debug('sub.regexp: %s -> %s using %r -> %r'
                                   % (oldpathstr, pathstr, key, val))
        if pathstr_ != pathstr:
            iflogger.info('sub: %s -> %s' % (pathstr_, pathstr))
        return pathstr

    def _list_outputs(self):
        """Execute this module.
        """
        outdir = self.inputs.base_directory
        if not isdefined(outdir):
            outdir = '.'
        outdir = os.path.abspath(outdir)
        if isdefined(self.inputs.container):
            outdir = os.path.join(outdir, self.inputs.container)
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except OSError, inst:
                if 'File exists' in inst:
                    pass
                else:
                    raise(inst)
        for key, files in self.inputs._outputs.items():
            if not isdefined(files):
                continue
            iflogger.debug("key: %s files: %s"%(key, str(files)))
            files = filename_to_list(files)
            tempoutdir = outdir
            for d in key.split('.'):
                if d[0] == '@':
                    continue
                tempoutdir = os.path.join(tempoutdir,d)

            # flattening list
            if isinstance(files, list):
                if isinstance(files[0], list):
                    files = [item for sublist in files for item in sublist]

            for src in filename_to_list(files):
                src = os.path.abspath(src)
                if os.path.isfile(src):
                    dst = self._get_dst(src)
                    dst = os.path.join(tempoutdir, dst)
                    dst = self._substitute(dst)
                    path,_ = os.path.split(dst)
                    if not os.path.exists(path):
                        try:
                            os.makedirs(path)
                        except OSError, inst:
                            if 'File exists' in inst:
                                pass
                            else:
                                raise(inst)
                    iflogger.debug("copyfile: %s %s"%(src, dst))
                    copyfile(src, dst, copy=True, hashmethod='content')
                elif os.path.isdir(src):
                    dst = self._get_dst(os.path.join(src,''))
                    dst = os.path.join(tempoutdir, dst)
                    dst = self._substitute(dst)
                    path,_ = os.path.split(dst)
                    if not os.path.exists(path):
                        try:
                            os.makedirs(path)
                        except OSError, inst:
                            if 'File exists' in inst:
                                pass
                            else:
                                raise(inst)
                    if os.path.exists(dst) and self.inputs.remove_dest_dir:
                        iflogger.debug("removing: %s"%dst)
                        shutil.rmtree(dst)
                    iflogger.debug("copydir: %s %s"%(src, dst))
                    copytree(src, dst)
        return None


class DataGrabberInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec): #InterfaceInputSpec):
    base_directory = Directory(exists=True,
            desc='Path to the base directory consisting of subject data.')
    raise_on_empty = traits.Bool(True, usedefault=True,
                          desc='Generate exception if list is empty for a given field')
    sort_filelist = traits.Bool(False, usedefault=True,
                        desc='Sort the filelist that matches the template')
    template = traits.Str(mandatory=True,
             desc='Layout used to get files. relative to base directory if defined')
    template_args = traits.Dict(key_trait=traits.Str,
                                value_trait= traits.List(traits.List),
                                desc='Information to plug into template')

class DataGrabber(IOBase):
    """ Generic datagrabber module that wraps around glob in an
        intelligent way for neuroimaging tasks to grab files


        .. attention::

           Doesn't support directories currently

        Examples
        --------

        >>> from nipype.interfaces.io import DataGrabber

        Pick all files from current directory

        >>> dg = DataGrabber()
        >>> dg.inputs.template = '*'

        Pick file foo/foo.nii from current directory

        >>> dg.inputs.template = '%s/%s.dcm'
        >>> dg.inputs.template_args['outfiles']=[['dicomdir','123456-1-1.dcm']]

        Same thing but with dynamically created fields

        >>> dg = DataGrabber(infields=['arg1','arg2'])
        >>> dg.inputs.template = '%s/%s.nii'
        >>> dg.inputs.arg1 = 'foo'
        >>> dg.inputs.arg2 = 'foo'

        however this latter form can be used with iterables and iterfield in a
        pipeline.

        Dynamically created, user-defined input and output fields

        >>> dg = DataGrabber(infields=['sid'], outfields=['func','struct','ref'])
        >>> dg.inputs.base_directory = '.'
        >>> dg.inputs.template = '%s/%s.nii'
        >>> dg.inputs.template_args['func'] = [['sid',['f3','f5']]]
        >>> dg.inputs.template_args['struct'] = [['sid',['struct']]]
        >>> dg.inputs.template_args['ref'] = [['sid','ref']]
        >>> dg.inputs.sid = 's1'

        Change the template only for output field struct. The rest use the
        general template

        >>> dg.inputs.field_template = dict(struct='%s/struct.nii')
        >>> dg.inputs.template_args['struct'] = [['sid']]

    """
    input_spec = DataGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created

        See class examples for usage

        """
        if not outfields:
            outfields = ['outfiles']
        super(DataGrabber, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                undefined_traits[key] = Undefined
        # add ability to insert field specific templates
        self.inputs.add_trait('field_template',
                              traits.Dict(traits.Enum(outfields),
                                desc="arguments that fit into template"))
        undefined_traits['field_template'] = Undefined
        if not isdefined(self.inputs.template_args):
            self.inputs.template_args = {}
        for key in outfields:
            if not key in self.inputs.template_args:
                if infields:
                    self.inputs.template_args[key] = [infields]
                else:
                    self.inputs.template_args[key] = []

        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _add_output_traits(self, base):
        """

        Using traits.Any instead out OutputMultiPath till add_trait bug
        is fixed.
        """
        return add_traits(base, self.inputs.template_args.keys())

    def _list_outputs(self):
        # infields are mandatory, however I could not figure out how to set 'mandatory' flag dynamically
        # hence manual check
        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs,key)
                if not isdefined(value):
                    msg = "%s requires a value for input '%s' because it was listed in 'infields'" % \
                    (self.__class__.__name__, key)
                    raise ValueError(msg)

        outputs = {}
        for key, args in self.inputs.template_args.items():
            outputs[key] = []
            template = self.inputs.template
            if hasattr(self.inputs, 'field_template') and \
                    isdefined(self.inputs.field_template) and \
                    self.inputs.field_template.has_key(key):
                template = self.inputs.field_template[key]
            if isdefined(self.inputs.base_directory):
                template = os.path.join(os.path.abspath(self.inputs.base_directory), template)
            else:
                template = os.path.abspath(template)
            if not args:
                filelist = glob.glob(template)
                if len(filelist) == 0:
                    msg = 'Output key: %s Template: %s returned no files'%(key, template)
                    if self.inputs.raise_on_empty:
                        raise IOError(msg)
                    else:
                        warn(msg)
                else:
                    if self.inputs.sort_filelist:
                        filelist.sort()
                    outputs[key] = list_to_filename(filelist)
            for argnum, arglist in enumerate(args):
                maxlen = 1
                for arg in arglist:
                    if isinstance(arg, str) and hasattr(self.inputs, arg):
                        arg = getattr(self.inputs, arg)
                    if isinstance(arg, list):
                        if (maxlen > 1) and (len(arg) != maxlen):
                            raise ValueError('incompatible number of arguments for %s' % key)
                        if len(arg)>maxlen:
                            maxlen = len(arg)
                outfiles = []
                for i in range(maxlen):
                    argtuple = []
                    for arg in arglist:
                        if isinstance(arg, str) and hasattr(self.inputs, arg):
                            arg = getattr(self.inputs, arg)
                        if isinstance(arg, list):
                            argtuple.append(arg[i])
                        else:
                            argtuple.append(arg)
                    filledtemplate = template
                    if argtuple:
                        filledtemplate = template%tuple(argtuple)
                    outfiles = glob.glob(filledtemplate)
                    if len(outfiles) == 0:
                        msg = 'Output key: %s Template: %s returned no files'%(key, filledtemplate)
                        if self.inputs.raise_on_empty:
                            raise IOError(msg)
                        else:
                            warn(msg)
                        outputs[key].insert(i, None)
                    else:
                        if self.inputs.sort_filelist:
                            outfiles.sort()
                        outputs[key].insert(i,list_to_filename(outfiles))
            if any([val==None for val in outputs[key]]):
                outputs[key] = []
            if len(outputs[key]) == 0:
                outputs[key] = None
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]
        return outputs


class FSSourceInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(mandatory=True,
                             desc='Freesurfer subjects directory.')
    subject_id = traits.Str(mandatory=True,
                            desc='Subject name for whom to retrieve data')
    hemi = traits.Enum('both', 'lh', 'rh', usedefault=True,
                       desc='Selects hemisphere specific outputs')

class FSSourceOutputSpec(TraitedSpec):
    T1 = File(exists=True, desc='Intensity normalized whole-head volume', loc='mri')
    aseg = File(exists=True, desc='Volumetric map of regions from automatic segmentation',
                loc='mri')
    brain = File(exists=True, desc='Intensity normalized brain-only volume', loc='mri')
    brainmask = File(exists=True, desc='Skull-stripped (brain-only) volume', loc='mri')
    filled = File(exists=True, desc='Subcortical mass volume', loc='mri')
    norm = File(exists=True, desc='Normalized skull-stripped volume', loc='mri')
    nu = File(exists=True, desc='Non-uniformity corrected whole-head volume', loc='mri')
    orig = File(exists=True, desc='Base image conformed to Freesurfer space',
                loc='mri')
    rawavg = File(exists=True, desc='Volume formed by averaging input images',
                  loc='mri')
    ribbon = OutputMultiPath(File(exists=True), desc='Volumetric maps of cortical ribbons',
                             loc='mri', altkey='*ribbon')
    wm = File(exists=True, desc='Segmented white-matter volume', loc='mri')
    wmparc = File(exists=True, desc='Aparc parcellation projected into subcortical white matter',
                  loc='mri')
    curv = OutputMultiPath(File(exists=True), desc='Maps of surface curvature',
                     loc='surf')
    inflated = OutputMultiPath(File(exists=True), desc='Inflated surface meshes',
                         loc='surf')
    pial = OutputMultiPath(File(exists=True), desc='Gray matter/pia mater surface meshes',
                           loc='surf')
    smoothwm = OutputMultiPath(File(exists=True), loc='surf',
                         desc='Smoothed original surface meshes')
    sphere = OutputMultiPath(File(exists=True), desc='Spherical surface meshes',
                       loc='surf')
    sulc = OutputMultiPath(File(exists=True), desc='Surface maps of sulcal depth', loc='surf')
    thickness = OutputMultiPath(File(exists=True), loc='surf',
                          desc='Surface maps of cortical thickness')
    volume = OutputMultiPath(File(exists=True), desc='Surface maps of cortical volume', loc='surf')
    white = OutputMultiPath(File(exists=True), desc='White/gray matter surface meshes',
                      loc='surf')
    label = OutputMultiPath(File(exists=True), desc='Volume and surface label files',
                      loc='label', altkey='*label')
    annot = OutputMultiPath(File(exists=True), desc='Surface annotation files',
                      loc='label', altkey='*annot')
    aparc_aseg = OutputMultiPath(File(exists=True), loc='mri', altkey='aparc*aseg',
                           desc='Aparc parcellation projected into aseg volume')
    sphere_reg = OutputMultiPath(File(exists=True), loc='surf', altkey='sphere.reg',
                           desc='Spherical registration file')
    aseg_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='aseg',
                           desc='Automated segmentation statistics file')
    wmparc_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='wmparc',
                           desc='White matter parcellation statistics file')
    aparc_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='aparc',
                           desc='Aparc parcellation statistics files')
    BA_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='BA',
                           desc='Brodmann Area statistics files')
    aparc_a2009s_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='aparc.a2009s',
                           desc='Aparc a2009s parcellation statistics files')
    curv_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='curv',
                           desc='Curvature statistics files')
    entorhinal_exvivo_stats = OutputMultiPath(File(exists=True), loc='stats', altkey='entorhinal_exvivo',
                           desc='Entorhinal exvivo statistics files')

class FreeSurferSource(IOBase):
    """Generates freesurfer subject info from their directories

    Examples
    --------

    >>> from nipype.interfaces.io import FreeSurferSource
    >>> fs = FreeSurferSource()
    >>> #fs.inputs.subjects_dir = '.'
    >>> fs.inputs.subject_id = 'PWS04'
    >>> res = fs.run() # doctest: +SKIP

    >>> fs.inputs.hemi = 'lh'
    >>> res = fs.run() # doctest: +SKIP

    """
    input_spec = FSSourceInputSpec
    output_spec = FSSourceOutputSpec
    _always_run = True

    def _get_files(self, path, key, dirval, altkey=None):
        globsuffix = ''
        if dirval == 'mri':
            globsuffix = '.mgz'
        elif dirval == 'stats':
            globsuffix = '.stats'
        globprefix = ''
        if key == 'ribbon' or dirval in ['surf', 'label', 'stats']:
            if self.inputs.hemi != 'both':
                globprefix = self.inputs.hemi+'.'
            else:
                globprefix = '*'
        if key == 'aseg_stats' or key == 'wmparc_stats':
			globprefix = ''
        keydir = os.path.join(path,dirval)
        if altkey:
            key = altkey
        globpattern = os.path.join(keydir,''.join((globprefix,key,globsuffix)))
        return glob.glob(globpattern)

    def _list_outputs(self):
        subjects_dir = self.inputs.subjects_dir
        subject_path = os.path.join(subjects_dir, self.inputs.subject_id)
        output_traits = self._outputs()
        outputs = output_traits.get()
        for k in outputs.keys():
            val = self._get_files(subject_path, k,
                                  output_traits.traits()[k].loc,
                                  output_traits.traits()[k].altkey)
            if val:
                outputs[k] = list_to_filename(val)
        return outputs




class XNATSourceInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):

    query_template = traits.Str(
        mandatory=True,
        desc=('Layout used to get files. Relative to base '
              'directory if defined')
        )

    query_template_args = traits.Dict(
        traits.Str,
        traits.List(traits.List),
        value=dict(outfiles=[]), usedefault=True,
        desc='Information to plug into template'
        )

    server = traits.Str(
        mandatory=True,
        requires=['user', 'pwd'],
        xor=['config']
        )

    user = traits.Str()
    pwd = traits.Password()
    config = File(mandatory=True, xor=['server'])

    cache_dir = Directory(desc='Cache directory')


class XNATSource(IOBase):
    """ Generic XNATSource module that wraps around the pyxnat module in
        an intelligent way for neuroimaging tasks to grab files and data
        from an XNAT server.

        Examples
        --------

        >>> from nipype.interfaces.io import XNATSource

        Pick all files from current directory

        >>> dg = XNATSource()
        >>> dg.inputs.template = '*'

        >>> dg = XNATSource(infields=['project','subject','experiment','assessor','inout'])
        >>> dg.inputs.query_template = '/projects/%s/subjects/%s/experiments/%s' \
                   '/assessors/%s/%s_resources/files'
        >>> dg.inputs.project = 'IMAGEN'
        >>> dg.inputs.subject = 'IMAGEN_000000001274'
        >>> dg.inputs.experiment = '*SessionA*'
        >>> dg.inputs.assessor = '*ADNI_MPRAGE_nii'
        >>> dg.inputs.inout = 'out'

        >>> dg = XNATSource(infields=['sid'],outfields=['struct','func'])
        >>> dg.inputs.query_template = '/projects/IMAGEN/subjects/%s/experiments/*SessionA*' \
                   '/assessors/*%s_nii/out_resources/files'
        >>> dg.inputs.query_template_args['struct'] = [['sid','ADNI_MPRAGE']]
        >>> dg.inputs.query_template_args['func'] = [['sid','EPI_faces']]
        >>> dg.inputs.sid = 'IMAGEN_000000001274'


    """
    input_spec = XNATSourceInputSpec
    output_spec = DynamicTraitedSpec

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created

        See class examples for usage

        """
        super(XNATSource, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                undefined_traits[key] = Undefined
            self.inputs.query_template_args['outfiles'] = [infields]
        if outfields:
            # add ability to insert field specific templates
            self.inputs.add_trait(
                'field_template',
                traits.Dict(traits.Enum(outfields),
                            desc="arguments that fit into query_template")
                )
            undefined_traits['field_template'] = Undefined
            #self.inputs.remove_trait('query_template_args')
            outdict = {}
            for key in outfields:
                outdict[key] = []
            self.inputs.query_template_args =  outdict
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _add_output_traits(self, base):
        """

        Using traits.Any instead out OutputMultiPath till add_trait bug
        is fixed.
        """
        return add_traits(base, self.inputs.query_template_args.keys())

    def _list_outputs(self):
        # infields are mandatory, however I could not figure out
        # how to set 'mandatory' flag dynamically, hence manual check

        cache_dir = self.inputs.cache_dir or tempfile.gettempdir()

        if self.inputs.config:
            xnat = pyxnat.Interface(config=self.inputs.config)
        else:
            xnat = pyxnat.Interface(self.inputs.server,
                                    self.inputs.user,
                                    self.inputs.pwd,
                                    cache_dir
                                    )

        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs,key)
                if not isdefined(value):
                    msg = ("%s requires a value for input '%s' "
                           "because it was listed in 'infields'" % \
                               (self.__class__.__name__, key)
                           )
                    raise ValueError(msg)

        outputs = {}
        for key, args in self.inputs.query_template_args.items():
            outputs[key] = []
            template = self.inputs.query_template
            if hasattr(self.inputs, 'field_template') and \
                    isdefined(self.inputs.field_template) and \
                    self.inputs.field_template.has_key(key):
                template = self.inputs.field_template[key]
            if not args:
                file_objects = xnat.select(template).get('obj')
                if file_objects == []:
                    raise IOError('Template %s returned no files' \
                                      % template
                                  )
                outputs[key] = list_to_filename(
                                        [str(file_object.get())
                                         for file_object in file_objects
                                         if file_object.exists()
                                        ])
            for argnum, arglist in enumerate(args):
                maxlen = 1
                for arg in arglist:
                    if isinstance(arg, str) and hasattr(self.inputs, arg):
                        arg = getattr(self.inputs, arg)
                    if isinstance(arg, list):
                        if (maxlen > 1) and (len(arg) != maxlen):
                            raise ValueError('incompatible number '
                                             'of arguments for %s' % key
                                             )
                        if len(arg)>maxlen:
                            maxlen = len(arg)
                outfiles = []
                for i in range(maxlen):
                    argtuple = []
                    for arg in arglist:
                        if isinstance(arg, str) and \
                                hasattr(self.inputs, arg):
                            arg = getattr(self.inputs, arg)
                        if isinstance(arg, list):
                            argtuple.append(arg[i])
                        else:
                            argtuple.append(arg)
                    if argtuple:
                        target = template % tuple(argtuple)
                        file_objects = xnat.select(target).get('obj')

                        if file_objects == []:
                            raise IOError('Template %s '
                                          'returned no files' % target
                                          )

                        outfiles = list_to_filename(
                            [str(file_object.get())
                             for file_object in file_objects
                             if file_object.exists()
                             ]
                            )
                    else:
                        file_objects = xnat.select(template).get('obj')

                        if file_objects == []:
                            raise IOError('Template %s '
                                          'returned no files' % template
                                          )

                        outfiles = list_to_filename(
                            [str(file_object.get())
                             for file_object in file_objects
                             if file_object.exists()
                             ]
                            )

                    outputs[key].insert(i,outfiles)
            if len(outputs[key]) == 0:
                outputs[key] = None
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]
        return outputs


class XNATSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):

    _outputs = traits.Dict(traits.Str, value={}, usedefault=True)

    server = traits.Str(mandatory=True,
                        requires=['user', 'pwd'],
                        xor=['config']
                        )

    user = traits.Str()
    pwd = traits.Password()
    config = File(mandatory=True, xor=['server'])
    cache_dir = Directory(desc='')

    project_id = traits.Str(
        desc='Project in which to store the outputs', mandatory=True)

    subject_id = traits.Str(
        desc='Set to subject id', mandatory=True)

    experiment_id = traits.Str(
        desc='Set to workflow name', mandatory=True)

    assessor_id = traits.Str(
        desc=('Option to customize ouputs representation in XNAT - '
              'assessor level will be used with specified id'),
        mandatory=False,
        xor=['reconstruction_id']
        )

    reconstruction_id = traits.Str(
        desc=('Option to customize ouputs representation in XNAT - '
              'reconstruction level will be used with specified id'),
        mandatory=False,
        xor=['assessor_id']
        )

    share = traits.Bool(
        desc=('Option to share the subjects from the original project'
              'instead of creating new ones when possible - the created '
              'experiments are then shared backk to the original project'
              ),
        value=False,
        usedefault=True,
        mandatory=False,
        )

    def __setattr__(self, key, value):
        if key not in self.copyable_trait_names():
            self._outputs[key] = value
        else:
            super(XNATSinkInputSpec, self).__setattr__(key, value)


class XNATSink(IOBase):
    """ Generic datasink module that takes a directory containing a
        list of nifti files and provides a set of structured output
        fields.
    """
    input_spec = XNATSinkInputSpec

    def _list_outputs(self):
        """Execute this module.
        """

        # setup XNAT connection
        cache_dir = self.inputs.cache_dir or tempfile.gettempdir()

        if self.inputs.config:
            xnat = pyxnat.Interface(config=self.inputs.config)
        else:
            xnat = pyxnat.Interface(self.inputs.server,
                                    self.inputs.user,
                                    self.inputs.pwd,
                                    cache_dir
                                    )

        # if possible share the subject from the original project
        if self.inputs.share:
            result = xnat.select(
                'xnat:subjectData',
                ['xnat:subjectData/PROJECT',
                 'xnat:subjectData/SUBJECT_ID']
                ).where('xnat:subjectData/SUBJECT_ID = %s AND' %
                        self.inputs.subject_id
                        )

            subject_id = self.inputs.subject_id

            # subject containing raw data exists on the server
            if isinstance(result.data[0], dict):
                result = result.data[0]

                shared = xnat.select('/project/%s/subject/%s' %
                                     (self.inputs.project_id,
                                      self.inputs.subject_id
                                      )
                                     )

                if not shared.exists(): # subject not in share project

                    share_project = xnat.select(
                        '/project/%s' % self.inputs.project_id)

                    if not share_project.exists(): # check project exists
                        share_project.insert()

                    subject = xnat.select('/project/%(project)s'
                                          '/subject/%(subject_id)s' % result
                                          )

                    subject.share(str(self.inputs.project_id))

        else:
            # subject containing raw data does not exist on the server
            subject_id = '%s_%s' % (
                quote_id(self.inputs.project_id),
                quote_id(self.inputs.subject_id)
                )

        # setup XNAT resource
        uri_template_args = {
            'project_id':quote_id(self.inputs.project_id),
            'subject_id':subject_id,
            'experiment_id': '%s_%s_%s' % (
                quote_id(self.inputs.project_id),
                quote_id(self.inputs.subject_id),
                quote_id(self.inputs.experiment_id)
                )
            }

        if self.inputs.share:
            uri_template_args['original_project'] = result['project']

        if self.inputs.assessor_id:
            uri_template_args['assessor_id'] = (
                '%s_%s' % (
                    uri_template_args['experiment_id'],
                    quote_id(self.inputs.assessor_id)
                    )
                )

        elif self.inputs.reconstruction_id:
            uri_template_args['reconstruction_id'] = (
                '%s_%s' % (
                    uri_template_args['experiment_id'],
                    quote_id(self.inputs.reconstruction_id)
                    )
                )

        # gather outputs and upload them
        for key, files in self.inputs._outputs.items():

            for name in filename_to_list(files):

                if isinstance(name, list):
                    for i, file_name in enumerate(name):
                        push_file(self, xnat, file_name,
                                  '%s_' % i + key,
                                  uri_template_args
                                  )
                else:
                    push_file(self, xnat, name, key, uri_template_args)


def quote_id(string):
    return str(string).replace('_', '---')

def unquote_id(string):
    return str(string).replace('---', '_')

def push_file(self, xnat, file_name, out_key, uri_template_args):

    # grab info from output file names
    val_list = [unquote_id(val)
                for part in os.path.split(file_name)[0].split(os.sep)
                for val in part.split('_')[1:]
                if part.startswith('_') and len(part.split('_')) % 2
                ]

    keymap = dict(zip(val_list[1::2],val_list[2::2]))

    _label = []
    for key, val in sorted(keymap.items()):
        if str(self.inputs.subject_id) not in val:
            _label.extend([key, val])

    # select and define container level
    uri_template_args['container_type'] = None

    for container in ['assessor_id', 'reconstruction_id']:
        if getattr(self.inputs, container):
            uri_template_args['container_type'] = container.split('_id')[0]
            uri_template_args['container_id'] = uri_template_args[container]

    if uri_template_args['container_type'] is None:
        uri_template_args['container_type'] = 'reconstruction'

        uri_template_args['container_id'] = unquote_id(
            uri_template_args['experiment_id']
            )

        if _label:
            uri_template_args['container_id'] += (
                '_results_%s' % '_'.join(_label)
                )
        else:
            uri_template_args['container_id'] += '_results'

    # define resource level
    uri_template_args['resource_label'] = (
        '%s_%s' % (uri_template_args['container_id'],
                   out_key.split('.')[0]
                   )
        )

    # define file level
    uri_template_args['file_name'] = os.path.split(
        os.path.abspath(unquote_id(file_name)))[1]

    uri_template = (
        '/project/%(project_id)s/subject/%(subject_id)s'
        '/experiment/%(experiment_id)s/%(container_type)s/%(container_id)s'
        '/out/resource/%(resource_label)s/file/%(file_name)s'
        )

    # unquote values before uploading
    for key in uri_template_args.keys():
        uri_template_args[key] = unquote_id(uri_template_args[key])

    # upload file
    remote_file = xnat.select(uri_template % uri_template_args)
    remote_file.insert(file_name,
                       experiments='xnat:imageSessionData',
                       use_label=True
                       )

    # shares the experiment back to the original project if relevant
    if uri_template_args.has_key('original_project'):

        experiment_template = (
            '/project/%(original_project)s'
            '/subject/%(subject_id)s/experiment/%(experiment_id)s'
            )

        xnat.select(experiment_template % uri_template_args
                    ).share(uri_template_args['original_project'])

def capture_provenance():
    pass

def push_provenance():
    pass


class SQLiteSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    database_file = File(exists=True, mandatory = True)
    table_name = traits.Str(mandatory=True)

class SQLiteSink(IOBase):
    """ Very simple frontend for storing values into SQLite database.

        .. warning::

            This is not a thread-safe node because it can write to a common
            shared location. It will not complain when it overwrites a file.

        Examples
        --------

        >>> sql = SQLiteSink(input_names=['subject_id', 'some_measurement'])
        >>> sql.inputs.database_file = 'my_database.db'
        >>> sql.inputs.table_name = 'experiment_results'
        >>> sql.inputs.subject_id = 's1'
        >>> sql.inputs.some_measurement = 11.4
        >>> sql.run() # doctest: +SKIP

    """
    input_spec = SQLiteSinkInputSpec

    def __init__(self, input_names, **inputs):

        super(SQLiteSink, self).__init__(**inputs)

        self._input_names = filename_to_list(input_names)
        add_traits(self.inputs, [name for name in self._input_names])

    def _list_outputs(self):
        """Execute this module.
        """
        conn = sqlite3.connect(self.inputs.database_file,
                               check_same_thread = False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO %s (" % self.inputs.table_name +
                  ",".join(self._input_names) + ") VALUES (" +
                  ",".join(["?"]*len(self._input_names)) + ")",
                  [getattr(self.inputs,name) for name in self._input_names])
        conn.commit()
        c.close()
        return None


class MySQLSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    host = traits.Str('localhost', mandatory=True,
                      requires=['username', 'password'],
                      xor=['config'], usedefault=True)
    config = File(mandatory=True, xor=['host'], desc="MySQL Options File (same format as my.cnf)")
    database_name = traits.Str(mandatory=True, desc='Otherwise known as the schema name')
    table_name = traits.Str(mandatory=True)
    username = traits.Str()
    password = traits.Str()


class MySQLSink(IOBase):
    """ Very simple frontend for storing values into MySQL database.

        Examples
        --------

        >>> sql = MySQLSink(input_names=['subject_id', 'some_measurement'])
        >>> sql.inputs.database_name = 'my_database'
        >>> sql.inputs.table_name = 'experiment_results'
        >>> sql.inputs.username = 'root'
        >>> sql.inputs.password = 'secret'
        >>> sql.inputs.subject_id = 's1'
        >>> sql.inputs.some_measurement = 11.4
        >>> sql.run() # doctest: +SKIP

    """
    input_spec = MySQLSinkInputSpec

    def __init__(self, input_names, **inputs):

        super(MySQLSink, self).__init__(**inputs)

        self._input_names = filename_to_list(input_names)
        add_traits(self.inputs, [name for name in self._input_names])

    def _list_outputs(self):
        """Execute this module.
        """
        import MySQLdb
        if isdefined(self.inputs.config):
            conn = MySQLdb.connect(db=self.inputs.database_name,
                                   read_default_file=self.inputs.config)
        else:
            conn = MySQLdb.connect(host=self.inputs.host,
                                   user=self.inputs.username,
                                   passwd=self.inputs.password,
                                   db=self.inputs.database_name)
        c = conn.cursor()
        c.execute("REPLACE INTO %s (" % self.inputs.table_name +
                  ",".join(self._input_names) + ") VALUES (" +
                  ",".join(["%s"] * len(self._input_names)) + ")",
                  [getattr(self.inputs, name) for name in self._input_names])
        conn.commit()
        c.close()
        return None
