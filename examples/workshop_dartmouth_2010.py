"""
================================
Workshop: Dartmouth College 2010
================================

First lets go to the directory with the data we'll be working on and start the interactive python interpreter
(with some nipype specific configuration). Note that nipype does not need to be run through ipython - it is
just much nicer to do interactive work in it.

.. sourcecode:: bash

    cd $TDPATH
    ipython -p nipype

For every neuroimaging procedure supported by nipype there exists a wrapper - a small piece of code managing
the underlying software (FSL, SPM, AFNI etc.). We call those interfaces. They are standarised so we can hook them up
together. Lets have a look at some of them.

.. sourcecode:: ipython

    In [1]: import nipype.interfaces.fsl as fsl

    In [2]: fsl.BET.help()
    Inputs
    ------

    Mandatory:
     in_file: input file to skull strip

    Optional:
     args: Additional parameters to the command
     center: center of gravity in voxels
     environ: Environment variables (default={})
     frac: fractional intensity threshold
     functional: apply to 4D fMRI data
      mutually exclusive: functional, reduce_bias
     mask: create binary mask image
     mesh: generate a vtk mesh brain surface
     no_output: Don't generate segmented output
     out_file: name of output skull stripped image
     outline: create surface outline image
     output_type: FSL output type
     radius: head radius
     reduce_bias: bias field and neck cleanup
      mutually exclusive: functional, reduce_bias
     skull: create skull image
     threshold: apply thresholding to segmented brain image and mask
     vertical_gradient: vertical gradient in fractional intensity threshold (-1, 1)

    Outputs
    -------
    mask_file: path/name of binary brain mask (if generated)
    meshfile: path/name of vtk mesh file (if generated)
    out_file: path/name of skullstripped file
    outline_file: path/name of outline file (if generated)

    In [3]: import nipype.interfaces.freesurfer as fs

    In [4]: fs.Smooth.help()
    Inputs
    ------

    Mandatory:
     in_file: source volume
     num_iters: number of iterations instead of fwhm
      mutually exclusive: surface_fwhm
     reg_file: registers volume to surface anatomical
     surface_fwhm: surface FWHM in mm
      mutually exclusive: num_iters
      requires: reg_file

    Optional:
     args: Additional parameters to the command
     environ: Environment variables (default={})
     proj_frac: project frac of thickness a long surface normal
      mutually exclusive: proj_frac_avg
     proj_frac_avg: average a long normal min max delta
      mutually exclusive: proj_frac
     smoothed_file: output volume
     subjects_dir: subjects directory
     vol_fwhm: volumesmoothing outside of surface

    Outputs
    -------
    args: Additional parameters to the command
    environ: Environment variables
    smoothed_file: smoothed input volume
    subjects_dir: subjects directory

You can read about all of the interfaces implemented in nipype at our online documentation at http://nipy.sourceforge.net/nipype/documentation.html#documentation .
Check it out now.

Using interfaces
----------------

Having interfaces allows us to use third party software (like FSL BET) as function. Look how simple it is.
"""

import nipype.interfaces.fsl as fsl
result = fsl.BET(in_file='data/s1/struct.nii').run()
print result

"""
Running a single program is not much of a breakthrough. Lets run motion correction followed by smoothing
(isotropic - in other words not using SUSAN). Notice that in the first line we are setting the output data type
for all FSL interfaces.
"""

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
result1 = fsl.MCFLIRT(in_file='data/s1/f3.nii').run()
result2 = fsl.Smooth(in_file='f3_mcf.nii.gz', fwhm=6).run()

"""
Simple workflow
---------------

In the previous example we knew that fsl.MCFLIRT will produce a file called f3_mcf.nii.gz and we have hard coded
this as an input to fsl.Smooth. This is quite limited, but luckily nipype supports joining interfaces in pipelines.
This way output of one interface will be used as an input of another without having to hard code anything. Before
connecting Interfaces we need to put them into (separate) Nodes and give them unique names. This way every interface will
process data in a separate folder.
"""

import nipype.pipeline.engine as pe
import os

motion_correct = pe.Node(interface=fsl.MCFLIRT(in_file=os.path.abspath('data/s1/f3.nii')),
                         name="motion_correct")
smooth = pe.Node(interface=fsl.Smooth(fwhm=6), name="smooth")

motion_correct_and_smooth = pe.Workflow(name="motion_correct_and_smooth")
motion_correct_and_smooth.base_dir = os.path.abspath('.') # define where will be the root folder for the workflow
motion_correct_and_smooth.connect([
                                   (motion_correct, smooth, [('out_file', 'in_file')])
                                   ])
# we are connecting 'out_file' output of motion_correct to 'in_file' input of smooth
motion_correct_and_smooth.run()

"""
Another workflow
----------------

Another example of a simple workflow (calculate the mean of fMRI signal and subtract it).
This time we'll be assigning inputs after defining the workflow.
"""

calc_mean = pe.Node(interface=fsl.ImageMaths(), name="calc_mean")
calc_mean.inputs.op_string = "-Tmean"
subtract = pe.Node(interface=fsl.ImageMaths(), name="subtract")
subtract.inputs.op_string = "-sub"

demean = pe.Workflow(name="demean")
demean.base_dir = os.path.abspath('.')
demean.connect([
                (calc_mean, subtract, [('out_file', 'in_file2')])
                ])

demean.inputs.calc_mean.in_file = os.path.abspath('data/s1/f3.nii')
demean.inputs.subtract.in_file = os.path.abspath('data/s1/f3.nii')
demean.run()

"""
Reusing workflows
-----------------

The beauty of the workflows is that they are reusable. We can just import a workflow made by someone
else and feed it with our data.
"""

from fmri_fsl import preproc
preproc.base_dir = os.path.abspath('.')
preproc.inputs.inputspec.func = os.path.abspath('data/s1/f3.nii')
preproc.inputs.inputspec.struct = os.path.abspath('data/s1/struct.nii')
preproc.run()


"""
... and we can run it again and it won't actually rerun anything because none of
the parameters have changed.
"""

preproc.run()


"""
... and we can change a parameter and run it again. Only the dependent nodes
are rerun and that too only if the input state has changed.
"""

preproc.inputs.meanfuncmask.frac = 0.5
preproc.run()

"""
Visualizing workflows 1
-----------------------

So what did we run in this precanned workflow
"""

preproc.write_graph()

"""
Datasink
--------

Datasink is a special interface for copying and arranging results.
"""

import nipype.interfaces.io as nio

preproc.inputs.inputspec.func = os.path.abspath('data/s1/f3.nii')
preproc.inputs.inputspec.struct = os.path.abspath('data/s1/struct.nii')
datasink = pe.Node(interface=nio.DataSink(),name='sinker')
preprocess = pe.Workflow(name='preprocout')
preprocess.base_dir = os.path.abspath('.')
preprocess.connect([
                    (preproc, datasink, [('meanfunc2.out_file', 'meanfunc'),
                                         ('maskfunc3.out_file', 'funcruns')])
                    ])
preprocess.run()

"""
Datagrabber
-----------

Datagrabber is (surprise, surprise) an interface for collecting files from hard drive. It is very flexible and
supports almost any file organisation of your data you can imagine.
"""

datasource1 = nio.DataGrabber()
datasource1.inputs.template = 'data/s1/f3.nii'
results = datasource1.run()
print results.outputs

datasource2 = nio.DataGrabber()
datasource2.inputs.template = 'data/s*/f*.nii'
results = datasource2.run()
print results.outputs

datasource3 = nio.DataGrabber(infields=['run'])
datasource3.inputs.template = 'data/s1/f%d.nii'
datasource3.inputs.run = [3, 7]
results = datasource3.run()
print results.outputs

datasource4 = nio.DataGrabber(infields=['subject_id', 'run'])
datasource4.inputs.template = 'data/%s/f%d.nii'
datasource4.inputs.run = [3, 7]
datasource4.inputs.subject_id = ['s1', 's3']
results = datasource4.run()
print results.outputs

"""
Iterables
---------

Iterables is a special field of the Node class that enables to iterate all workfloes/nodes connected to it over
some parameters. Here we'll use it to iterate over two subjects.
"""

import nipype.interfaces.utility as util
infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', ['s1', 's3'])

datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['func', 'struct']), name="datasource")
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.base_directory = os.path.abspath('data')
datasource.inputs.template_args = dict(func=[['subject_id','f3']], struct=[['subject_id','struct']])

my_workflow = pe.Workflow(name="my_workflow")
my_workflow.base_dir = os.path.abspath('.')

my_workflow.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                     (datasource, preproc, [('func', 'inputspec.func'),
                                          ('struct', 'inputspec.struct')])])
my_workflow.run()


"""
and we can change a node attribute and run it again

"""

smoothnode = my_workflow.get_node('preproc.smooth')
assert(str(smoothnode)=='preproc.smooth')
smoothnode.iterables = ('fwhm', [5.,10.])
my_workflow.run()

"""
Visualizing workflows 2
-----------------------

In the case of nested workflows, we might want to look at expanded forms of the workflow.
"""
