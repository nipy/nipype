.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.nitime.analysis
==========================


.. _nipype.interfaces.nitime.analysis.CoherenceAnalyzer:


.. index:: CoherenceAnalyzer

CoherenceAnalyzer
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/nitime/analysis.py#L94>`__

Inputs::

        [Mandatory]

        [Optional]
        NFFT: (an integer >= 32, nipype default value: 64)
                This is the size of the window used for the spectral estimation. Use
                values between 32 and the number of samples in your time-
                series.(Defaults to 64.)
        TR: (a float)
                The TR used to collect the datain your csv file <in_file>
        figure_type: ('matrix' or 'network', nipype default value: matrix)
                The type of plot to generate, where 'matrix' denotes a matrix image
                and'network' denotes a graph representation. Default: 'matrix'
        frequency_range: (a list of from 2 to 2 items which are any value,
                 nipype default value: [0.02, 0.15])
                The range of frequencies overwhich the analysis will
                average.[low,high] (Default [0.02,0.15]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_TS: (any value)
                a nitime TimeSeries object
        in_file: (an existing file name)
                csv file with ROIs on the columns and time-points on the rows. ROI
                names at the top row
                requires: TR
        n_overlap: (an integer >= 0, nipype default value: 0)
                The number of samples which overlapbetween subsequent
                windows.(Defaults to 0)
        output_csv_file: (a file name)
                File to write outputs (coherence,time-delay) with file-names:
                file_name_ {coherence,timedelay}
        output_figure_file: (a file name)
                File to write output figures (coherence,time-delay) with file-names:
                file_name_{coherence,timedelay}. Possible formats:
                .png,.svg,.pdf,.jpg,...

Outputs::

        coherence_array: (an array)
                The pairwise coherence valuesbetween the ROIs
        coherence_csv: (a file name)
                A csv file containing the pairwise coherence values
        coherence_fig: (a file name)
                Figure representing coherence values
        timedelay_array: (an array)
                The pairwise time delays between theROIs (in seconds)
        timedelay_csv: (a file name)
                A csv file containing the pairwise time delay values
        timedelay_fig: (a file name)
                Figure representing coherence values
