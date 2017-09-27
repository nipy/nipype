.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.fsl.model
====================


.. _nipype.interfaces.fsl.model.Cluster:


.. index:: Cluster

Cluster
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1630>`__

Wraps command **cluster**

Uses FSL cluster to perform clustering on statistical output

Examples
~~~~~~~~

>>> cl = Cluster()
>>> cl.inputs.threshold = 2.3
>>> cl.inputs.in_file = 'zstat1.nii.gz'
>>> cl.inputs.out_localmax_txt_file = 'stats.txt'
>>> cl.cmdline
'cluster --in=zstat1.nii.gz --olmax=stats.txt --thresh=2.3000000000'

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input volume
                flag: --in=%s
        threshold: (a float)
                threshold for input volume
                flag: --thresh=%.10f

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        connectivity: (an integer (int or long))
                the connectivity of voxels (default 26)
                flag: --connectivity=%d
        cope_file: (a file name)
                cope volume
                flag: --cope=%s
        dlh: (a float)
                smoothness estimate = sqrt(det(Lambda))
                flag: --dlh=%.10f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        find_min: (a boolean)
                find minima instead of maxima
        fractional: (a boolean)
                interprets the threshold as a fraction of the robust range
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        minclustersize: (a boolean)
                prints out minimum significant cluster size
                flag: --minclustersize
        no_table: (a boolean)
                suppresses printing of the table info
        num_maxima: (an integer (int or long))
                no of local maxima to report
                flag: --num=%d
        out_index_file: (a boolean or a file name)
                output of cluster index (in size order)
                flag: --oindex=%s
        out_localmax_txt_file: (a boolean or a file name)
                local maxima text file
                flag: --olmax=%s
        out_localmax_vol_file: (a boolean or a file name)
                output of local maxima volume
                flag: --olmaxim=%s
        out_max_file: (a boolean or a file name)
                filename for output of max image
                flag: --omax=%s
        out_mean_file: (a boolean or a file name)
                filename for output of mean image
                flag: --omean=%s
        out_pval_file: (a boolean or a file name)
                filename for image output of log pvals
                flag: --opvals=%s
        out_size_file: (a boolean or a file name)
                filename for output of size image
                flag: --osize=%s
        out_threshold_file: (a boolean or a file name)
                thresholded image
                flag: --othresh=%s
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        peak_distance: (a float)
                minimum distance between local maxima/minima, in mm (default 0)
                flag: --peakdist=%.10f
        pthreshold: (a float)
                p-threshold for clusters
                flag: --pthresh=%.10f
                requires: dlh, volume
        std_space_file: (a file name)
                filename for standard-space volume
                flag: --stdvol=%s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        use_mm: (a boolean)
                use mm, not voxel, coordinates
        volume: (an integer (int or long))
                number of voxels in the mask
                flag: --volume=%d
        warpfield_file: (a file name)
                file contining warpfield
                flag: --warpvol=%s
        xfm_file: (a file name)
                filename for Linear: input->standard-space transform. Non-linear:
                input->highres transform
                flag: --xfm=%s

Outputs::

        index_file: (a file name)
                output of cluster index (in size order)
        localmax_txt_file: (a file name)
                local maxima text file
        localmax_vol_file: (a file name)
                output of local maxima volume
        max_file: (a file name)
                filename for output of max image
        mean_file: (a file name)
                filename for output of mean image
        pval_file: (a file name)
                filename for image output of log pvals
        size_file: (a file name)
                filename for output of size image
        threshold_file: (a file name)
                thresholded image

.. _nipype.interfaces.fsl.model.ContrastMgr:


.. index:: ContrastMgr

ContrastMgr
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1006>`__

Wraps command **contrast_mgr**

Use FSL contrast_mgr command to evaluate contrasts

In interface mode this file assumes that all the required inputs are in the
same location.

Inputs::

        [Mandatory]
        corrections: (an existing file name)
                statistical corrections used within FILM modelling
        dof_file: (an existing file name)
                degrees of freedom
        param_estimates: (a list of items which are an existing file name)
                Parameter estimates for each column of the design matrix
        sigmasquareds: (an existing file name)
                summary of residuals, See Woolrich, et. al., 2001
        tcon_file: (an existing file name)
                contrast file containing T-contrasts
                flag: %s, position: -1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        contrast_num: (an integer >= 1)
                contrast number to start labeling copes from
                flag: -cope
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fcon_file: (an existing file name)
                contrast file containing F-contrasts
                flag: -f %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        suffix: (a string)
                suffix to put on the end of the cope filename before the contrast
                number, default is nothing
                flag: -suffix %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        copes: (a list of items which are an existing file name)
                Contrast estimates for each contrast
        fstats: (a list of items which are an existing file name)
                f-stat file for each contrast
        neffs: (a list of items which are an existing file name)
                neff file ?? for each contrast
        tstats: (a list of items which are an existing file name)
                t-stat file for each contrast
        varcopes: (a list of items which are an existing file name)
                Variance estimates for each contrast
        zfstats: (a list of items which are an existing file name)
                z-stat file for each F contrast
        zstats: (a list of items which are an existing file name)
                z-stat file for each contrast

.. _nipype.interfaces.fsl.model.FEAT:


.. index:: FEAT

FEAT
----

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L378>`__

Wraps command **feat**

Uses FSL feat to calculate first level stats

Inputs::

        [Mandatory]
        fsf_file: (an existing file name)
                File specifying the feat design spec file
                flag: %s, position: 0

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        feat_dir: (an existing directory name)

.. _nipype.interfaces.fsl.model.FEATModel:


.. index:: FEATModel

FEATModel
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L433>`__

Wraps command **feat_model**

Uses FSL feat_model to generate design.mat files

Inputs::

        [Mandatory]
        ev_files: (a list of items which are an existing file name)
                Event spec files generated by level1design
                flag: %s, position: 1
        fsf_file: (an existing file name)
                File specifying the feat design spec file
                flag: %s, position: 0

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        con_file: (an existing file name)
                Contrast file containing contrast vectors
        design_cov: (an existing file name)
                Graphical representation of design covariance
        design_file: (an existing file name)
                Mat file containing ascii matrix for design
        design_image: (an existing file name)
                Graphical representation of design matrix
        fcon_file: (a file name)
                Contrast file containing contrast vectors

.. _nipype.interfaces.fsl.model.FEATRegister:


.. index:: FEATRegister

FEATRegister
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L763>`__

Register feat directories to a specific standard

Inputs::

        [Mandatory]
        feat_dirs: (a list of items which are an existing directory name)
                Lower level feat dirs
        reg_image: (an existing file name)
                image to register to (will be treated as standard)

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        reg_dof: (an integer (int or long), nipype default value: 12)
                registration degrees of freedom

Outputs::

        fsf_file: (an existing file name)
                FSL feat specification file

.. _nipype.interfaces.fsl.model.FILMGLS:


.. index:: FILMGLS

FILMGLS
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L611>`__

Wraps command **film_gls**

Use FSL film_gls command to fit a design matrix to voxel timeseries

Examples
~~~~~~~~

Initialize with no options, assigning them when calling run:

>>> from nipype.interfaces import fsl
>>> fgls = fsl.FILMGLS()
>>> res = fgls.run('in_file', 'design_file', 'thresh', rn='stats') #doctest: +SKIP

Assign options through the ``inputs`` attribute:

>>> fgls = fsl.FILMGLS()
>>> fgls.inputs.in_file = 'functional.nii'
>>> fgls.inputs.design_file = 'design.mat'
>>> fgls.inputs.threshold = 10
>>> fgls.inputs.results_dir = 'stats'
>>> res = fgls.run() #doctest: +SKIP

Specify options when creating an instance:

>>> fgls = fsl.FILMGLS(in_file='functional.nii', design_file='design.mat', threshold=10, results_dir='stats')
>>> res = fgls.run() #doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input data file
                flag: --in=%s, position: -3

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        autocorr_estimate_only: (a boolean)
                perform autocorrelation estimation only
                flag: --ac
                mutually_exclusive: autocorr_estimate_only, fit_armodel,
                 tukey_window, multitaper_product, use_pava, autocorr_noestimate
        autocorr_noestimate: (a boolean)
                do not estimate autocorrs
                flag: --noest
                mutually_exclusive: autocorr_estimate_only, fit_armodel,
                 tukey_window, multitaper_product, use_pava, autocorr_noestimate
        brightness_threshold: (an integer >= 0)
                susan brightness threshold, otherwise it is estimated
                flag: --epith=%d
        design_file: (an existing file name)
                design matrix file
                flag: --pd=%s, position: -2
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fcon_file: (an existing file name)
                contrast file containing F-contrasts
                flag: --fcon=%s
        fit_armodel: (a boolean)
                fits autoregressive model - default is to use tukey with
                M=sqrt(numvols)
                flag: --ar
                mutually_exclusive: autocorr_estimate_only, fit_armodel,
                 tukey_window, multitaper_product, use_pava, autocorr_noestimate
        full_data: (a boolean)
                output full data
                flag: -v
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        mask_size: (an integer (int or long))
                susan mask size
                flag: --ms=%d
        mode: ('volumetric' or 'surface')
                Type of analysis to be done
                flag: --mode=%s
        multitaper_product: (an integer (int or long))
                multitapering with slepian tapers and num is the time-bandwidth
                product
                flag: --mt=%d
                mutually_exclusive: autocorr_estimate_only, fit_armodel,
                 tukey_window, multitaper_product, use_pava, autocorr_noestimate
        output_pwdata: (a boolean)
                output prewhitened data and average design matrix
                flag: --outputPWdata
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        results_dir: (a directory name, nipype default value: results)
                directory to store results in
                flag: --rn=%s
        smooth_autocorr: (a boolean)
                Smooth auto corr estimates
                flag: --sa
        surface: (an existing file name)
                input surface for autocorr smoothing in surface-based analyses
                flag: --in2=%s
        tcon_file: (an existing file name)
                contrast file containing T-contrasts
                flag: --con=%s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        threshold: (a float, nipype default value: 0.0)
                threshold
                flag: --thr=%f, position: -1
        tukey_window: (an integer (int or long))
                tukey window size to estimate autocorr
                flag: --tukey=%d
                mutually_exclusive: autocorr_estimate_only, fit_armodel,
                 tukey_window, multitaper_product, use_pava, autocorr_noestimate
        use_pava: (a boolean)
                estimates autocorr using PAVA
                flag: --pava

Outputs::

        copes: (a list of items which are an existing file name)
                Contrast estimates for each contrast
        dof_file: (an existing file name)
                degrees of freedom
        fstats: (a list of items which are an existing file name)
                f-stat file for each contrast
        logfile: (an existing file name)
                FILM run logfile
        param_estimates: (a list of items which are an existing file name)
                Parameter estimates for each column of the design matrix
        residual4d: (an existing file name)
                Model fit residual mean-squared error for each time point
        results_dir: (an existing directory name)
                directory storing model estimation output
        sigmasquareds: (an existing file name)
                summary of residuals, See Woolrich, et. al., 2001
        thresholdac: (an existing file name)
                The FILM autocorrelation parameters
        tstats: (a list of items which are an existing file name)
                t-stat file for each contrast
        varcopes: (a list of items which are an existing file name)
                Variance estimates for each contrast
        zfstats: (a list of items which are an existing file name)
                z-stat file for each F contrast
        zstats: (a list of items which are an existing file name)
                z-stat file for each contrast

.. _nipype.interfaces.fsl.model.FLAMEO:


.. index:: FLAMEO

FLAMEO
------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L866>`__

Wraps command **flameo**

Use FSL flameo command to perform higher level model fits

Examples
~~~~~~~~

Initialize FLAMEO with no options, assigning them when calling run:

>>> from nipype.interfaces import fsl
>>> import os
>>> flameo = fsl.FLAMEO(cope_file='cope.nii.gz',                             var_cope_file='varcope.nii.gz',                             cov_split_file='cov_split.mat',                             design_file='design.mat',                             t_con_file='design.con',                             mask_file='mask.nii',                             run_mode='fe')
>>> flameo.cmdline
'flameo --copefile=cope.nii.gz --covsplitfile=cov_split.mat --designfile=design.mat --ld=stats --maskfile=mask.nii --runmode=fe --tcontrastsfile=design.con --varcopefile=varcope.nii.gz'

Inputs::

        [Mandatory]
        cope_file: (an existing file name)
                cope regressor data file
                flag: --copefile=%s
        cov_split_file: (an existing file name)
                ascii matrix specifying the groups the covariance is split into
                flag: --covsplitfile=%s
        design_file: (an existing file name)
                design matrix file
                flag: --designfile=%s
        mask_file: (an existing file name)
                mask file
                flag: --maskfile=%s
        run_mode: ('fe' or 'ols' or 'flame1' or 'flame12')
                inference to perform
                flag: --runmode=%s
        t_con_file: (an existing file name)
                ascii matrix specifying t-contrasts
                flag: --tcontrastsfile=%s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        burnin: (an integer (int or long))
                number of jumps at start of mcmc to be discarded
                flag: --burnin=%d
        dof_var_cope_file: (an existing file name)
                dof data file for varcope data
                flag: --dofvarcopefile=%s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        f_con_file: (an existing file name)
                ascii matrix specifying f-contrasts
                flag: --fcontrastsfile=%s
        fix_mean: (a boolean)
                fix mean for tfit
                flag: --fixmean
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        infer_outliers: (a boolean)
                infer outliers - not for fe
                flag: --inferoutliers
        log_dir: (a directory name, nipype default value: stats)
                flag: --ld=%s
        n_jumps: (an integer (int or long))
                number of jumps made by mcmc
                flag: --njumps=%d
        no_pe_outputs: (a boolean)
                do not output pe files
                flag: --nopeoutput
        outlier_iter: (an integer (int or long))
                Number of max iterations to use when inferring outliers. Default is
                12.
                flag: --ioni=%d
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        sample_every: (an integer (int or long))
                number of jumps for each sample
                flag: --sampleevery=%d
        sigma_dofs: (an integer (int or long))
                sigma (in mm) to use for Gaussian smoothing the DOFs in FLAME 2.
                Default is 1mm, -1 indicates no smoothing
                flag: --sigma_dofs=%d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        var_cope_file: (an existing file name)
                varcope weightings data file
                flag: --varcopefile=%s

Outputs::

        copes: (a list of items which are an existing file name)
                Contrast estimates for each contrast
        fstats: (a list of items which are an existing file name)
                f-stat file for each contrast
        mrefvars: (a list of items which are an existing file name)
                mean random effect variances for each contrast
        pes: (a list of items which are an existing file name)
                Parameter estimates for each column of the design matrix for each
                voxel
        res4d: (a list of items which are an existing file name)
                Model fit residual mean-squared error for each time point
        stats_dir: (a directory name)
                directory storing model estimation output
        tdof: (a list of items which are an existing file name)
                temporal dof file for each contrast
        tstats: (a list of items which are an existing file name)
                t-stat file for each contrast
        var_copes: (a list of items which are an existing file name)
                Variance estimates for each contrast
        weights: (a list of items which are an existing file name)
                weights file for each contrast
        zfstats: (a list of items which are an existing file name)
                z stat file for each f contrast
        zstats: (a list of items which are an existing file name)
                z-stat file for each contrast

.. _nipype.interfaces.fsl.model.GLM:


.. index:: GLM

GLM
---

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1905>`__

Wraps command **fsl_glm**

FSL GLM:

Example
~~~~~~~
>>> import nipype.interfaces.fsl as fsl
>>> glm = fsl.GLM(in_file='functional.nii', design='maps.nii', output_type='NIFTI')
>>> glm.cmdline
'fsl_glm -i functional.nii -d maps.nii -o functional_glm.nii'

Inputs::

        [Mandatory]
        design: (an existing file name)
                file name of the GLM design matrix (text time courses for temporal
                regression or an image file for spatial regression)
                flag: -d %s, position: 2
        in_file: (an existing file name)
                input file name (text matrix or 3D/4D image file)
                flag: -i %s, position: 1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        contrasts: (an existing file name)
                matrix of t-statics contrasts
                flag: -c %s
        dat_norm: (a boolean)
                switch on normalization of the data time series to unit std
                deviation
                flag: --dat_norm
        demean: (a boolean)
                switch on demeaining of design and data
                flag: --demean
        des_norm: (a boolean)
                switch on normalization of the design matrix columns to unit std
                deviation
                flag: --des_norm
        dof: (an integer (int or long))
                set degrees of freedom explicitly
                flag: --dof=%d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        mask: (an existing file name)
                mask image file name if input is image
                flag: -m %s
        out_cope: (a file name)
                output file name for COPE (either as txt or image
                flag: --out_cope=%s
        out_data_name: (a file name)
                output file name for pre-processed data
                flag: --out_data=%s
        out_f_name: (a file name)
                output file name for F-value of full model fit
                flag: --out_f=%s
        out_file: (a file name)
                filename for GLM parameter estimates (GLM betas)
                flag: -o %s, position: 3
        out_p_name: (a file name)
                output file name for p-values of Z-stats (either as text file or
                image)
                flag: --out_p=%s
        out_pf_name: (a file name)
                output file name for p-value for full model fit
                flag: --out_pf=%s
        out_res_name: (a file name)
                output file name for residuals
                flag: --out_res=%s
        out_sigsq_name: (a file name)
                output file name for residual noise variance sigma-square
                flag: --out_sigsq=%s
        out_t_name: (a file name)
                output file name for t-stats (either as txt or image
                flag: --out_t=%s
        out_varcb_name: (a file name)
                output file name for variance of COPEs
                flag: --out_varcb=%s
        out_vnscales_name: (a file name)
                output file name for scaling factors for variance normalisation
                flag: --out_vnscales=%s
        out_z_name: (a file name)
                output file name for Z-stats (either as txt or image
                flag: --out_z=%s
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        var_norm: (a boolean)
                perform MELODIC variance-normalisation on data
                flag: --vn

Outputs::

        out_cope: (a list of items which are an existing file name)
                output file name for COPEs (either as text file or image)
        out_data: (a list of items which are an existing file name)
                output file for preprocessed data
        out_f: (a list of items which are an existing file name)
                output file name for F-value of full model fit
        out_file: (an existing file name)
                file name of GLM parameters (if generated)
        out_p: (a list of items which are an existing file name)
                output file name for p-values of Z-stats (either as text file or
                image)
        out_pf: (a list of items which are an existing file name)
                output file name for p-value for full model fit
        out_res: (a list of items which are an existing file name)
                output file name for residuals
        out_sigsq: (a list of items which are an existing file name)
                output file name for residual noise variance sigma-square
        out_t: (a list of items which are an existing file name)
                output file name for t-stats (either as text file or image)
        out_varcb: (a list of items which are an existing file name)
                output file name for variance of COPEs
        out_vnscales: (a list of items which are an existing file name)
                output file name for scaling factors for variance normalisation
        out_z: (a list of items which are an existing file name)
                output file name for COPEs (either as text file or image)

.. _nipype.interfaces.fsl.model.L2Model:


.. index:: L2Model

L2Model
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1113>`__

Generate subject specific second level model

Examples
~~~~~~~~

>>> from nipype.interfaces.fsl import L2Model
>>> model = L2Model(num_copes=3) # 3 sessions

Inputs::

        [Mandatory]
        num_copes: (an integer >= 1)
                number of copes to be combined

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run

Outputs::

        design_con: (an existing file name)
                design contrast file
        design_grp: (an existing file name)
                design group file
        design_mat: (an existing file name)
                design matrix file

.. _nipype.interfaces.fsl.model.Level1Design:


.. index:: Level1Design

Level1Design
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L98>`__

Generate FEAT specific files

Examples
~~~~~~~~

>>> level1design = Level1Design()
>>> level1design.inputs.interscan_interval = 2.5
>>> level1design.inputs.bases = {'dgamma':{'derivs': False}}
>>> level1design.inputs.session_info = 'session_info.npz'
>>> level1design.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        bases: (a dictionary with keys which are 'dgamma' and with values
                 which are a dictionary with keys which are 'derivs' and with values
                 which are a boolean or a dictionary with keys which are 'gamma' and
                 with values which are a dictionary with keys which are 'derivs' and
                 with values which are a boolean or a dictionary with keys which are
                 'none' and with values which are None)
                name of basis function and options e.g., {'dgamma': {'derivs':
                True}}
        interscan_interval: (a float)
                Interscan interval (in secs)
        model_serial_correlations: (a boolean)
                Option to model serial correlations using an autoregressive
                estimator (order 1). Setting this option is only useful in the
                context of the fsf file. If you set this to False, you need to
                repeat this option for FILMGLS by setting autocorr_noestimate to
                True
        session_info: (any value)
                Session specific information generated by ``modelgen.SpecifyModel``

        [Optional]
        contrasts: (a list of items which are a tuple of the form: (a string,
                 'T', a list of items which are a string, a list of items which are
                 a float) or a tuple of the form: (a string, 'T', a list of items
                 which are a string, a list of items which are a float, a list of
                 items which are a float) or a tuple of the form: (a string, 'F', a
                 list of items which are a tuple of the form: (a string, 'T', a list
                 of items which are a string, a list of items which are a float) or
                 a tuple of the form: (a string, 'T', a list of items which are a
                 string, a list of items which are a float, a list of items which
                 are a float)))
                List of contrasts with each contrast being a list of the form -
                [('name', 'stat', [condition list], [weight list], [session list])].
                if session list is None or not provided, all sessions are used. For
                F contrasts, the condition list should contain previously defined
                T-contrasts.
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run

Outputs::

        ev_files: (a list of items which are a list of items which are an
                 existing file name)
                condition information files
        fsf_files: (a list of items which are an existing file name)
                FSL feat specification files

.. _nipype.interfaces.fsl.model.MELODIC:


.. index:: MELODIC

MELODIC
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1466>`__

Wraps command **melodic**

Multivariate Exploratory Linear Optimised Decomposition into Independent Components

Examples
~~~~~~~~

>>> melodic_setup = MELODIC()
>>> melodic_setup.inputs.approach = 'tica'
>>> melodic_setup.inputs.in_files = ['functional.nii', 'functional2.nii', 'functional3.nii']
>>> melodic_setup.inputs.no_bet = True
>>> melodic_setup.inputs.bg_threshold = 10
>>> melodic_setup.inputs.tr_sec = 1.5
>>> melodic_setup.inputs.mm_thresh = 0.5
>>> melodic_setup.inputs.out_stats = True
>>> melodic_setup.inputs.t_des = 'timeDesign.mat'
>>> melodic_setup.inputs.t_con = 'timeDesign.con'
>>> melodic_setup.inputs.s_des = 'subjectDesign.mat'
>>> melodic_setup.inputs.s_con = 'subjectDesign.con'
>>> melodic_setup.inputs.out_dir = 'groupICA.out'
>>> melodic_setup.cmdline
'melodic -i functional.nii,functional2.nii,functional3.nii -a tica --bgthreshold=10.000000 --mmthresh=0.500000 --nobet -o groupICA.out --Ostats --Scon=subjectDesign.con --Sdes=subjectDesign.mat --Tcon=timeDesign.con --Tdes=timeDesign.mat --tr=1.500000'
>>> melodic_setup.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_files: (a list of items which are an existing file name)
                input file names (either single file name or a list)
                flag: -i %s, position: 0

        [Optional]
        ICs: (an existing file name)
                filename of the IC components file for mixture modelling
                flag: --ICs=%s
        approach: (a string)
                approach for decomposition, 2D: defl, symm (default), 3D: tica
                (default), concat
                flag: -a %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        bg_image: (an existing file name)
                specify background image for report (default: mean image)
                flag: --bgimage=%s
        bg_threshold: (a float)
                brain/non-brain threshold used to mask non-brain voxels, as a
                percentage (only if --nobet selected)
                flag: --bgthreshold=%f
        cov_weight: (a float)
                voxel-wise weights for the covariance matrix (e.g. segmentation
                information)
                flag: --covarweight=%f
        dim: (an integer (int or long))
                dimensionality reduction into #num dimensions(default: automatic
                estimation)
                flag: -d %d
        dim_est: (a string)
                use specific dim. estimation technique: lap, bic, mdl, aic, mean
                (default: lap)
                flag: --dimest=%s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        epsilon: (a float)
                minimum error change
                flag: --eps=%f
        epsilonS: (a float)
                minimum error change for rank-1 approximation in TICA
                flag: --epsS=%f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        log_power: (a boolean)
                calculate log of power for frequency spectrum
                flag: --logPower
        mask: (an existing file name)
                file name of mask for thresholding
                flag: -m %s
        max_restart: (an integer (int or long))
                maximum number of restarts
                flag: --maxrestart=%d
        maxit: (an integer (int or long))
                maximum number of iterations before restart
                flag: --maxit=%d
        mix: (an existing file name)
                mixing matrix for mixture modelling / filtering
                flag: --mix=%s
        mm_thresh: (a float)
                threshold for Mixture Model based inference
                flag: --mmthresh=%f
        no_bet: (a boolean)
                switch off BET
                flag: --nobet
        no_mask: (a boolean)
                switch off masking
                flag: --nomask
        no_mm: (a boolean)
                switch off mixture modelling on IC maps
                flag: --no_mm
        non_linearity: (a string)
                nonlinearity: gauss, tanh, pow3, pow4
                flag: --nl=%s
        num_ICs: (an integer (int or long))
                number of IC's to extract (for deflation approach)
                flag: -n %d
        out_all: (a boolean)
                output everything
                flag: --Oall
        out_dir: (a directory name)
                output directory name
                flag: -o %s
        out_mean: (a boolean)
                output mean volume
                flag: --Omean
        out_orig: (a boolean)
                output the original ICs
                flag: --Oorig
        out_pca: (a boolean)
                output PCA results
                flag: --Opca
        out_stats: (a boolean)
                output thresholded maps and probability maps
                flag: --Ostats
        out_unmix: (a boolean)
                output unmixing matrix
                flag: --Ounmix
        out_white: (a boolean)
                output whitening/dewhitening matrices
                flag: --Owhite
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        pbsc: (a boolean)
                switch off conversion to percent BOLD signal change
                flag: --pbsc
        rem_cmp: (a list of items which are an integer (int or long))
                component numbers to remove
                flag: -f %d
        remove_deriv: (a boolean)
                removes every second entry in paradigm file (EV derivatives)
                flag: --remove_deriv
        report: (a boolean)
                generate Melodic web report
                flag: --report
        report_maps: (a string)
                control string for spatial map images (see slicer)
                flag: --report_maps=%s
        s_con: (an existing file name)
                t-contrast matrix across subject-domain
                flag: --Scon=%s
        s_des: (an existing file name)
                design matrix across subject-domain
                flag: --Sdes=%s
        sep_vn: (a boolean)
                switch off joined variance normalization
                flag: --sep_vn
        sep_whiten: (a boolean)
                switch on separate whitening
                flag: --sep_whiten
        smode: (an existing file name)
                matrix of session modes for report generation
                flag: --smode=%s
        t_con: (an existing file name)
                t-contrast matrix across time-domain
                flag: --Tcon=%s
        t_des: (an existing file name)
                design matrix across time-domain
                flag: --Tdes=%s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tr_sec: (a float)
                TR in seconds
                flag: --tr=%f
        update_mask: (a boolean)
                switch off mask updating
                flag: --update_mask
        var_norm: (a boolean)
                switch off variance normalization
                flag: --vn

Outputs::

        out_dir: (an existing directory name)
        report_dir: (an existing directory name)

.. _nipype.interfaces.fsl.model.MultipleRegressDesign:


.. index:: MultipleRegressDesign

MultipleRegressDesign
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1212>`__

Generate multiple regression design

.. note::
  FSL does not demean columns for higher level analysis.

Please see `FSL documentation <http://www.fmrib.ox.ac.uk/fsl/feat5/detail.html#higher>`_
for more details on model specification for higher level analysis.

Examples
~~~~~~~~

>>> from nipype.interfaces.fsl import MultipleRegressDesign
>>> model = MultipleRegressDesign()
>>> model.inputs.contrasts = [['group mean', 'T',['reg1'],[1]]]
>>> model.inputs.regressors = dict(reg1=[1, 1, 1], reg2=[2.,-4, 3])
>>> model.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        contrasts: (a list of items which are a tuple of the form: (a string,
                 'T', a list of items which are a string, a list of items which are
                 a float) or a tuple of the form: (a string, 'F', a list of items
                 which are a tuple of the form: (a string, 'T', a list of items
                 which are a string, a list of items which are a float)))
                List of contrasts with each contrast being a list of the form -
                [('name', 'stat', [condition list], [weight list])]. if session list
                is None or not provided, all sessions are used. For F contrasts, the
                condition list should contain previously defined T-contrasts without
                any weight list.
        regressors: (a dictionary with keys which are a string and with
                 values which are a list of items which are a float)
                dictionary containing named lists of regressors

        [Optional]
        groups: (a list of items which are an integer (int or long))
                list of group identifiers (defaults to single group)
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run

Outputs::

        design_con: (an existing file name)
                design t-contrast file
        design_fts: (an existing file name)
                design f-contrast file
        design_grp: (an existing file name)
                design group file
        design_mat: (an existing file name)
                design matrix file

.. _nipype.interfaces.fsl.model.Randomise:


.. index:: Randomise

Randomise
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1764>`__

Wraps command **randomise**

XXX UNSTABLE DO NOT USE

FSL Randomise: feeds the 4D projected FA data into GLM
modelling and thresholding
in order to find voxels which correlate with your model

Example
~~~~~~~
>>> import nipype.interfaces.fsl as fsl
>>> rand = fsl.Randomise(in_file='allFA.nii', mask = 'mask.nii', tcon='design.con', design_mat='design.mat')
>>> rand.cmdline
'randomise -i allFA.nii -o "tbss_" -d design.mat -t design.con -m mask.nii'

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                4D input file
                flag: -i %s, position: 0

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        base_name: (a string, nipype default value: tbss_)
                the rootname that all generated files will have
                flag: -o "%s", position: 1
        c_thresh: (a float)
                carry out cluster-based thresholding
                flag: -c %.2f
        cm_thresh: (a float)
                carry out cluster-mass-based thresholding
                flag: -C %.2f
        demean: (a boolean)
                demean data temporally before model fitting
                flag: -D
        design_mat: (an existing file name)
                design matrix file
                flag: -d %s, position: 2
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        f_c_thresh: (a float)
                carry out f cluster thresholding
                flag: -F %.2f
        f_cm_thresh: (a float)
                carry out f cluster-mass thresholding
                flag: -S %.2f
        f_only: (a boolean)
                calculate f-statistics only
                flag: --f_only
        fcon: (an existing file name)
                f contrasts file
                flag: -f %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        mask: (an existing file name)
                mask image
                flag: -m %s
        num_perm: (an integer (int or long))
                number of permutations (default 5000, set to 0 for exhaustive)
                flag: -n %d
        one_sample_group_mean: (a boolean)
                perform 1-sample group-mean test instead of generic permutation test
                flag: -1
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        p_vec_n_dist_files: (a boolean)
                output permutation vector and null distribution text files
                flag: -P
        raw_stats_imgs: (a boolean)
                output raw ( unpermuted ) statistic images
                flag: -R
        seed: (an integer (int or long))
                specific integer seed for random number generator
                flag: --seed=%d
        show_info_parallel_mode: (a boolean)
                print out information required for parallel mode and exit
                flag: -Q
        show_total_perms: (a boolean)
                print out how many unique permutations would be generated and exit
                flag: -q
        tcon: (an existing file name)
                t contrasts file
                flag: -t %s, position: 3
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tfce: (a boolean)
                carry out Threshold-Free Cluster Enhancement
                flag: -T
        tfce2D: (a boolean)
                carry out Threshold-Free Cluster Enhancement with 2D optimisation
                flag: --T2
        tfce_C: (a float)
                TFCE connectivity (6 or 26; default=6)
                flag: --tfce_C=%.2f
        tfce_E: (a float)
                TFCE extent parameter (default=0.5)
                flag: --tfce_E=%.2f
        tfce_H: (a float)
                TFCE height parameter (default=2)
                flag: --tfce_H=%.2f
        var_smooth: (an integer (int or long))
                use variance smoothing (std is in mm)
                flag: -v %d
        vox_p_values: (a boolean)
                output voxelwise (corrected and uncorrected) p-value images
                flag: -x
        x_block_labels: (an existing file name)
                exchangeability block labels file
                flag: -e %s

Outputs::

        f_corrected_p_files: (a list of items which are an existing file
                 name)
                f contrast FWE (Family-wise error) corrected p values files
        f_p_files: (a list of items which are an existing file name)
                f contrast uncorrected p values files
        fstat_files: (a list of items which are an existing file name)
                f contrast raw statistic
        t_corrected_p_files: (a list of items which are an existing file
                 name)
                t contrast FWE (Family-wise error) corrected p values files
        t_p_files: (a list of items which are an existing file name)
                f contrast uncorrected p values files
        tstat_files: (a list of items which are an existing file name)
                t contrast raw statistic

.. _nipype.interfaces.fsl.model.SMM:


.. index:: SMM

SMM
---

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1355>`__

Wraps command **mm --ld=logdir**

Spatial Mixture Modelling. For more detail on the spatial mixture modelling see
Mixture Models with Adaptive Spatial Regularisation for Segmentation with an Application to FMRI Data;
Woolrich, M., Behrens, T., Beckmann, C., and Smith, S.; IEEE Trans. Medical Imaging, 24(1):1-11, 2005.

Inputs::

        [Mandatory]
        mask: (an existing file name)
                mask file
                flag: --mask="%s", position: 1
        spatial_data_file: (an existing file name)
                statistics spatial map
                flag: --sdf="%s", position: 0

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        no_deactivation_class: (a boolean)
                enforces no deactivation class
                flag: --zfstatmode, position: 2
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        activation_p_map: (an existing file name)
        deactivation_p_map: (an existing file name)
        null_p_map: (an existing file name)

.. _nipype.interfaces.fsl.model.SmoothEstimate:


.. index:: SmoothEstimate

SmoothEstimate
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/fsl/model.py#L1531>`__

Wraps command **smoothest**

Estimates the smoothness of an image

Examples
~~~~~~~~

>>> est = SmoothEstimate()
>>> est.inputs.zstat_file = 'zstat1.nii.gz'
>>> est.inputs.mask_file = 'mask.nii'
>>> est.cmdline
'smoothest --mask=mask.nii --zstat=zstat1.nii.gz'

Inputs::

        [Mandatory]
        dof: (an integer (int or long))
                number of degrees of freedom
                flag: --dof=%d
                mutually_exclusive: zstat_file
        mask_file: (an existing file name)
                brain mask volume
                flag: --mask=%s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        output_type: ('NIFTI_PAIR' or 'NIFTI_PAIR_GZ' or 'NIFTI_GZ' or
                 'NIFTI')
                FSL output type
        residual_fit_file: (an existing file name)
                residual-fit image file
                flag: --res=%s
                requires: dof
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        zstat_file: (an existing file name)
                zstat image file
                flag: --zstat=%s
                mutually_exclusive: dof

Outputs::

        dlh: (a float)
                smoothness estimate sqrt(det(Lambda))
        resels: (a float)
                number of resels
        volume: (an integer (int or long))
                number of voxels in mask
