.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.ants.legacy
======================


.. _nipype.interfaces.ants.legacy.GenWarpFields:


.. index:: GenWarpFields

GenWarpFields
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/ants/legacy.py#L122>`__

Wraps command **antsIntroduction.sh**


Inputs::

        [Mandatory]
        input_image: (an existing file name)
                input image to warp to template
                flag: -i %s
        reference_image: (an existing file name)
                template file to warp to
                flag: -r %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bias_field_correction: (a boolean)
                Applies bias field correction to moving image
                flag: -n 1
        dimension: (3 or 2, nipype default value: 3)
                image dimension (2 or 3)
                flag: -d %d, position: 1
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        force_proceed: (a boolean)
                force script to proceed even if headers may be incompatible
                flag: -f 1
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inverse_warp_template_labels: (a boolean)
                Applies inverse warp to the template labels to estimate label
                positions in target space (use for template-based segmentation)
                flag: -l
        max_iterations: (a list of items which are an integer (int or long))
                maximum number of iterations (must be list of integers in the form
                [J,K,L...]: J = coarsest resolution iterations, K = middle
                resolution interations, L = fine resolution iterations
                flag: -m %s
        num_threads: (an integer (int or long), nipype default value: 1)
                Number of ITK threads to use
        out_prefix: (a string, nipype default value: ants_)
                Prefix that is prepended to all output files (default = ants_)
                flag: -o %s
        quality_check: (a boolean)
                Perform a quality check of the result
                flag: -q 1
        similarity_metric: ('PR' or 'CC' or 'MI' or 'MSQ')
                Type of similartiy metric used for registration (CC = cross
                correlation, MI = mutual information, PR = probability mapping, MSQ
                = mean square difference)
                flag: -s %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformation_model: ('GR' or 'EL' or 'SY' or 'S2' or 'EX' or 'DD'
                 or 'RI' or 'RA', nipype default value: GR)
                Type of transofmration model used for registration (EL = elastic
                transformation model, SY = SyN with time, arbitrary number of time
                points, S2 = SyN with time optimized for 2 time points, GR = greedy
                SyN, EX = exponential, DD = diffeomorphic demons style exponential
                mapping, RI = purely rigid, RA = affine rigid
                flag: -t %s

Outputs::

        affine_transformation: (an existing file name)
                affine (prefix_Affine.txt)
        input_file: (an existing file name)
                input image (prefix_repaired.nii)
        inverse_warp_field: (an existing file name)
                inverse warp field (prefix_InverseWarp.nii)
        output_file: (an existing file name)
                output image (prefix_deformed.nii)
        warp_field: (an existing file name)
                warp field (prefix_Warp.nii)

.. _nipype.interfaces.ants.legacy.antsIntroduction:


.. index:: antsIntroduction

antsIntroduction
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/ants/legacy.py#L75>`__

Wraps command **antsIntroduction.sh**

Uses ANTS to generate matrices to warp data from one space to another.

Examples
~~~~~~~~

>>> from nipype.interfaces.ants.legacy import antsIntroduction
>>> warp = antsIntroduction()
>>> warp.inputs.reference_image = 'Template_6.nii'
>>> warp.inputs.input_image = 'structural.nii'
>>> warp.inputs.max_iterations = [30,90,20]
>>> warp.cmdline
'antsIntroduction.sh -d 3 -i structural.nii -m 30x90x20 -o ants_ -r Template_6.nii -t GR'

Inputs::

        [Mandatory]
        input_image: (an existing file name)
                input image to warp to template
                flag: -i %s
        reference_image: (an existing file name)
                template file to warp to
                flag: -r %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bias_field_correction: (a boolean)
                Applies bias field correction to moving image
                flag: -n 1
        dimension: (3 or 2, nipype default value: 3)
                image dimension (2 or 3)
                flag: -d %d, position: 1
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        force_proceed: (a boolean)
                force script to proceed even if headers may be incompatible
                flag: -f 1
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inverse_warp_template_labels: (a boolean)
                Applies inverse warp to the template labels to estimate label
                positions in target space (use for template-based segmentation)
                flag: -l
        max_iterations: (a list of items which are an integer (int or long))
                maximum number of iterations (must be list of integers in the form
                [J,K,L...]: J = coarsest resolution iterations, K = middle
                resolution interations, L = fine resolution iterations
                flag: -m %s
        num_threads: (an integer (int or long), nipype default value: 1)
                Number of ITK threads to use
        out_prefix: (a string, nipype default value: ants_)
                Prefix that is prepended to all output files (default = ants_)
                flag: -o %s
        quality_check: (a boolean)
                Perform a quality check of the result
                flag: -q 1
        similarity_metric: ('PR' or 'CC' or 'MI' or 'MSQ')
                Type of similartiy metric used for registration (CC = cross
                correlation, MI = mutual information, PR = probability mapping, MSQ
                = mean square difference)
                flag: -s %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformation_model: ('GR' or 'EL' or 'SY' or 'S2' or 'EX' or 'DD'
                 or 'RI' or 'RA', nipype default value: GR)
                Type of transofmration model used for registration (EL = elastic
                transformation model, SY = SyN with time, arbitrary number of time
                points, S2 = SyN with time optimized for 2 time points, GR = greedy
                SyN, EX = exponential, DD = diffeomorphic demons style exponential
                mapping, RI = purely rigid, RA = affine rigid
                flag: -t %s

Outputs::

        affine_transformation: (an existing file name)
                affine (prefix_Affine.txt)
        input_file: (an existing file name)
                input image (prefix_repaired.nii)
        inverse_warp_field: (an existing file name)
                inverse warp field (prefix_InverseWarp.nii)
        output_file: (an existing file name)
                output image (prefix_deformed.nii)
        warp_field: (an existing file name)
                warp field (prefix_Warp.nii)

.. _nipype.interfaces.ants.legacy.buildtemplateparallel:


.. index:: buildtemplateparallel

buildtemplateparallel
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/ants/legacy.py#L187>`__

Wraps command **buildtemplateparallel.sh**

Generate a optimal average template

.. warning::

  This can take a VERY long time to complete

Examples
~~~~~~~~

>>> from nipype.interfaces.ants.legacy import buildtemplateparallel
>>> tmpl = buildtemplateparallel()
>>> tmpl.inputs.in_files = ['T1.nii', 'structural.nii']
>>> tmpl.inputs.max_iterations = [30, 90, 20]
>>> tmpl.cmdline
'buildtemplateparallel.sh -d 3 -i 4 -m 30x90x20 -o antsTMPL_ -c 0 -t GR T1.nii structural.nii'

Inputs::

        [Mandatory]
        in_files: (a list of items which are an existing file name)
                list of images to generate template from
                flag: %s, position: -1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bias_field_correction: (a boolean)
                Applies bias field correction to moving image
                flag: -n 1
        dimension: (3 or 2, nipype default value: 3)
                image dimension (2 or 3)
                flag: -d %d, position: 1
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gradient_step_size: (a float)
                smaller magnitude results in more cautious steps (default = .25)
                flag: -g %f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        iteration_limit: (an integer (int or long), nipype default value: 4)
                iterations of template construction
                flag: -i %d
        max_iterations: (a list of items which are an integer (int or long))
                maximum number of iterations (must be list of integers in the form
                [J,K,L...]: J = coarsest resolution iterations, K = middle
                resolution interations, L = fine resolution iterations
                flag: -m %s
        num_cores: (an integer (int or long))
                Requires parallelization = 2 (PEXEC). Sets number of cpu cores to
                use
                flag: -j %d
                requires: parallelization
        num_threads: (an integer (int or long), nipype default value: 1)
                Number of ITK threads to use
        out_prefix: (a string, nipype default value: antsTMPL_)
                Prefix that is prepended to all output files (default = antsTMPL_)
                flag: -o %s
        parallelization: (0 or 1 or 2, nipype default value: 0)
                control for parallel processing (0 = serial, 1 = use PBS, 2 = use
                PEXEC, 3 = use Apple XGrid
                flag: -c %d
        rigid_body_registration: (a boolean)
                registers inputs before creating template (useful if no initial
                template available)
                flag: -r 1
        similarity_metric: ('PR' or 'CC' or 'MI' or 'MSQ')
                Type of similartiy metric used for registration (CC = cross
                correlation, MI = mutual information, PR = probability mapping, MSQ
                = mean square difference)
                flag: -s %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformation_model: ('GR' or 'EL' or 'SY' or 'S2' or 'EX' or 'DD',
                 nipype default value: GR)
                Type of transofmration model used for registration (EL = elastic
                transformation model, SY = SyN with time, arbitrary number of time
                points, S2 = SyN with time optimized for 2 time points, GR = greedy
                SyN, EX = exponential, DD = diffeomorphic demons style exponential
                mapping
                flag: -t %s
        use_first_as_target: (a boolean)
                uses first volume as target of all inputs. When not used, an
                unbiased average image is used to start.

Outputs::

        final_template_file: (an existing file name)
                final ANTS template
        subject_outfiles: (a list of items which are an existing file name)
                Outputs for each input image. Includes warp field, inverse warp,
                Affine, original image (repaired) and warped image (deformed)
        template_files: (a list of items which are an existing file name)
                Templates from different stages of iteration
