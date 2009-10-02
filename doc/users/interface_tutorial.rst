.. _interface_tutorial:

=======================
 Tutorial : Interfaces
=======================

Specifying options
------------------

The nipype interface modules provide a Python interface to external
packages like FSL_ and SPM_.  Within the module are a series of Python
classes which wrap specific package functionality.  For example, in
the fsl module, the class :class:`nipype.interfaces.fsl.Bet` wraps the
``bet`` command-line tool.  Using the command-line tool, one would
specify options using flags like ``-o``, ``-m``, ``-f <f>``, etc...
However, in nipype, options are assigned to Python attributes and can
be specified in the following ways:

Options can be assigned when you first create an interface object:

.. testcode::
   
   import nipype.interfaces.fsl as fsl
   mybet = fsl.Bet(infile='foo.nii', outfile='bar.nii')
   result = mybet.run()

Options can be assigned through the ``inputs`` attribute:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.Bet()
   mybet.inputs.infile = 'foo.nii'
   mybet.inputs.outfile = 'bar.nii'
   result = mybet.run()

Options can be assigned when calling the ``run`` method:

.. testcode::

   import nipype.interfaces.fsl as fsl
   mybet = fsl.Bet()
   result = mybet.run(infile='foo.nii', outfile='bar.nii', frac=0.5)   

Getting Help
------------

In IPython_ you can view the docstrings which provide some basic
documentation and examples.

.. sourcecode:: ipython

   In [5]: fsl.Fast?
   Type:		type
   Base Class:	<type 'type'>
   String Form:	<class 'nipype.interfaces.fsl.Fast'>
   Namespace:	Interactive
   File:		/home/cburns/local/lib/python2.6/site-packages/nipype/interfaces/fsl.py
   Docstring:
       Use FSL FAST for segmenting and bias correction.

       For complete details, see the `FAST Documentation. 
       <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_

       To print out the command line help, use:
           fsl.Fast().inputs_help()

       Examples
       --------
       >>> from nipype.interfaces import fsl
       >>> faster = fsl.Fast(out_basename='myfasted')
       >>> fasted = faster.run(['file1','file2'])

       >>> faster = fsl.Fast(infiles=['filea','fileb'], out_basename='myfasted')
       >>> fasted = faster.run()

   Constructor information:
   Definition:	fsl.Fast(self, *args, **inputs)

.. sourcecode:: ipython

   In [4]: spm.Realign?
   Base Class:       <type 'type'>
   String Form:   <class 'nipype.interfaces.spm.Realign'>
   Namespace:        Interactive
   File:             /home/jagust/cindeem/src/nipy-sourceforge/nipype/trunk/nipype/interfaces/spm.py
   Docstring:
    Use spm_realign for estimating within modality rigid body alignment
    
    See Realign().spm_doc() for more information.
    
    Parameters
    ----------
    inputs : mapping
    key, value pairs that will update the Realign.inputs attributes
    see self.inputs_help() for a list of Realign.inputs attributes
    
    Attributes
    ----------
    inputs : Bunch
    a (dictionary-like) bunch of options that can be passed to 
    spm_realign via a job structure
    cmdline : string
    string used to call matlab/spm via SpmMatlabCommandLine interface

    <snip>

All of the nipype.interfaces classes have an ``inputs_help`` method
which provides information on each of the options one can assign.


.. sourcecode:: ipython

   In [7]: fsl.Bet().inputs_help()
   Parameters
   ----------
   outline : 
        generate brain surface outline overlaid onto original image
   mask : 
        generate binary brain mask
   skull : 
        generate approximate skull image
   nooutput : 
        don't generate segmented brain image output
   frac : 
        <f> fractional intensity threshold (0->1); default=0.5; smaller values give larger brain outline estimates
   vertical_gradient : 
        <g> vertical gradient in fractional intensity threshold (-1->1); default=0; positive values give larger brain outline at bottom, smaller at top

   <snip>

.. sourcecode:: ipython

   In [6]: spm.Realign().inputs_help()
           Parameters
        ----------
        
        infile: string, list
            list of filenames to realign
        write : bool, optional
            if True updates headers and generates
            resliced files prepended with  'r'
            if False just updates header files
            (default == True, will reslice)
        quality : float, optional
            0.1 = fastest, 1.0 = most precise
            (spm5 default = 0.9)
        fwhm : float, optional
            full width half maximum gaussian kernel 
            used to smooth images before realigning
            (spm default = 5.0)
        separation : float, optional
            separation in mm used to sample images
            (spm default = 4.0)
	   
    <snip>


Our :ref:`api-index` documentation provides html versions of our
docstrings and includes links to the specific package
documentation. For instance, the :class:`nipype.interfaces.fsl.Bet`
docstring has a direct link to the online BET Documentation.


FSL interface example
---------------------

Using FSL_ to realign a time_series:

.. testcode::

   import nipype.interfaces.fsl as fsl
   realigner = fsl.McFlirt()
   realigner.infile='timeseries4D.nii'
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
   realigner.inputs.infile = allepi
   result = realigner.run()

.. include:: ../links_names.txt
