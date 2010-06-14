# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
''' Header reading functions for SPM version of analyze format '''
import warnings
import numpy as np

from nipype.externals.pynifti.volumeutils import HeaderDataError, HeaderTypeError, \
    allopen

from nipype.externals.pynifti import filetuples # module import
from nipype.externals.pynifti.batteryrunners import Report
from nipype.externals.pynifti import analyze # module import

''' Support subtle variations of SPM version of Analyze '''
header_key_dtd = analyze.header_key_dtd
# funused1 in dime subfield is scalefactor
image_dimension_dtd = analyze.image_dimension_dtd[:]
image_dimension_dtd[
    image_dimension_dtd.index(('funused1', 'f4'))
    ] = ('scl_slope', 'f4')
# originator text field used as image origin (translations)
data_history_dtd = analyze.data_history_dtd[:]
data_history_dtd[
    data_history_dtd.index(('originator', 'S10'))
    ] = ('origin', 'i2', 5)

# Full header numpy dtype combined across sub-fields
header_dtype = np.dtype(header_key_dtd +
                        image_dimension_dtd +
                        data_history_dtd)


class SpmAnalyzeHeader(analyze.AnalyzeHeader):
    ''' Basic scaling Spm Analyze header '''
    # Copies of module level definitions
    _dtype = header_dtype
    
    # data scaling capabilities
    has_data_slope = True
    has_data_intercept = False

    def _empty_headerdata(self, endianness=None):
        ''' Create empty header binary block with given endianness '''
        hdr_data = super(SpmAnalyzeHeader, self)._empty_headerdata(endianness)
        hdr_data['scl_slope'] = 1
        return hdr_data

    def get_slope_inter(self):
        ''' Get scalefactor and intercept '''
        slope = self._header_data['scl_slope']
        inter = 0.0
        return slope, inter

    def set_slope_inter(self, slope, inter):
        self._header_data['scl_slope'] = slope
        if inter:
            raise HeaderTypeError('Cannot set non-zero intercept '
                                  'for SPM headers')
        
    @classmethod
    def _get_checks(klass):
        checks = super(SpmAnalyzeHeader, klass)._get_checks()
        return checks + (klass._chk_scale,)
        
    @staticmethod
    def _chk_scale(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        scale = hdr['scl_slope']
        if scale and np.isfinite(scale):
            return ret
        ret.problem_msg = ('scale slope is %s; should !=0 and be finite'
                           % scale)
        if fix:
            hdr['scl_slope'] = 1
            ret.fix_msg = 'setting scalefactor "scale" to 1'
        else:
            ret.level = 30
        return ret


class Spm99AnalyzeHeader(SpmAnalyzeHeader):
    ''' Adds origin functionality to base SPM header '''
    def get_origin_affine(self):
        ''' Get affine from header, using SPM origin field if sensible

        The default translations are got from the ``origin``
        field, if set, or from the center of the image otherwise.

        Examples
        --------
        >>> hdr = Spm99AnalyzeHeader()
        >>> hdr.set_data_shape((3, 5, 7))
        >>> hdr.set_zooms((3, 2, 1))
        >>> hdr.default_x_flip
        True
        >>> hdr.get_origin_affine() # from center of image
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -3.],
               [ 0.,  0.,  0.,  1.]])
        >>> hdr['origin'][:3] = [3,4,5]
        >>> hdr.get_origin_affine() # using origin
        array([[-3.,  0.,  0.,  6.],
               [ 0.,  2.,  0., -6.],
               [ 0.,  0.,  1., -4.],
               [ 0.,  0.,  0.,  1.]])
        >>> hdr['origin'] = 0 # unset origin
        >>> hdr.set_data_shape((3, 5))
        >>> hdr.get_origin_affine()
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -0.],
               [ 0.,  0.,  0.,  1.]])
        >>> hdr.set_data_shape((3, 5, 7))
        >>> hdr.get_origin_affine() # from center of image
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -3.],
               [ 0.,  0.,  0.,  1.]])
        '''
        hdr = self._header_data
        zooms = hdr['pixdim'][1:4].copy()
        if self.default_x_flip:
            zooms[0] *= -1
        # Get translations from origin, or center of image
        # Remember that the origin is for matlab (1-based indexing)
        origin = hdr['origin'][:3]
        dims = hdr['dim'][1:4]
        if (np.any(origin) and
            np.all(origin > -dims) and np.all(origin < dims*2)):
            origin = origin-1
        else:    
            origin = (dims-1) / 2.0
        aff = np.eye(4)
        aff[:3,:3] = np.diag(zooms)
        aff[:3,-1] = -origin * zooms
        return aff

    get_best_affine = get_origin_affine
    
    def set_origin_from_affine(self, affine):
        ''' Set SPM origin to header from affine matrix.

        The ``origin`` field was read but not written by SPM99 and 2.
 	It was used for storing a central voxel coordinate, that could
 	be used in aligning the image to some standard position - a
 	proxy for a full translation vector that was usually stored in
 	a separate matlab .mat file.
        
	Nifti uses the space occupied by the SPM ``origin`` field for
        important other information (the transform codes), so writing
        the origin will make the header a confusing Nifti file.  If
        you work with both Analyze and Nifti, you should probably
        avoid doing this. 

        Parameters
        ----------
        affine : array-like, shape (4,4)
           Affine matrix to set

        Returns
        -------
        None

        Examples
        --------
        >>> hdr = Spm99AnalyzeHeader()
        >>> hdr.set_data_shape((3, 5, 7))
        >>> hdr.set_zooms((3,2,1))
        >>> hdr.get_origin_affine()
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -3.],
               [ 0.,  0.,  0.,  1.]])
        >>> affine = np.diag([3,2,1,1])
        >>> affine[:3,3] = [-6, -6, -4]
        >>> hdr.set_origin_from_affine(affine)
	>>> np.all(hdr['origin'][:3] == [3,4,5])
	True
        >>> hdr.get_origin_affine()
        array([[-3.,  0.,  0.,  6.],
               [ 0.,  2.,  0., -6.],
               [ 0.,  0.,  1., -4.],
               [ 0.,  0.,  0.,  1.]])
        '''
        if affine.shape != (4,4):
            raise ValueError('Need 4x4 affine to set')
        hdr = self._header_data
        RZS = affine[:3,:3]
        Z = np.sqrt(np.sum(RZS * RZS, axis=0))
        T = affine[:3,3]
        # Remember that the origin is for matlab (1-based) indexing
        hdr['origin'][:3] = -T / Z + 1

    @classmethod
    def _get_checks(klass):
        checks = super(Spm99AnalyzeHeader, klass)._get_checks()
        return checks + (klass._chk_origin,)
        
    @staticmethod
    def _chk_origin(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        origin = hdr['origin'][0:3]
        dims = hdr['dim'][1:4]
        if (not np.any(origin) or
            (np.all(origin > -dims) and np.all(origin < dims*2))):
            return ret
        ret.problem_msg = 'very large origin values relative to dims'
        if fix:
            ret.fix_msg = 'leaving as set, ignoring for affine'
        else:
            ret.level = 20
        return ret


class Spm99AnalyzeImage(analyze.AnalyzeImage):
    _header_maker = Spm99AnalyzeHeader
    @classmethod
    def from_filespec(klass, filespec):
        ret = super(Spm99AnalyzeImage, klass).from_filespec(filespec)
        import scipy.io as sio
        matf = ret._files['mat']
        try:
            matf = allopen(matf)
        except IOError:
            return ret
        mats = sio.loadmat(matf)
        if 'mat' in mats: # this overrides a 'M', and includes any flip
            mat = mats['mat']
            if mat.ndim > 2:
                warnings.warn('More than one affine in "mat" matrix, '
                              'using first')
                mat = mat[:,:,0]
            ret._affine = mat
            return ret
        elif 'M' in mats: # the 'M' matrix does not include flips
            hdr = ret._header
            if hdr.default_x_flip:
                ret._affine = np.dot(np.diag([-1,1,1,1]), mats['M'])
            else:
                ret._affine = mats['M']
        else:
            raise ValueError('mat file found but no "mat" or "M" in it')
        return ret
    
    @staticmethod
    def filespec_to_files(filespec):
        ftups = filetuples.FileTuples(
            (('header', '.hdr'),('image', '.img'),('mat', '.mat')),
            ignored_suffixes = ('.gz', '.bz2'))
        try:
            ftups.set_filenames(filespec)
        except filetuples.FileTuplesError:
            raise ValueError('Strange filespec "%s"' % filespec)
        files = dict(zip(
                ('header', 'image', 'mat'),
                ftups.get_filenames()))
        return files

    def to_files(self, files=None):
        super(Spm99AnalyzeImage, self).to_files(files)
        if self._affine is None:
            return
        import scipy.io as sio
        matfname = self._files['mat']
        mfobj = allopen(matfname, 'wb')
        mat = self._affine
        hdr = self._header
        if hdr.default_x_flip:
            M = np.dot(np.diag([-1,1,1,1]), mat)
        else:
            M = mat
        # use matlab 4 format to allow gzipped write without error
        sio.savemat(mfobj, {'M': M, 'mat': mat}, format='4')
        mfobj.close()


load = Spm99AnalyzeImage.load
save = Spm99AnalyzeImage.save
