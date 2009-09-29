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
            --------------------
            (all default to None)

            base_directory : /path/to/dir
                Basedirectory consisting of subject data
            subject_template : string
                Template encoding the subject directory name, indexed
                by subject id. For example, the default
            subject_id: string or int
                Subject identifier
            subject_directory : /path/to/dir
                Path to subject directory
            subject_info : dict
                Provides information about how to map subject run
                numbers to output fields

                subject_id are keys and values are a list of tuples.
                info[subject_id] = [([runnos],fieldname),...]

                Examples
                --------

                info['s1'] = [([4,5],'anat'),([6,7],'bold'),([8],'dti')]
                info[1] = [([3,4],'struct'),([6,7],'bold'),([8],'dti')]

                In the above examples, the output fields of this
                object will be the names 'anat', 'bold', etc.,.
            """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(base_directory=None,
                            subject_template=None,
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
                subjdir = self.inputs.subject_template % (self.inputs.subject_id)
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
            raise KeyError("Key [%s] does not exist in subject_info dictionary"%self.inputs.subject_id)
        for idx,type in info:
            outputs[type] = []
            for i in idx:
                files = '*-%d-*.nii' % i
                path = os.path.abspath(os.path.join(subjdir,files))
                outputs[type].extend(glob.glob(path))
            outputs[type] = list_to_filename(outputs[type])
        return outputs

    def run(self):
        """Execute this module.
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

    def run(self):
        """Execute this module.
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
            os.mkdir(outdir)
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

            Alternatively can provide upto 3 additional arguments
            to use as iterables
            template_arg1: argument 1
            template_arg2: argument 2
            template_arg3: argument 3
            """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(file_template=None,
                            template_argtuple=None,
                            template_arg1=None,
                            template_arg2=None,
                            template_arg3=None
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

        for i in range(3):
            arg = self.inputs['template_arg%d'%(i+1)]
            if arg is not None:
                args.append(arg)
        template = self.inputs.file_template
        if len(args)>0:
            template = template%tuple(args)
        outputs.file_list = list_to_filename(glob.glob(template))
        return outputs

    def run(self):
        """Execute this module.
        """
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

