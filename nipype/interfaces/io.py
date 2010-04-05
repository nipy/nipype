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

from nipype.interfaces.base import Interface, CommandLine, Bunch, InterfaceResult,\
    NEW_Interface, TraitedSpec, traits, File, Directory, isdefined, BaseInterfaceInputSpec,\
    NEW_BaseInterface, MultiPath
from nipype.utils.filemanip import copyfiles, list_to_filename, filename_to_list

class IOBase(NEW_BaseInterface):

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        raise NotImplementedError

    def _outputs(self):
        return self._add_output_traits(super(IOBase, self)._outputs())
    
    def _add_output_traits(self, base):
        return base
    
class SubjectSourceInputSpec(BaseInterfaceInputSpec):
    base_directory = Directory(exists=True, mandatory=True,
            desc='Path to the base directory consisting of subject data.')
    subject_id = traits.Either(traits.Str, traits.Int, mandatory=True,
                               desc = 'subject identifier')
    file_layout = traits.Either(traits.Str, traits.DictStrStr,
                                mandatory=True,
                                desc='Layout used to get files.')
    subject_info = traits.DictStrList(mandatory=True,
                                      desc="""
            Provides information about how to map subject run
            numbers to the output fields.

            `subject_id` are keys and the values are a list of tuples.
            info[subject_id] = [([run_identifiers], output_fieldname), ...]
            """)

class SubjectSourceOutputSpec(TraitedSpec):
    subject_id = traits.Either(traits.Str, traits.Int,
                               desc = 'subject identifier')
    subject_directory = Directory(exists=True,
                                  desc='Path to the subject directory')

class SubjectSource(IOBase):
    """ Generic datasource module that takes a directory containing a
        list of nifti files and provides a set of structured output
        fields.

        Examples
        --------
     
        Here our experiment data is stored in our the directory
        '/software/data'.  In the data directory we have a subdirectory
        for our subject named 'S03'.  In the 'S03' directory we have
        four types of data. In the `info` dictionary we create an
        entry where the keys are the output fields and the value is a
        list of run numbers corresponding to the template in layout.

        >>> from nipype.interfaces.io import SubjectSource
        >>> info = dict(dti=[7], bold=[14, 16, 18], mprage=[4], fieldmap=[5,6])
        >>> ds = SubjectSource()
        >>> ds.inputs.base_directory = '/software/data'
        >>> ds.inputs.subject_id = 'S03'
        >>> ds.inputs.file_layout = 'nii/s*-%d.nii'
        >>> ds.inputs.subject_info = info
        >>> 'dti' in ds._outputs().trait_names()
        True

        We can also have a different layout per field:
        >>> ds.inputs.file_layout = dict(dti='dwiscans/*-%d.nii', bold='boldruns/*-%d.nii')
        >>> info = dict(dti=[7], bold=[14, 16, 18])
        >>> ds.inputs.subject_info = info
        
       """

    input_spec = SubjectSourceInputSpec
    output_spec = SubjectSourceOutputSpec

    def _add_output_traits(self, base):
        undefined_traits = {}
        if isdefined(self.inputs.subject_info):
            for key in self.inputs.subject_info.keys():
                base.add_trait(key, MultiPath(File(exists=True), default=traits.Undefined))
                undefined_traits[key] = traits.Undefined
            base.trait_set(trait_change_notify=False, **undefined_traits)
        return base

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['subject_id'] = self.inputs.subject_id
        subjdir = os.path.join(self.inputs.base_directory, str(self.inputs.subject_id))
        outputs['subject_directory'] = subjdir 
        for outfield, fileinfo in self.inputs.subject_info.items():
            if isinstance(self.inputs.file_layout, str):
                file_template = self.inputs.file_layout
            else:
                file_template = self.inputs.file_layout[outfield]
            files_found = []
            for val in fileinfo:
                path = os.path.abspath(os.path.join(subjdir,
                                                    file_template % val))
                files_found.extend(glob.glob(path))
            if fileinfo:
                outputs[outfield] = list_to_filename(deepcopy(files_found))
        return outputs
    
class DataSink(Interface):
    """ Generic datasink module that takes a directory containing a
        list of nifti files and provides a set of structured output
        fields.
    """
    
    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
            Parameters
            ----------
            (all default to None)

            base_directory : /path/to/dir
                Basedirectory consisting of subject data
            subject_id: string or int
                Subject identifier
            subject_directory : /path/to/dir
                Path to subject directory
            parameterization : string
                Includes parameterization for creating directory structure

            Any fields that are set as lists will be copied to a
            directory under subject_directory with the fieldname as a
            new directory.

        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(base_directory=None,
                            parameterization=None,
                            subject_directory=None,
                            subject_template=None,
                            subject_id=None)
        self.input_keys = self.inputs.__dict__.keys()

    def outputs(self):
        """
        """
        return Bunch()
    
    def outputs_help(self):
        """
            No outputs 
        """
        print self.outputs.__doc__
        
    def aggregate_outputs(self):
        return self.outputs()

    def run(self, cwd=None):
        """Execute this module.

        cwd is just there to make things work for now
        """
        subjdir = self.inputs.subject_directory
        if not subjdir:
            #print self.inputs['subj_template'],self.inputs['subj_id']
            if self.inputs.subject_template:
                subjdir = self.inputs.subject_template % (self.inputs.subject_id)
            else:
                subjdir = self.inputs.subject_id
            subjdir = os.path.join(self.inputs.base_directory,subjdir)
        if subjdir is None:
            raise Exception('Subject directory not provided')
        outdir = subjdir
        if self.inputs.parameterization:
            outdir = os.path.join(outdir,self.inputs.parameterization)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        for k,v in self.inputs.items():
            if k not in self.input_keys:
                if v is not None:
                    tempoutdir = outdir
                    for d in k.split('.'):
                        if d[0] == '@':
                            continue
                        tempoutdir = os.path.join(tempoutdir,d)
                    if not os.path.exists(tempoutdir):
                        os.makedirs(tempoutdir)
                    for src in filename_to_list(self.inputs.get(k)):
                        if os.path.isfile(src):
                            copyfiles(src,tempoutdir,copy=True)
                        elif os.path.isdir(src):
                            dirname = os.path.split(os.path.join(src,''))[0]
                            newdir = dirname.split(os.path.sep)[-1]
                            newoutdir = os.path.join(tempoutdir,newdir)
                            if os.path.exists(newoutdir):
                                shutil.rmtree(newoutdir)
                            shutil.copytree(dirname,newoutdir)
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)


class DataGrabberInputSpec(BaseInterfaceInputSpec):
    file_template = traits.Either(traits.Str(),File(), desc="template or filename")
    template_argtuple = traits.Tuple(desc="arguments that fit into file_template")
    template_argnames = traits.List(traits.Str(), desc="""provides names of inputs that will be used as
                arguments to the template.
                For example,

                dg.file_template = '%s/%s.nii'
                
                dg.template_argtuple = ('foo','foo')

                is equivalent to

                dg.inputs.arg1 = 'foo'
                dg.inputs.arg2 = 'foo'
                dg.inputs.template_argnames = ['arg1','arg2']

                however this latter form can be used with iterables
                and iterfield in a pipeline.
""")

class DataGrabberOutputSpec(TraitedSpec):
    file_list = traits.List(File(exists=True), desc='list of files picked up by the grabber')
    
class DataGrabber(NEW_BaseInterface):
    """ Generic datagrabber module that wraps around glob in an
        intelligent way for neuroimaging tasks 
    """
    input_spec = DataGrabberInputSpec
    output_spec = DataGrabberOutputSpec
    
    def _run_interface(self, runtime):
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        args = []
        if isdefined(self.inputs.template_argtuple):
            args.extend(list(self.inputs.template_argtuple))
        if isdefined(self.inputs.template_argnames):
            for name in self.inputs.template_argnames:
                arg = self.inputs.get(name)
                if arg:
                    args.append(arg)
        template = self.inputs.file_template
        if args:
            template = template%tuple(args)
        outputs['file_list'] = list_to_filename(glob.glob(template))
        return outputs

class ContrastGrabber(Interface):
    """ Contrast grabber module to pick up SPM or FSL contrast files

    subject_id if provided is always the first arg to the templates
    
    Examples
    --------

    >>> from nipype.interfaces.io import ContrastGrabber
    >>> cg = ContrastGrabber()
    >>> cg.inputs.con_template = 'l1output/*/model*/*/cope%d.feat/*/cope*.gz'
    >>> cg.inputs.contrast_id = 2
    >>> res = cg.run() # doctest: +SKIP

    Now return cope and varcopes
    >>> cg.inputs.var_template = 'l1output/*/model*/*/cope%d.feat/*/varcope*.gz'
    >>> res = cg.run() # doctest: +SKIP

    """
    
    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
            Parameters
            --------------------
            (all default to None)

            con_template : str
                template to pickup up contrasts
            var_template : str
                template to pickup up variance estimates
            subject_id : list
                Only return contrasts for these subjects
            contrast_id : int/list
                index of contrast to be picked up
            """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(con_template=None,
                            var_template=None,
                            subject_id=None,
                            contrast_id=None)

    def outputs_help(self):
        print self.outputs.__doc__

    def outputs(self):
        """
            Parameters
            ----------

            (all default to None)

            con_images : list
                list of contrast images
            var_images : list
                list of variance images if they exist
        """
        return Bunch(con_images=None,
                     var_images=None)
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.contrast_id is None:
            return outputs
        outputs.con_images = []
        outputs.var_images = []
        subject_id = self.inputs.subject_id
        if not subject_id:
            subject_id = [None]
        if not isinstance(subject_id, list):
            subject_id = [subject_id]
        contrast_id = self.inputs.contrast_id
        if not isinstance(contrast_id, list):
            contrast_id = [contrast_id]
        for subj in subject_id:
            for cont in contrast_id:
                if subj:
                    basedir = self.inputs.con_template % (subj, cont)
                else:
                    basedir = self.inputs.con_template % cont
                print basedir
                conimg = glob.glob(basedir)
                outputs.con_images.extend(conimg)
                if self.inputs.var_template:
                    if subj:
                        basedir = self.inputs.var_template % (subj, cont)
                    else:
                        basedir = self.inputs.var_template % cont
                    varimg = glob.glob(basedir)
                    outputs.var_images.extend(varimg)
        if outputs.con_images:
            outputs.con_images = list_to_filename(outputs.con_images)
        else:
            outputs.con_images = None
        if outputs.var_images:
            outputs.var_images = list_to_filename(outputs.var_images)
        else:
            outputs.var_images = None
        return outputs

    def run(self, cwd=None):
        """Execute this module.
        """
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)


class FreeSurferSource(Interface):
    """Generates freesurfer subject info from their directories
    """
    dirmap = dict(T1='mri',
                  aseg='mri',
                  brain='mri',
                  brainmask='mri',
                  filled='mri',
                  norm='mri',
                  nu='mri',
                  orig='mri',
                  rawavg='mri',
                  ribbon='mri',
                  wm='mri',
                  wmparc='mri',
                  curv='surf',
                  inflated='surf',
                  pial='surf',
                  smoothwm='surf',
                  sphere='surf',
                  sulc='surf',
                  thickness='surf',
                  volume='surf',
                  white='surf',
                  label='label',
                  annot='label')
    dirmap['aparc+aseg']='mri'
    dirmap['sphere.reg']='surf'

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
            Parameters
            --------------------
            (all default to None)

            subjects_dir : string
                freesurfer subjects directory.  The program will try to
                retrieve it from the environment if available.
            subject_id : string
                The subject for whom data needs to be retrieved
            hemi : string
                Selects hemisphere specific outputs
            """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(subjects_dir=None,
                            subject_id=None,
                            hemi=None,
                            )

    def _get_files(self, path, key):
        dirval = self.dirmap[key]
        globsuffix = ''
        if dirval == 'mri':
            globsuffix = '.mgz'
        if key == 'ribbon' or dirval in ['surf', 'label']:
            if self.inputs.hemi:
                globprefix = self.inputs.hemi+'.'
            else:
                globprefix = '*h.'
                if key == 'ribbon' or key == 'label':
                    globprefix = '*'
            if key == 'annot':
                globprefix += '*'
        else:
            globprefix = ''
        if key in ['annot','label']:
            globsuffix = ''
        keydir = os.path.join(path,dirval)
        globpattern = os.path.join(keydir,''.join((globprefix,key,globsuffix)))
        outfiles = glob.glob(globpattern)
        if outfiles:
            return deepcopy(list_to_filename(outfiles))
        else:
            return None
    
    def outputs_help(self):
        """Print description of outputs provided by the module"""
        print self.outputs.__doc__

    def outputs(self):
        """Set of output names that are generated.

        If hemi is specified only that particular hemisphere's data is returned
        for those variables that care about hemisphere (noted below).
        Otherwise the returned items contain left and right in sequence.

        Parameters
        ----------
        
        T1
        aseg
        aparc+aseg
        brain
        brainmask
        filled
        norm
        nu
        orig
        rawavg
        ribbon : lh, rh, combined
        wm
        wmparc
        white : lh, rh
        pial : lh, rh
        curv : lh, rh
        labels
        annot : lh, rh
        """
        outputs = Bunch(self.dirmap)
        for k,v in outputs.items():
            setattr(outputs,k,None)
        return outputs
        
    def aggregate_outputs(self):
        subjects_dir = self.inputs.subjects_dir
        if not subjects_dir:
            subjects_dir = os.getenv('SUBJECTS_DIR')
        if not subjects_dir:
            raise Exception('SUBJECTS_DIR variable must be set or '\
                                'provided as input to FreeSurferSource.')
        subject_path = os.path.join(subjects_dir,self.inputs.subject_id)
        outputs = self.outputs()
        for k,v in outputs.items():
            val = self._get_files(subject_path,k)
            setattr(outputs,k, val)
        return outputs

    def run(self, cwd=None):
        """Execute this module.

        cwd is just there to make things "work" for now
        """
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)
        
        
        
