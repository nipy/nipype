.. _dartmouth_workshop_2010:

=================================
 Dartmouth College Workshop 2010 
=================================

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

.. include:: ../examples/dartmouth_workshop_2010.rst

.. include:: ../links_names.txt