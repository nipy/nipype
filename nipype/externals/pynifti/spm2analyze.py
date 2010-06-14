# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
''' Header reading functions for SPM2 version of analyze format '''

import numpy as np

from nipype.externals.pynifti.volumeutils import HeaderDataError, HeaderTypeError
from nipype.externals.pynifti.batteryrunners import Report
from nipype.externals.pynifti import spm99analyze as spm99 # module import

image_dimension_dtd = spm99.image_dimension_dtd[:]
image_dimension_dtd[
    image_dimension_dtd.index(('funused2', 'f4'))
    ] = ('scl_inter', 'f4')

# Full header numpy dtype combined across sub-fields
header_dtype = np.dtype(spm99.header_key_dtd +
                        image_dimension_dtd +
                        spm99.data_history_dtd)
    

class Spm2AnalyzeHeader(spm99.Spm99AnalyzeHeader):
    ''' SPM2 header; adds possibility of reading, but not writing DC
    offset for data'''
    
    # Copies of module level definitions
    _dtype = header_dtype
    
    def get_slope_inter(self):
        ''' Get data scaling (slope) and offset (intercept) from header data

        Uses the algorithm from SPM2 spm_vol_ana.m by John Ashburner

        Parameters
        ----------
        self : header
           Mapping with fields:
           * scl_slope - slope
           * scl_inter - possible intercept (SPM2 use - shared by nifti)
           * glmax - the (recorded) maximum value in the data (unscaled)
           * glmin - recorded minimum unscaled value
           * cal_max - the calibrated (scaled) maximum value in the dataset
           * cal_min - ditto minimum value

        Returns
        -------
        scl_slope : None or float
            scaling (slope).  None if there is no valid scaling from
            these fields
        scl_inter : None or float
            offset (intercept).  Also None if there is no valid scaling,
            offset

        Examples
        --------
        >>> fields = {'scl_slope':1,'scl_inter':0,'glmax':0,'glmin':0,'cal_max':0, 'cal_min':0}
        >>> hdr = Spm2AnalyzeHeader()
        >>> for key, value in fields.items():
        ...     hdr[key] = value
        >>> hdr.get_slope_inter()
        (1.0, 0.0)
        >>> hdr['scl_inter'] = 0.5
        >>> hdr.get_slope_inter()
        (1.0, 0.5)
        >>> hdr['scl_inter'] = np.nan
        >>> hdr.get_slope_inter()
        (1.0, 0.0)

        If 'scl_slope' is 0, nan or inf, cannot use 'scl_slope'.
        Without valid information in the gl / cal fields, we cannot get
        scaling, and return None

        >>> hdr['scl_slope'] = 0
        >>> hdr.get_slope_inter()
        (None, None)
        >>> hdr['scl_slope'] = np.nan
        >>> hdr.get_slope_inter()
        (None, None)

        Valid information in the gl AND cal fields are needed

        >>> hdr['cal_max'] = 0.8
        >>> hdr['cal_min'] = 0.2
        >>> hdr.get_slope_inter()
        (None, None)
        >>> hdr['glmax'] = 110
        >>> hdr['glmin'] = 10
        >>> np.allclose(hdr.get_slope_inter(), [0.6/100, 0.2-0.6/100*10])
        True
        '''
        # get scaling factor from 'scl_slope' (funused1)
        scale = float(self['scl_slope'])
        if np.isfinite(scale) and scale:
            # try to get offset from scl_inter
            dc_offset = float(self['scl_inter'])
            if not np.isfinite(dc_offset):
                dc_offset = 0.0
            return scale, dc_offset
        # no non-zero and finite scaling, try gl/cal fields
        unscaled_range = self['glmax'] - self['glmin']
        scaled_range = self['cal_max'] - self['cal_min']
        if unscaled_range and scaled_range:
            scale = float(scaled_range) / unscaled_range
            dc_offset = self['cal_min'] - scale * self['glmin']
            return scale, dc_offset
        return None, None

    @classmethod
    def _chk_scale(klass, hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        scale, offset = hdr.get_slope_inter()
        if not scale is None:
            return ret
        ret.problem_msg = ('no valid scaling in scalefactor (=%s) '
                           'or cal / gl fields; scalefactor assumed 1.0'
                           % scale)
        if fix:
            hdr['scl_slope'] = 1
            ret.fix_msg = 'setting scalefactor "scl_slope" to 1'
        else:
            ret.level = 30
        return ret


class Spm2AnalyzeImage(spm99.Spm99AnalyzeImage):
    _header_maker = Spm2AnalyzeHeader


load = Spm2AnalyzeImage.load
save = Spm2AnalyzeImage.save
