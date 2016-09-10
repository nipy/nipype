.. _interface_tutorial:

=======================
 Tutorial : Interfaces
=======================

Specifying input settings
-------------------------

The nipype interface modules provide a Python interface to external
packages like FSL_ and SPM_.  Within the module are a series of Python
classes which wrap specific package functionality.  For example, in
the fsl module, the class :class:`nipype.interfaces.fsl.Bet` wraps the
``bet`` command-line tool.  Using the command-line tool, one would
specify input settings using flags like ``-o``, ``-m``, ``-f <f>``, etc...
However, in nipype, options are assigned to Python attributes and can
be specified in the following ways:

Settings can be assigned when you first create an interface object:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET(in_file='foo.nii', out_file='bar.nii')
   result = mybet.run()

Settings can be assigned through the ``inputs`` attribute:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET()
   mybet.inputs.in_file = 'foo.nii'
   mybet.inputs.out_file = 'bar.nii'
   result = mybet.run()

Settings can be assigned when calling the ``run`` method:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET()
   result = mybet.run(in_file='foo.nii', out_file='bar.nii', frac=0.5)

Settings can be saved to a json file:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET(in_file='foo.nii', out_file='bar.nii', frac=0.5)
   mybet.save_inputs_to_json('bet-settings.json')

Once saved, the three inputs set for ``mybet`` will be stored in a JSON
file. These settings can also be loaded from a json file:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET()
   mybet.load_inputs_from_json('bet-settings.json', overwrite=False)


Loading settings will overwrite previously set inputs by default, unless
the ``overwrite`` argument is ``False``. Conveniently, the settings can be
also read during the interface instantiation:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET(from_file='bet-settings.json')

If the user provides settings during interface creation, they will take
precedence over those loaded using ``from_file``:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.BET(from_file='bet-settings.json', frac=0.7)

In this case, ``mybet.inputs.frac`` will contain the value ``0.7`` regardless
the value that could be stored in the ``bet-settings.json`` file.


Getting Help
------------

In IPython_ you can view the docstrings which provide some basic
documentation and examples.

.. sourcecode:: ipython

    In [2]: fsl.FAST?
    Type:		type
    Base Class:	<type 'type'>
    String Form:	<class 'nipype.interfaces.fsl.preprocess.FAST'>
    Namespace:	Interactive
    File:		/Users/satra/sp/nipype/interfaces/fsl/preprocess.py
    Docstring:
        Use FSL FAST for segmenting and bias correction.

        For complete details, see the `FAST Documentation.
        <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_

        Examples
        --------
        >>> from nipype.interfaces import fsl
        >>> from nipype.testing import anatfile

        Assign options through the ``inputs`` attribute:

        >>> fastr = fsl.FAST()
        >>> fastr.inputs.in_files = anatfile
        >>> out = fastr.run() #doctest: +SKIP

    Constructor information:
    Definition:	fsl.FAST(self, **inputs)

.. sourcecode:: ipython

   In [5]: spm.Realign?
   Type:		type
   Base Class:	<type 'type'>
   String Form:	<class 'nipype.interfaces.spm.preprocess.Realign'>
   Namespace:	Interactive
   File:		/Users/satra/sp/nipype/interfaces/spm/preprocess.py
   Docstring:
       Use spm_realign for estimating within modality rigid body alignment

       http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf#page=25

       Examples
       --------

       >>> import nipype.interfaces.spm as spm
       >>> realign = spm.Realign()
       >>> realign.inputs.in_files = 'functional.nii'
       >>> realign.inputs.register_to_mean = True
       >>> realign.run() # doctest: +SKIP

   Constructor information:
   Definition:	spm.Realign(self, **inputs)


All of the nipype.interfaces classes have an ``help`` method
which provides information on each of the options one can assign.

.. sourcecode:: ipython

    In [6]: fsl.BET.help()
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

.. sourcecode:: ipython

    In [7]: spm.Realign.help()
    Inputs
    ------

    Mandatory:
     in_files: list of filenames to realign

    Optional:
     fwhm: gaussian smoothing kernel width
     interp: degree of b-spline used for interpolation
     jobtype: one of: estimate, write, estwrite (default=estwrite)
     matlab_cmd: None
     mfile: Run m-code using m-file (default=True)
     paths: Paths to add to matlabpath
     quality: 0.1 = fast, 1.0 = precise
     register_to_mean: Indicate whether realignment is done to the mean image
     separation: sampling separation in mm
     weight_img: filename of weighting image
     wrap: Check if interpolation should wrap in [x,y,z]
     write_interp: degree of b-spline used for interpolation
     write_mask: True/False mask output image
     write_which: determines which images to reslice
     write_wrap: Check if interpolation should wrap in [x,y,z]

    Outputs
    -------
    mean_image: Mean image file from the realignment
    realigned_files: Realigned files
    realignment_parameters: Estimated translation and rotation parameters


Our :ref:`interface-index` documentation provides html versions of our
docstrings and includes links to the specific package
documentation. For instance, the :class:`nipype.interfaces.fsl.Bet`
docstring has a direct link to the online BET Documentation.


FSL interface example
---------------------

Using FSL_ to realign a time_series:

.. testcode::

   import nipype.interfaces.fsl as fsl
   realigner = fsl.McFlirt()
   realigner.inputs.in_file='timeseries4D.nii'
   result = realigner.run()


SPM interface example
---------------------

Using SPM_ to realign a time-series:

.. testcode::

   import nipype.interfaces.spm as spm
   from glob import glob
   allepi = glob('epi*.nii') # this will return an unsorted list
   allepi.sort()
   realigner = spm.Realign()
   realigner.inputs.in_files = allepi
   result = realigner.run()

.. include:: ../links_names.txt
