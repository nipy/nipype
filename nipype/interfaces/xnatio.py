""" Set of interfaces that allow interaction with data. Currently
    available interfaces are:

    DataSource: Generic nifti to named Nifti interface
    DataSink: Generic named output from interfaces to data store

    To come :
    XNATSource, XNATSink

"""
from copy import deepcopy
import glob
import os
import shutil

from enthought.traits.trait_errors import TraitError
from xnatlib import Interface as XNATInterface

from nipype.interfaces.base import (Interface, CommandLine, Bunch,
                                    InterfaceResult, Interface,
                                    TraitedSpec, traits, File, Directory,
                                    BaseInterface,
                                    OutputMultiPath, DynamicTraitedSpec,
                                    BaseTraitedSpec, Undefined)
from nipype.utils.misc import isdefined
from nipype.utils.filemanip import (copyfile, list_to_filename, load_json,
                                    filename_to_list, FileNotFoundError)

from nipype.interfaces.io import (add_traits, IOBase)

class XNATSourceInputSpec(DynamicTraitedSpec): #InterfaceInputSpec):
    config_file = File(exists=True, mandatory=True,
                        desc='config file containing xnat access info')
    query_template = traits.Str(mandatory=True,
             desc='Layout used to get files. relative to base directory if defined')
    query_template_args = traits.Dict(traits.Str,
                                traits.List(traits.List),
                                value=dict(outfiles=[]), usedefault=True,
                                desc='Information to plug into template')

class XNATSource(IOBase):
    """ Generic XNATSource module that wraps around glob in an
        intelligent way for neuroimaging tasks to grab files

        Doesn't support directories currently

        Examples
        --------
        >>> from nipype.interfaces.io import XNATSource

        Pick all files from current directory
        >>> dg = XNATSource()
        >>> dg.inputs.template = '*'

        Pick file foo/foo.nii from current directory
        >>> dg.inputs.template = '%s/%s.nii'
        >>> dg.inputs.template_args['outfiles']=[['foo','foo']]

        Same thing but with dynamically created fields
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
            self.inputs.add_trait('field_template',
                                  traits.Dict(traits.Enum(outfields),
                                    desc="arguments that fit into query_template"))
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
        # infields are mandatory, however I could not figure out how to set 'mandatory' flag dynamically
        # hence manual check
        config_info = load_json(self.inputs.config_file)
        cwd = os.getcwd()
        xnat = XNATInterface(config_info['url'], config_info['username'], config_info['password'], cachedir=cwd)
        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs,key)
                if not isdefined(value):
                    msg = "%s requires a value for input '%s' because it was listed in 'infields'" % \
                    (self.__class__.__name__, key)
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
                file_objects = xnat.select(template).request_objects()
                if file_objects == []:
                    raise IOError('Template %s returned no files'%template)
                outputs[key] = list_to_filename([str(file_object.get()) for file_object in file_objects])
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
                    if argtuple:
                        file_objects = xnat.select(template%tuple(argtuple)).request_objects()
                        if file_objects == []:
                            raise IOError('Template %s returned no files'%(template%tuple(argtuple)))
                        outfiles = list_to_filename([str(file_object.get()) for file_object in file_objects])
                    else:
                        file_objects = xnat.select(template).request_objects()
                        if file_objects == []:
                            raise IOError('Template %s returned no files'%template)
                        outfiles = list_to_filename([str(file_object.get()) for file_object in file_objects])
                    outputs[key].insert(i,outfiles)
            if len(outputs[key]) == 0:
                outputs[key] = None
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]
        return outputs


class FSSourceInputSpec(TraitedSpec):
    subjects_dir = Directory(mandatory=True,
                             desc='Freesurfer subjects directory.')
    subject_id = traits.Str(mandatory=True,
                            desc='Subject name for whom to retrieve data')
    hemi = traits.Enum('both', 'lh', 'rh', usedefault=True,
                       desc='Selects hemisphere specific outputs')

class FSSourceOutputSpec(TraitedSpec):
    T1 = File(exists=True, desc='T1 image', loc='mri')
    aseg = File(exists=True, desc='Auto-seg image', loc='mri')
    brain = File(exists=True, desc='brain only image', loc='mri')
    brainmask = File(exists=True, desc='brain binary mask', loc='mri')
    filled = File(exists=True, desc='?', loc='mri')
    norm = File(exists=True, desc='intensity normalized image', loc='mri')
    nu = File(exists=True, desc='?', loc='mri')
    orig = File(exists=True, desc='original image conformed to FS space',
                loc='mri')
    rawavg = File(exists=True, desc='averaged input images to recon-all',
                  loc='mri')
    ribbon = OutputMultiPath(File(exists=True), desc='cortical ribbon', loc='mri',
                       altkey='*ribbon')
    wm = File(exists=True, desc='white matter image', loc='mri')
    wmparc = File(exists=True, desc='white matter parcellation', loc='mri')
    curv = OutputMultiPath(File(exists=True), desc='surface curvature files',
                     loc='surf')
    inflated = OutputMultiPath(File(exists=True), desc='inflated surface meshes',
                         loc='surf')
    pial = OutputMultiPath(File(exists=True), desc='pial surface meshes', loc='surf')
    smoothwm = OutputMultiPath(File(exists=True), loc='surf',
                         desc='smooth white-matter surface meshes')
    sphere = OutputMultiPath(File(exists=True), desc='spherical surface meshes',
                       loc='surf')
    sulc = OutputMultiPath(File(exists=True), desc='surface sulci files', loc='surf')
    thickness = OutputMultiPath(File(exists=True), loc='surf',
                          desc='surface thickness files')
    volume = OutputMultiPath(File(exists=True), desc='surface volume files', loc='surf')
    white = OutputMultiPath(File(exists=True), desc='white matter surface meshes',
                      loc='surf')
    label = OutputMultiPath(File(exists=True), desc='volume and surface label files',
                      loc='label', altkey='*label')
    annot = OutputMultiPath(File(exists=True), desc='surface annotation files',
                      loc='label', altkey='*annot')
    aparc_aseg = OutputMultiPath(File(exists=True), loc='mri', altkey='aparc*aseg',
                           desc='aparc+aseg file')
    sphere_reg = OutputMultiPath(File(exists=True), loc='surf', altkey='sphere.reg',
                           desc='spherical registration file')

class FreeSurferSource(IOBase):
    """Generates freesurfer subject info from their directories

    Examples
    --------

    >>> from nipype.interfaces.io import FreeSurferSource
    >>> fs = FreeSurferSource()
    >>> #fs.inputs.subjects_dir = '/software/data/STUT/FSDATA/'
    >>> fs.inputs.subject_id = 'PWS04'
    >>> res = fs.run()

    >>> fs.inputs.hemi = 'lh'
    >>> res = fs.run()

    """
    input_spec = FSSourceInputSpec
    output_spec = FSSourceOutputSpec

    def _get_files(self, path, key, dirval, altkey=None):
        globsuffix = ''
        if dirval == 'mri':
            globsuffix = '.mgz'
        globprefix = ''
        if key == 'ribbon' or dirval in ['surf', 'label']:
            if self.inputs.hemi != 'both':
                globprefix = self.inputs.hemi+'.'
            else:
                globprefix = '*'
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
        
        
        
