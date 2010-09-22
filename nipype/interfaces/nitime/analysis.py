# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""

Interfaces to functionality from nitime for time-series analysis of fmri data 

- nitime.analysis.CoherenceAnalyzer: Coherence/y 
- nitime.fmri.io:  
- nitime.viz.drawmatrix_channels

"""

from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath,
                                    OutputMultiPath, Undefined, traits,
                                    BaseInterface)

from nitime.analysis import CoherenceAnalyzer
from nitime import TimeSeries

class CoherenceAnalyzerInputSpec(TraitedSpec):

    #Input either csv file, or time-series object and use _xor_inputs to
    #discriminate

    
class CoherenceAnalyzerOutputSpec(TraitedSpec):
class CoherenceAnalyzer(BaseInterface):

    # Use the get_attr to pull out the input values from the InputSpec


    #Rewrite _run_interface, but not run
    #Rewrite _list_outputs (look at BET)
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        return outputs
    
class GetTimeSeriesInputSpec():
class GetTimeSeriesOutputSpec():
class GetTimeSeries():

class CoherenceVizInputSpec():
class CoherenceVizOutputSpec():
class CoherenceViz():

