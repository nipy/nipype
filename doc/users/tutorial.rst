.. _tutorial:

=========
 Tutorial
=========

CommandLine interface example
-----------------------------
CommandLine in interfaces.base is a basic interface for running
command line calls through python

You typically generate an instance of CommandLine, and then call
.run() on it.

.. sourcecode:: ipython
   
   from nipype.interfaces.base import CommandLine
   cl = CommandLine(args=['echo hello'])
   print cl.inputs.args
   clout = cl.run()
   print clout.runtime.messages
   print clout.runtime.returncode
   print clout.runtime.errmessages
   print clout.interface.cmdline
   

   cl.inputs.args = ['echo', 'goodbye']


   clout = CommandLine().run('ls -l')
   clout = CommandLine('ls').run('-l)
   clout = CommandLine(args=['ls', '-l'], cwd='.').run()

.. Note:
   
   If you pass args as a key, value pair to .run(), it will overwrite
   the existing inputs.args, not append to it....however any new
   single args will just be appended

   For example in the code below, the final command line argument
   will be
   *'echo hello'* , NOT 'ls echo hello'

.. sourcecode:: ipython

   clout.CommandLine(args=['ls']).run(args=['echo','hello'])


   

FSL interface example
---------------------

SPM interface example
---------------------

There are three different ways in which you can call an SPM interface.

.. sourcecode:: ipython
   
   import nipype.interfaces.spm as spm
   result = spm.realign().run(infile='epi.nii')

   result = spm.realign(infile='epi.nii').run()
   
   realign = spm.Realign()
   realign.inputs.infile = 'epi.nii'
   result = realign.run()


Running a pipeline
-------------------

This section describes how one might go about doing a first level
analysis using the pipeline approach. Running a first-level analysis
pipeline involves setting up a python script containing a few
different pieces.

#. Setting up the nodes of the pipeline

#. Setting up the connections between nodes

#. Providing subject specific model information

The anatomy of a pipeline script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Tell python where to find the appropriate functions.

.. sourcecode:: ipython

   # Telling python where to look for things
   import nipype.interfaces.io as nio           # Data i/o 
   import nipype.interfaces.spm as spm          # spm
   import nipype.interfaces.matlab as mlab      # how to run matlab
   import nipype.interfaces.fsl as fsl          # fsl
   import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
   import nipype.pipeline.engine as pe          # pypeline engine
   import nipype.algorithms.rapidart as ra      # artifact detection
   import os                                    # system functions

#. Setup any package specific configuration. The output file format for
 FSL routines is being set to NIFTI and a specific version of matlab
 is being used.

.. sourcecode:: ipython

   # Tell fsl to generate all output in nifti format
   print fsl.fslversion()
   fsl.fsloutputtype('NIFTI')
   # setup the way matlab should be called
   mlab.MatlabCommandLine.matlab_cmd = "matlab.2009a -nodesktop -nosplash"

#. The following lines of code sets up the necessary information
 required by the datasource module. It provides a mapping between run
 numbers (nifti files) and the mnemonic ('struct', 'func', etc.,.)
 that run should be called. These mnemonics or fields become the
 output fields of the datasource module.

.. sourcecode:: ipython

   subj_list = ['s175']
   info = {}
   # provides subject-specific, run-specific information
   # info[subjid] = [([runno1,runno2,...],'runtype'),...] 
   info['s175'] = [([6],'multiecho'),([7],'struct'),([12,14,16],'func'),([20],'dti'),([8,18],'resting')]

#. Setup nodes for performing the preprocessing with the data. The
 variable iterables for datasource tells the system, that it should
 perform any of the operations related to data source for each of the
 iterable items. In this case, the entire preprocessing and estimation
 will be repeated for each subject contained in subj_list.

.. sourcecode:: ipython

   # Setup preprocessing pipeline nodes
   # This node looks into the directory containing Nifti files and returns pointers to the files in a structured format as determined by the runtype names provided in the info structure above
   datasource = nw.NodeWrapper(interface=nio.DataSource())
   datasource.inputs.base_directory = '/g2/gablab/memory/conversion/data'
   datasource.inputs.base_directory = '/software/data/sourcemem'
   datasource.inputs.subject_info = info

   # iterables provides a mechanism to execute part of the processing over multiple instances of the parameter. In the following example iterables allows DataSource node and its descendants to be executed for multiple subjects. 
   datasource.iterables = dict(subject_id=lambda:subj_list)

   # run SPM realign
   realign = nw.NodeWrapper(interface=spm.Realign(),diskbased=True)
   realign.inputs.register_to_mean = True

   # run artifact detection
   art = nw.NodeWrapper(interface=ra.ArtifactDetect(),diskbased=True)
   art.inputs.use_differences = True
   art.inputs.use_norm = True
   art.inputs.norm_threshold = 0.2
   art.inputs.zintensity_threshold = 3
   art.inputs.mask_type = 'spm_global'

   # run FSL's bet
   better = nw.NodeWrapper(interface=fsl.Bet(),diskbased=True)

   # run SPM's coregistration
   coregister = nw.NodeWrapper(interface=spm.Coregister(),diskbased=True)

   # run SPM's normalization
   normalize = nw.NodeWrapper(interface=spm.Normalize(),diskbased=True)
   normalize.inputs.template = '/software/spm5_1782/templates/EPI.nii'

   # run SPM's smoothing
   smooth = nw.NodeWrapper(interface=spm.Smooth(),diskbased=True)
   smooth.inputs.fwhm = [5,5,9]

#. Define a function that returns subject-specific model information

.. sourcecode:: ipython

   # setup analysis components
   from nipype.interfaces.base import Bunch
   import scipy.io as sio

   #define a function that reads a matlab file and returns subject specific condition information

   def subjectinfo(subject_id):
      print "Subject ID: %s\n"%str(subject_id)
      subjcondfile = '%s_statistics.mat' % str(subject_id)
          # read mat file that stores event information for the subject
      data = sio.loadmat(os.path.join('/software/data/sourcemem',subjcondfile))
      output = []
      names = ['Miss','Source_2','Source_Font','Source_Question','Source_0']
      for r in range(3):
          runinfo = data['stats'][0][0].onsets[0][r]
          output.insert(r,
                        Bunch(conditions=[s.replace('_','') for s in names],
                              onsets=[runinfo.__getattribute__(s)[0].tolist() for s in names],
                              durations=[[0] for s in names],
                              amplitudes=None,
                              tmod=None,
                              pmod=None,
                              regressor_names=None,
                              regressors=None))
      return output

  # Set up all the contrasts that should be evaluated
  cont1 = ['Hit>Miss','T', ['Source2','SourceFont','SourceQuestion','Source0','Miss'],[1,1,1,1,-4]]
  cont2 = ['Source2>0', 'T', ['Source2','Source0'],[1,-1]]
  cont3 = ['Source2>source0miss', 'T', ['Source2','Source0','Miss'],[2,-1,-1]]
  cont4 = ['source12>source0miss', 'T', ['Source2','SourceFont','SourceQuestion','Source0','Miss'],[1,0.5,0.5,-1,-1]]
  cont5 = ['mem strength', 'T', ['Source2','SourceFont','SourceQuestion','Source0','Miss'],[2,0.5,0.5,-1,-2]]
  cont6 = ['source strength', 'T', ['Source2','SourceFont','SourceQuestion'],[1,-0.5,-0.5]]
  cont7 = ['source specificity', 'T', ['SourceFont','SourceQuestion'],[1,-1]]
  cont8 = ['Task vs Fixation', 'T', ['Miss','Source2','SourceFont','SourceQuestion','Source0'],[0.2,0.2,0.2,0.2,0.2]]
  cont9 = ['source12>0', 'T', ['Source2','SourceFont','SourceQuestion','Source0'],[1,1,1,-3]]
  contrasts = [cont1,cont2,cont3,cont4,cont5,cont6,cont7,cont8,cont9]

#. Setup the final nodes of the pipeline that are used for specifying
 the model and estimating model parameters.

.. sourcecode:: ipython

   modelspec = nw.NodeWrapper(interface=spm.SpecifyModel())
   modelspec.inputs.subject_info_func = subjectinfo
   modelspec.inputs.concatenate_runs = True
   modelspec.inputs.input_units = 'scans'
   modelspec.inputs.output_units = 'scans'
   modelspec.inputs.time_repetition = 2.

   level1design = nw.NodeWrapper(interface=spm.Level1Design(),diskbased=True)
   level1design.inputs.timing_units = modelspec.inputs.output_units
   level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
   level1design.inputs.bases = {'hrf':{'derivs': [0,0]}}

   level1estimate = nw.NodeWrapper(interface=spm.EstimateModel(),diskbased=True)
   level1estimate.inputs.estimation_method = {'Classical' : 1}

   contrastestimate = nw.NodeWrapper(interface=spm.EstimateContrast(),diskbased=True)
   contrastestimate.inputs.contrasts = contrasts

#. Setup different confuguration options for the pipeline.

.. sourcecode:: ipython

   # Setup pipeline
   pipeline = pe.Pipeline()
   pipeline.config['workdir'] = os.path.abspath('/g2/gablab/memory/newpype')
   pipeline.config['workdir'] = os.path.abspath('.')
   pipeline.config['use_parameterized_dirs'] = True

   pipeline.connect([(datasource,realign,[('func','infile')]),
                  (realign,better,[('mean_image','infile')]),
                  (realign,coregister,[('mean_image', 'source')]),
		  (datasource,coregister,[('struct', 'target')]),
		  (better,normalize,[('outfile', 'source')]),
		  (realign, normalize, [('realigned_files','apply_to_files')]),
                  (realign,art,[('realigned_files','realigned_files'),('realignment_parameters','realignment_parameters')]),
		  (normalize, smooth, [('normalized_files', 'infile')]),
                  (datasource,modelspec,[('subject_id','subject_id')]),
                  (realign,modelspec,[('realignment_parameters','realignment_parameters')]),
                  (smooth,modelspec,[('smoothed_files','functional_runs')]),
                  (art,modelspec,[('outlier_files','outlier_files')]),
                  (modelspec,level1design,[('session_info','session_info')]),
                  (level1design,level1estimate,[('spm_mat_file','spm_design_file')]),
                  (level1estimate,contrastestimate,[('spm_mat_file','spm_mat_file'),
                                                  ('beta_images','beta_images'),
                                                  ('residual_image','residual_image'),
                                                  ('RPVimage','RPVimage')]),
                  ])


#. To execute the pipeline, call it's run function.

.. sourcecode:: ipython

   pipeline.run()
