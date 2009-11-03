""" Set of interfaces that allow interaction with data. Currently
    available interfaces are:

    DataSource: Generic nifti to named Nifti interface
    DataSink: Generic named output from interfaces to data store

    To come :
    XNATSource, XNATSink

"""
from nipype.interfaces.base import Interface, CommandLine, Bunch, InterfaceResult
from copy import deepcopy
from nipype.utils.filemanip import copyfiles, list_to_filename
from nipype.utils.misc import mktree
import glob
import os


class DataSource(Interface):
    """ Generic datasource module that takes a directory containing a
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

        base_directory : str
            Path to the base directory consisting of subject data.
        subject_template : str
            Template encoding the subject directory name, indexed
            by subject id.
        file_template : str
            Template used for matching filenames.
            Default = '*-%d-*.nii'
        subject_id: str or int
            The subject identifier.
        subject_directory : str
            Path to the subject directory.
        subject_info : dict
            Provides information about how to map subject run
            numbers to the output fields.

            `subject_id` are keys and the values are a list of tuples.
            info[subject_id] = [([run_identifiers], output_fieldname), ...]

        Examples
        --------
     
        Here our experiment data is stored in our home directory under
        'data/exp001'.  In the exp001 directory we have a subdirectory
        for our subject named 's1'.  In the 's1' directory we have
        four functional images, 'f3', 'f5', 'f7', 'f10'.  In the
        `info` dictionary we create an entry where the key is the
        subject identifier 's1', and the value is a list of one
        element, a tuple containing a list of the functional image
        names and a field name 'func'.  The 'func' field name is the
        output field name for this datasource object.  So for
        instance, if we were doing motion correction using SPM
        realign, the datasource output 'func' would map to the realign
        input 'infile' in the pipeline.

        >>> from nipype.interfaces.io import DataSource
        >>> info = {}
        >>> info['s1'] = [(['f3', 'f5', 'f7', 'f10'], 'func')]
        >>> datasource = DataSource()
        >>> data_dir = os.path.expanduser('~/data/exp001')
        >>> datasource.inputs.base_directory = data_dir
        >>> datasource.inputs.subject_template = '%s'
        >>> datasource.inputs.file_template = '%s.nii'
        >>> datasource.inputs.subject_info = info
        >>> datasource.inputs.subject_id = 's1'

        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(base_directory=None,
                            subject_template=None,
                            file_template='*-%d-*.nii',
                            subject_id=None,
                            subject_directory=None,
                            subject_info=None)

    def outputs_help(self):
        """
            Parameters
            ----------

            (all default to None)

            subject_id : string
                Subject identifier
            subject_directory: /path/to/dir
                Location of subject directory containing nifti files

            remaining fields are defined by user. See subject_info in
            inputs_help() for description of how to specify output
            fields 
            """
        print self.outputs_help.__doc__
        
    def aggregate_outputs(self):
        outputs = Bunch(subject_id=None)
        outputs.subject_id = self.inputs.subject_id
        subjdir = self.inputs.subject_directory
        if subjdir is None:
            #print self.inputs['subj_template'],self.inputs['subj_id']
            if self.inputs.subject_template is not None:
                subjdir = self.inputs.subject_template % self.inputs.subject_id
            else:
                subjdir = self.inputs.subject_id
            subjdir = os.path.join(self.inputs.base_directory,subjdir)
        if subjdir is None:
            raise Exception('Subject directory not provided')
        outputs.subject_directory = subjdir
        if self.inputs.subject_info is None:
            raise Exception('Subject info not provided')
        try:
            info = self.inputs.subject_info[self.inputs.subject_id]
        except KeyError:
            raise KeyError("Key [%s] does not exist in subject_info dictionary"
                           % self.inputs.subject_id)
        for idx, _type in info:
            outputs[_type] = []
            for i in idx:
                files = self.inputs.file_template % i
                path = os.path.abspath(os.path.join(subjdir, files))
                files_found = glob.glob(path)
                if len(files_found) == 0:
                    msg = 'Unable to find file: %s' % path
                    raise IOError(msg)
                outputs[_type].extend(files_found)
            outputs[_type] = list_to_filename(outputs[_type])
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

            Any fields that are set as lists will be copied to a
            directory under subject_directory with the fieldname as a
            new directory.

        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(base_directory=None,
                            subject_directory=None,
                            subject_template=None,
                            subject_id=None)
        self.input_keys = self.inputs.__dict__.keys()
        
    def outputs_help(self):
        """
            No outputs 
        """
        print self.outputs_help.__doc__
        
    def aggregate_outputs(self):
        outputs = Bunch()
        return Bunch()

    def run(self, cwd=None):
        """Execute this module.

        cwd is just there to make things work for now
        """
        subjdir = self.inputs.subject_directory
        if subjdir is None:
            #print self.inputs['subj_template'],self.inputs['subj_id']
            if self.inputs.subject_template is not None:
                subjdir = self.inputs.subject_template % (self.inputs.subject_id)
            else:
                subjdir = self.inputs.subject_id
            subjdir = os.path.join(self.inputs.base_directory,subjdir)
        if subjdir is None:
            raise Exception('Subject directory not provided')
        outdir = subjdir
        if not os.path.exists(outdir):
            mktree(outdir)
        for k,v in self.inputs.iteritems():
            if k not in self.input_keys:
                if v is not None:
                    tempoutdir = outdir
                    for d in k.split('.'):
                        if d[0] == '@':
                            continue
                        tempoutdir = os.path.join(tempoutdir,d)
                        if not os.path.exists(tempoutdir):
                            os.mkdir(tempoutdir)
                    copyfiles(self.inputs[k],tempoutdir,copy=True)
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)


class DataGrabber(Interface):
    """ Generic datagrabber module that wraps around glob in an
        intelligent way for neuroimaging tasks 
    """
    
    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
            Parameters
            --------------------
            (all default to None)

            file_template : string
                template for filename
            template_argtuple: tuple of arguments
                arguments that fit into file_template
            template_argnames: list of strings
                provides names of inputs that will be used as
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
            """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(file_template=None,
                            template_argtuple=None,
                            template_argnames=None,
                            )

    def outputs_help(self):
        """
            Parameters
            ----------

            (all default to None)

            file_list : list
                list of files picked up by the grabber
            """
        print self.outputs_help.__doc__
        
    def aggregate_outputs(self):
        outputs = Bunch(file_list=None)
        args = []
        if self.inputs.template_argtuple is not None:
            args.extend(list(self.inputs.template_argtuple))

        if self.inputs.template_argnames is not None:
            for name in self.inputs.template_argnames:
                arg = self.inputs[name]
                print name, arg
                if arg is not None:
                    args.append(arg)
        template = self.inputs.file_template
        if len(args)>0:
            template = template%tuple(args)
        outputs.file_list = list_to_filename(glob.glob(template))
        return outputs

    def run(self, cwd=None):
        """Execute this module.
        """
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

