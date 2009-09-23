''' Header reading / writing functions for nifti1 image format

Author: Matthew Brett
'''

import numpy as np
import numpy.linalg as npl

from nipype.externals.pynifti.volumeutils import Recoder, make_dt_codes, \
     HeaderDataError, HeaderTypeError, allopen
from nipype.externals.pynifti.batteryrunners import Report
from nipype.externals.pynifti.quaternions import fillpositive, quat2mat, mat2quat
from nipype.externals.pynifti import analyze # module import
from nipype.externals.pynifti.spm99analyze import SpmAnalyzeHeader
from nipype.externals.pynifti import filetuples # module import
from nipype.externals.pynifti.spatialimages import SpatialImage

from nipype.externals.pynifti.header_ufuncs import write_data, adapt_header

# nifti1 flat header definition for Analyze-like first 348 bytes
# first number in comments indicates offset in file header in bytes
header_dtd = [
    ('sizeof_hdr', 'i4'), # 0; must be 348
    ('data_type', 'S10'), # 4; unused
    ('db_name', 'S18'),   # 14; unused
    ('extents', 'i4'),    # 32; unused
    ('session_error', 'i2'), # 36; unused
    ('regular', 'S1'),    # 38; unused
    ('dim_info', 'u1'),   # 39; MRI slice ordering code
    ('dim', 'i2', 8),     # 40; data array dimensions
    ('intent_p1', 'f4'),  # 56; first intent parameter
    ('intent_p2', 'f4'),  # 60; second intent parameter
    ('intent_p3', 'f4'),  # 64; third intent parameter
    ('intent_code', 'i2'),# 68; NIFTI intent code
    ('datatype', 'i2'),   # 70; it's the datatype
    ('bitpix', 'i2'),     # 72; number of bits per voxel
    ('slice_start', 'i2'),# 74; first slice index  
    ('pixdim', 'f4', 8),  # 76; grid spacings (units below)
    ('vox_offset', 'f4'), # 108; offset to data in image file
    ('scl_slope', 'f4'),  # 112; data scaling slope
    ('scl_inter', 'f4'),  # 116; data scaling intercept
    ('slice_end', 'i2'),  # 120; last slice index
    ('slice_code', 'u1'), # 122; slice timing order
    ('xyzt_units', 'u1'), # 123; inits of pixdim[1..4]
    ('cal_max', 'f4'),    # 124; max display intensity
    ('cal_min', 'f4'),    # 128; min display intensity
    ('slice_duration', 'f4'), # 132; time for 1 slice
    ('toffset', 'f4'),   # 136; time axis shift
    ('glmax', 'i4'),     # 140; unused
    ('glmin', 'i4'),     # 144; unused
    ('descrip', 'S80'),  # 148; any text
    ('aux_file', 'S24'), # 228; auxiliary filename
    ('qform_code', 'i2'), # 252; xform code
    ('sform_code', 'i2'), # 254; xform code
    ('quatern_b', 'f4'), # 256; quaternion b param
    ('quatern_c', 'f4'), # 260; quaternion c param
    ('quatern_d', 'f4'), # 264; quaternion d param
    ('qoffset_x', 'f4'), # 268; quaternion x shift
    ('qoffset_y', 'f4'), # 272; quaternion y shift
    ('qoffset_z', 'f4'), # 276; quaternion z shift
    ('srow_x', 'f4', 4), # 280; 1st row affine transform
    ('srow_y', 'f4', 4), # 296; 2nd row affine transform
    ('srow_z', 'f4', 4), # 312; 3rd row affine transform
    ('intent_name', 'S16'), # 328; name or meaning of data
    ('magic', 'S4')      # 344; must be 'ni1\0' or 'n+1\0'
    ]

# Full header numpy dtype
header_dtype = np.dtype(header_dtd)

# datatypes not in analyze format, with codes
try:
    _float128t = np.float128
except AttributeError:
    _float128t = np.void
try:
    _complex256t = np.complex256
except AttributeError:
    _complex256t = np.void
_added_dtdefs = ( # code, label, dtype definition
    (256, 'int8', np.int8),
    (512, 'uint16', np.uint16),
    (768, 'uint32', np.uint32),
    (1024,'int64', np.int64),
    (1280, 'int64', np.uint64),
    (1536, 'float128', _float128t), # Only numpy defined on 64 bit
    (1792, 'complex128', np.complex128),
    (2048, 'complex256', _complex256t), # 64 bit again
    (2304, 'RGBA', np.dtype([('R','u1'),
                    ('G', 'u1'),
                    ('B', 'u1'),
                    ('A', 'u1')]))
    )

# Make full code alias bank, including dtype column
data_type_codes = make_dt_codes(analyze._dtdefs + _added_dtdefs)

# Transform (qform, sform) codes
xform_codes = Recoder(( # code, label
    (0, 'unknown'), # Code for transform unknown or absent
    (1, 'scanner'),
    (2, 'aligned'),
    (3, 'talairach'),
    (4, 'mni')), fields=('code', 'label'))

# unit codes
unit_codes = Recoder(( # code, label
    (0, 'unknown'), 
    (1, 'meter'),
    (2, 'mm'),
    (3, 'micron'),
    (8, 'sec'),
    (16, 'msec'),
    (24, 'usec'),
    (32, 'hz'),
    (40, 'ppm'),
    (48, 'rads')), fields=('code', 'label'))

slice_order_codes = Recoder(( # code, label
    (0, 'unknown'),
    (1, 'sequential increasing', 'seq inc'),
    (2, 'sequential decreasing', 'seq dec'),
    (3, 'alternating increasing', 'alt inc'),
    (4, 'alternating decreasing', 'alt dec'),
    (5, 'alternating increasing 2', 'alt inc 2'),
    (6, 'alternating decreasing 2', 'alt dec 2')),
                            fields=('code', 'label'))

intent_codes = Recoder((
    # code, label, parameters description tuple
    (0, 'none', ()),
    (2, 'correlation',('p1 = DOF',)),
    (3, 't test', ('p1 = DOF',)),
    (4, 'f test', ('p1 = numerator DOF', 'p2 = denominator DOF')),
    (5, 'z score', ()),
    (6, 'chi2', ('p1 = DOF',)),
    (7, 'beta', ('p1=a', 'p2=b')), # two parameter beta distribution
    (8, 'binomial', ('p1 = number of trials', 'p2 = probability per trial')),
    # Prob(x) = (p1 choose x) * p2^x * (1-p2)^(p1-x), for x=0,1,...,p1
    (9, 'gamma', ('p1 = shape, p2 = scale', 2)), # 2 parameter gamma
    (10, 'poisson', ('p1 = mean',)), # Density(x) proportional to x^(p1-1) * exp(-p2*x)
    (11, 'normal', ('p1 = mean', 'p2 = standard deviation',)),
    (12, 'non central f test', ('p1 = numerator DOF',
                                'p2 = denominator DOF',
                                'p3 = numerator noncentrality parameter',)),
    (13, 'non central chi2', ('p1 = DOF', 'p2 = noncentrality parameter',)),
    (14, 'logistic', ('p1 = location', 'p2 = scale',)),
    (15, 'laplace', ('p1 = location', 'p2 = scale')),
    (16, 'uniform', ('p1 = lower end', 'p2 = upper end')),
    (17, 'non central t test', ('p1 = DOF', 'p2 = noncentrality parameter')),
    (18, 'weibull', ('p1 = location', 'p2 = scale, p3 = power')),
    (19, 'chi', ('p1 = DOF',)),
    # p1 = 1 = 'half normal' distribution
    # p1 = 2 = Rayleigh distribution
    # p1 = 3 = Maxwell-Boltzmann distribution.                  */
    (20, 'inverse gaussian', ('pi = mu', 'p2 = lambda')),
    (21, 'extreme value 1', ('p1 = location', 'p2 = scale')),
    (22, 'p value', ()),
    (23, 'log p value', ()),
    (24, 'log10 p value', ()),
    (1001, 'estimate', ()),
    (1002, 'label', ()),
    (1003, 'neuroname', ()),
    (1004, 'general matrix', ('p1 = M', 'p2 = N')),
    (1005, 'symmetric matrix', ('p1 = M',)),
    (1006, 'displacement vector', ()),
    (1007, 'vector', ()),
    (1008, 'poinset', ()),
    (1009, 'triangle', ()),
    (1010, 'quaternion', ()),
    (1011, 'dimensionless', ()),
    (2001, 'time series', ()),
    (2002, 'node index', ()),
    (2003, 'rgb vector', ()),
    (2004, 'rgba vector', ()),
    (2005, 'shape', ())),
                       fields=('code', 'label', 'parameters'))


class Nifti1Extension(object):
    """Baseclass for NIfTI1 header extensions.

    This class is sufficient to handle very simple text-based extensions, such
    as `comment`. More sophisticated extensions should/will be supported by
    dedicated subclasses.
    """
    def __init__(self, code, content):
        """
        Parameters
        ----------
        code : int|str
          Canonical extension code as defined in the NIfTI standard, given
          either as integer or corresponding label
          (see :data:`~nifti.nifti1.extension_codes`)
        content : str
          Extension content as read from the NIfTI file header. This content is
          converted into a runtime representation.
        """
        try:
            self._code = extension_codes.code[code]
        except KeyError:
            # XXX or fail or at least complain?
            self._code = code
        self._content = self._unmangle(content)

    def _unmangle(self, value):
        """Convert the extension content into its runtime representation.

        The default implementation does nothing at all.

        Parameters
        ----------
        value : str
          Extension content as read from file.

        Returns
        -------
        The same object that was passed as `value`.

        Notes
        -----
        Subclasses should reimplement this method to provide the desired
        unmangling procedure and may return any type of object.
        """
        return value

    def _mangle(self, value):
        """Convert the extension content into NIfTI file header representation.

        The default implementation does nothing at all.

        Parameters
        ----------
        value : str
          Extension content in runtime form.

        Returns
        -------
        str

        Notes
        -----
        Subclasses should reimplement this method to provide the desired
        mangling procedure.
        """
        return value

    def get_code(self):
        """Return the canonical extension type code."""
        return self._code

    def get_content(self):
        """Return the extension content in its runtime representation."""
        return self._content

    def get_sizeondisk(self):
        """Return the size of the extension in the NIfTI file.
        """
        # need raw value size plus 8 bytes for esize and ecode
        size = len(self._mangle(self._content))
        size += 8
        # extensions size has to be a multiple of 16 bytes
        size += 16 - (size % 16)
        return size

    def __repr__(self):
        try:
            code = extension_codes.label[self._code]
        except KeyError:
            # deal with unknown codes
            code = self._code

        s = "Nifti1Extension('%s', '%s')" % (code, self._content)
        return s

    def __eq__(self, other):
        if self._code != other._code \
           or self._content != other._content:
            return False
        else:
            return True

    def write_to(self, fileobj):
        ''' Write header extensions to fileobj

        Write starts at fileobj current file position.

        Parameters
        ----------
        fileobj : file-like object
           Should implement ``write`` method

        Returns
        -------
        None
        '''
        extstart = fileobj.tell()
        rawsize = self.get_sizeondisk()
        # write esize and ecode first
        fileobj.write(np.array((rawsize, self._code),
                               dtype=np.int32).tostring())
        # followed by the actual extension content
        # XXX if mangling upon load is implemented, it should be reverted here
        fileobj.write(self._mangle(self._content))
        # be nice and zero out remaining part of the extension till the
        # next 16 byte border
        fileobj.write('\x00' * (extstart + rawsize - fileobj.tell()))


# NIfTI header extension type codes (ECODE)
# see nifti1_io.h for a complete list of all known extensions and
# references to their description or contacts of the respective
# initiators
extension_codes = Recoder((
    (0, "ignore", Nifti1Extension),
    (2, "dicom", Nifti1Extension),
    (4, "afni", Nifti1Extension),
    (6, "comment", Nifti1Extension),
    (8, "xcede", Nifti1Extension),
    (10, "jimdiminfo", Nifti1Extension),
    (12, "workflow_fwds", Nifti1Extension),
    (14, "freesurfer", Nifti1Extension),
    (16, "pypickle", Nifti1Extension)
    ),
    fields=('code', 'label', 'handler'))


class Nifti1Extensions(list):
    """Simple extension collection, implemented as a list-subclass.
    """
    def count(self, ecode):
        """Returns the number of extensions matching a given *ecode*.

        Parameter
        ---------
          code : int | str
            The ecode can be specified either literal or as numerical value.
        """
        count = 0
        code = extension_codes.code[ecode]
        for e in self:
            if e.get_code() == code:
                count += 1
        return count

    def get_codes(self):
        """Return a list of the extension code of all available extensions"""
        return [e.get_code() for e in self]

    def get_sizeondisk(self):
        """Return the size of the complete header extensions in the NIfTI file.
        """
        # add four bytes for the NIfTI extension flag!
        return np.sum([e.get_sizeondisk() for e in self]) + 4

    def __repr__(self):
        s = "Nifti1Extensions(%s)" \
                % ', '.join([str(e) for e in self])
        return s

    def __eq__(self, other):
        for i, e in enumerate(self):
            if not e == other[i]:
                return False
        return True

    def write_to(self, fileobj):
        ''' Write header extensions to fileobj

        Write starts at fileobj current file position.

        Parameters
        ----------
        fileobj : file-like object
           Should implement ``write`` method

        Returns
        -------
        None
        '''
        # not extensions -> nothing to do
        if not len(self):
            return

        # since we have extensions write the appropriate flag
        fileobj.write(np.array((1,0,0,0), dtype=np.int8).tostring())
        # and now each extension
        for e in self:
            e.write_to(fileobj)

    @classmethod
    def from_fileobj(klass, fileobj, size):
        '''Read header extensions from a fileobj

        Parameters
        ----------
        fileobj : file-like object
          It is assumed to be positions right after the NIfTI magic field.
        size : int
          Number of bytes to read. If negative, fileobj will be read till its
          end.

        Returns
        -------
          An extension list. This list might be empty in case not extensions
          were present in fileobj.
        '''
        # make empty extension list
        extensions = klass()
        # assume the fileptr is just after header (magic field)
        # try reading the next 4 bytes after the initial header
        extension_status = fileobj.read(4)
        if not len(extension_status):
            # if there is nothing the NIfTI standard requires to assume zeros
            extension_status = np.zeros((4,), dtype=np.int8)
        else:
            extension_status = np.fromstring(extension_status, dtype=np.int8)

        # NIfTI1 says: if first element is non-zero there are extensions present
        # if not there is nothing left to do
        if not extension_status[0]:
            return extensions

        # note that we read the extension flag
        if not size < 0:
            size = size - 4
        # read until the whole header is parsed (each extension is a multiple
        # of 16 bytes) or in case of a separate header file till the end
        # (break inside the body)
        # XXX not sure if the separate header behavior is sane
        while size >= 16 or size < 0:
            # the next 8 bytes should have esize and ecode
            ext_def = fileobj.read(8)
            # nothing was read and instructed to read till the end
            # -> assume all extensions where parsed and break
            if not len(ext_def) and size < 0:
                break
            # otherwise there should be a full extension header
            if not len(ext_def) == 8:
                raise HeaderDataError('failed to read extension header')
            ext_def = np.fromstring(ext_def, dtype=np.int32)
            # be extra verbose
            ecode = ext_def[1]
            esize = ext_def[0]
            if esize % 16:
                raise HeaderDataError(
                        'extension size is not a multiple of 16 bytes')
            # read extension itself; esize includes the 8 bytes already read
            evalue = fileobj.read(esize - 8)
            if not len(evalue) == esize - 8:
                raise HeaderDataError('failed to read extension content')
            # note that we read a full extension
            size -= esize
            # store raw extension content, but strip trailing NULL chars
            evalue = evalue.rstrip('\x00')
            # 'extension_codes' also knows the best implementation to handle
            # a particular extension type
            try:
                ext = extension_codes.handler[ecode](ecode, evalue)
            except KeyError:
                # unknown extension type
                # XXX complain or fail or go with a generic extension
                ext = Nifti1Extension(ecode, evalue)
            extensions.append(ext)
        return extensions


class Nifti1Header(SpmAnalyzeHeader):
    ''' Class for NIFTI1 header '''
    # Copies of module level definitions
    _dtype = header_dtype
    _data_type_codes = data_type_codes
    _xform_codes = xform_codes
    _unit_codes = unit_codes
    _intent_codes = intent_codes
    _slice_order_codes = slice_order_codes

    # data scaling capabilities
    has_data_slope = True
    has_data_intercept = True

    def get_best_affine(self):
        ''' Select best of available transforms '''
        hdr = self._header_data
        if hdr['sform_code']:
            return self.get_sform()
        if hdr['qform_code']:
            return self.get_qform()
        return self.get_base_affine()

    def _empty_headerdata(self, endianness=None):
        ''' Create empty header binary block with given endianness '''
        hdr_data = analyze.AnalyzeHeader._empty_headerdata(self, endianness)
        hdr_data['scl_slope'] = 1
        hdr_data['magic'] = 'n+1'
        hdr_data['vox_offset'] = 352
        return hdr_data

    def get_qform_quaternion(self):
        ''' Compute quaternion from b, c, d of quaternion

        Fills a value by assuming this is a unit quaternion
        '''
        hdr = self._header_data
        bcd = [hdr['quatern_b'], hdr['quatern_c'], hdr['quatern_d']]
        return fillpositive(bcd)

    def get_qform(self):
        ''' Return 4x4 affine matrix from qform parameters in header '''
        hdr = self._header_data
        quat = self.get_qform_quaternion()
        R = quat2mat(quat)
        vox = hdr['pixdim'][1:4].copy()
        if np.any(vox) < 0:
            raise HeaderDataError('pixdims[1,2,3] should be positive')
        qfac = hdr['pixdim'][0]
        if qfac not in (-1,1):
            raise HeaderDataError('qfac (pixdim[0]) should be 1 or -1')
        vox[-1] *= qfac
        S = np.diag(vox)
        M = np.dot(R, S)
        out = np.eye(4)
        out[0:3,0:3] = M
        out[0:3,3] = [hdr['qoffset_x'], hdr['qoffset_y'], hdr['qoffset_z']]
        return out

    def set_qform(self, affine, code=None):
        ''' Set qform header values from 4x4 affine

        Parameters
        ----------
        hdr : nifti1 header
        affine : 4x4 array
            affine transform to write into qform
        code : None, string or integer
            String or integer giving meaning of transform in *affine*.
            The default is None.  If code is None, then {if current
            qform code is not 0, leave code as it is in the header; else
            set to 1 ('scanner')}.

        Notes
        -----
        The qform transform only encodes translations, rotations and
        zooms. If there are shear components to the *affine* transform,
        the written qform gives the closest approximation where the
        rotation matrix is orthogonal. This is to allow quaternion
        representation. The orthogonal representation enforces orthogonal
        axes.

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> int(hdr['qform_code']) # gives 0 - unknown
        0
        >>> affine = np.diag([1,2,3,1])
        >>> np.all(hdr.get_qform() == affine)
        False
        >>> hdr.set_qform(affine)
        >>> np.all(hdr.get_qform() == affine)
        True
        >>> int(hdr['qform_code']) # gives 1 - scanner
        1
        >>> hdr.set_qform(affine, code='talairach')
        >>> int(hdr['qform_code'])
        3
        >>> hdr.set_qform(affine, code=None)
        >>> int(hdr['qform_code'])
        3
        >>> hdr.set_qform(affine, code='scanner')
        >>> int(hdr['qform_code'])
        1
        '''
        hdr = self._header_data
        if code is None:
            code = hdr['qform_code']
            if code == 0:
                hdr['qform_code'] = 1
        else:
            code = self._xform_codes[code]
            hdr['qform_code'] = code
        if not affine.shape == (4,4):
            raise TypeError('Need 4x4 affine as input')
        trans = affine[:3,3]
        RZS = affine[:3,:3]
        zooms = np.sqrt(np.sum(RZS * RZS, axis=0))
        R = RZS / zooms
        # Set qfac to make R determinant positive
        if npl.det(R) > 0:
            qfac = 1
        else:
            qfac = -1
            R[:,-1] *= -1
        # Make R orthogonal (to allow quaternion representation)
        # The orthogonal representation enforces orthogonal axes
        # (a subtle requirement of the NIFTI format qform transform)
        # Transform below is polar decomposition, returning the closest
        # orthogonal matrix PR, to input R
        P, S, Qs = npl.svd(R)
        PR = np.dot(P, Qs)
        # Convert to quaternion
        quat = mat2quat(PR)
        # Set into header
        hdr['qoffset_x'], hdr['qoffset_y'], hdr['qoffset_z'] = trans
        hdr['pixdim'][0] = qfac
        hdr['pixdim'][1:4] = zooms 
        hdr['quatern_b'], hdr['quatern_c'], hdr['quatern_d'] = quat[1:]

    def get_sform(self):
        ''' Return sform 4x4 affine matrix from header '''
        hdr = self._header_data
        out = np.eye(4)
        out[0,:] = hdr['srow_x'][:]
        out[1,:] = hdr['srow_y'][:]
        out[2,:] = hdr['srow_z'][:]
        return out

    def set_sform(self, affine, code=None):
        ''' Set sform transform from 4x4 affine

        Parameters
        ----------
        hdr : nifti1 header
        affine : 4x4 array
            affine transform to write into sform
        code : None, string or integer
            String or integer giving meaning of transform in *affine*.
            The default is None.  If code is None, then {if current
            sform code is not 0, leave code as it is in the header; else
            set to 1 ('scanner')}.

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> int(hdr['sform_code']) # gives 0 - unknown
        0
        >>> affine = np.diag([1,2,3,1])
        >>> np.all(hdr.get_sform() == affine)
        False
        >>> hdr.set_sform(affine)
        >>> np.all(hdr.get_sform() == affine)
        True
        >>> int(hdr['sform_code']) # gives 1 - scanner
        1
        >>> hdr.set_sform(affine, code='talairach')
        >>> int(hdr['sform_code'])
        3
        >>> hdr.set_sform(affine, code=None)
        >>> int(hdr['sform_code'])
        3
        >>> hdr.set_sform(affine, code='scanner')
        >>> int(hdr['sform_code'])
        1
        '''
        hdr = self._header_data
        if code is None:
            code = hdr['sform_code']
            if code == 0:
                hdr['sform_code'] = 1
        else:
            code = self._xform_codes[code]
            hdr['sform_code'] = code
        hdr['srow_x'][:] = affine[0,:]
        hdr['srow_y'][:] = affine[1,:]
        hdr['srow_z'][:] = affine[2,:]

    def get_qform_code(self, code_repr='label'):
        ''' Return representation of qform code

        Parameters
        ----------
        code_repr : string
           string giving output form of intent code representation.
           Default is 'label'; use 'code' for integer representation.

        Returns
        -------
        qform_code : string or integer
            string label for qform code or code

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr['qform_code'] = 3
        >>> hdr.get_qform_code()
        'talairach'
        '''
        return self._get_code_field(
            code_repr,
            'qform_code',
            self._xform_codes)

    def get_sform_code(self, code_repr='label'):
        ''' Return representation of sform code

        Parameters
        ----------
        code_repr : string
           string giving output form of intent code representation.
           Default is 'label'; use 'code' for integer representation.

        Returns
        -------
        sform_code : string or integer
            string label for sform code or code

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr['sform_code'] = 3
        >>> hdr.get_sform_code()
        'talairach'
        '''
        return self._get_code_field(
            code_repr,
            'sform_code',
            self._xform_codes)

    def get_slope_inter(self):
        ''' Get data scaling (slope) and DC offset (intercept) from header data

        Parameters
        ----------
        self : header object
           Should have fields (keys)
           * scl_slope - slope
           * scl_inter - intercept

        Returns
        -------
        slope : None or float
           scaling (slope).  None if there is no valid scaling from
           these fields
        inter : None or float
           offset (intercept).  Also None if there is no valid scaling, offset

        Examples
        --------
        >>> fields = {'scl_slope':1,'scl_inter':0}
        >>> hdr = Nifti1Header()
        >>> hdr.get_slope_inter()
        (1.0, 0.0)
        >>> hdr['scl_slope'] = 0
        >>> hdr.get_slope_inter()
        (None, None)
        >>> hdr['scl_slope'] = np.nan
        >>> hdr.get_slope_inter()
        (None, None)
        >>> hdr['scl_slope'] = 1
        >>> hdr['scl_inter'] = 1
        >>> hdr.get_slope_inter()
        (1.0, 1.0)
        >>> hdr['scl_inter'] = np.inf
        >>> hdr.get_slope_inter()
        (1.0, 0.0)
        '''
        scale = float(self['scl_slope'])
        dc_offset = float(self['scl_inter'])
        if not scale or not np.isfinite(scale):
            return None, None
        if not np.isfinite(dc_offset):
            dc_offset = 0.0
        return scale, dc_offset

    def set_slope_inter(self, slope, inter):
        self._header_data['scl_slope'] = slope
        self._header_data['scl_inter'] = inter

    def get_dim_info(self):
        ''' Gets nifti MRI slice etc dimension information

        Returns
        -------
        freq : {None,0,1,2}
           Which data array axis is freqency encode direction
        phase : {None,0,1,2}
           Which data array axis is phase encode direction
        slice : {None,0,1,2}
           Which data array axis is slice encode direction

        where ``data array`` is the array returned by ``get_data``

        Because nifti1 files are natively Fortran indexed:
          0 is fastest changing in file
          1 is medium changing in file
          2 is slowest changing in file

        ``None`` means the axis appears not to be specified.

        Examples
        --------
        See set_dim_info function

        '''
        hdr = self._header_data
        info = int(hdr['dim_info'])
        freq = info & 3
        phase = (info >> 2) & 3
        slice = (info >> 4) & 3
        return (freq-1 if freq else None,
                phase-1 if phase else None,
                slice-1 if slice else None)

    def set_dim_info(self, freq=None, phase=None, slice=None):
        ''' Sets nifti MRI slice etc dimension information

        Parameters
        ----------
        hdr : nifti1 header
        freq : {None, 0, 1, 2}
            axis of data array refering to freqency encoding
        phase : {None, 0, 1, 2}
            axis of data array refering to phase encoding
        slice : {None, 0, 1, 2}
            axis of data array refering to slice encoding

        ``None`` means the axis is not specified.

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_dim_info(1, 2, 0)
        >>> hdr.get_dim_info()
        (1, 2, 0)
        >>> hdr.set_dim_info(freq=1, phase=2, slice=0)
        >>> hdr.get_dim_info()
        (1, 2, 0)
        >>> hdr.set_dim_info()
        >>> hdr.get_dim_info()
        (None, None, None)
        >>> hdr.set_dim_info(freq=1, phase=None, slice=0)
        >>> hdr.get_dim_info()
        (1, None, 0)

        Notes
        -----
        This is stored in one byte in the header
        '''
        for inp in (freq, phase, slice):
            if inp not in (None, 0, 1, 2):
                raise HeaderDataError('Inputs must be in [None, 0, 1, 2]')
        info = 0
        if not freq is None:
            info = info | ((freq+1) & 3)
        if not phase is None:
            info = info | (((phase+1) & 3) << 2)
        if not slice is None:
            info = info | (((slice+1) & 3) << 4)
        self._header_data['dim_info'] = info

    def get_intent_code(self, code_repr='label'):
        ''' Return representation of intent code

        Parameters
        ----------
        code_repr : string
           string giving output form of intent code representation.
           Default is 'label'; use 'code' for integer representation.

        Returns
        -------
        intent_code : string or integer
            string label for intent code or code

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_intent('t test', (10,), name='some score')
        >>> hdr.get_intent_code()
        't test'
        '''
        return self._get_code_field(
            code_repr,
            'intent_code',
            self._intent_codes)

    def get_intent(self, code_repr='label'):
        ''' Get intent code, parameters and name

        Parameters
        ----------
        code_repr : string
           string giving output form of intent code representation.
           Default is 'label'; use 'code' for integer representation.

        Returns
        -------
        code : string or integer
            intent code, or string describing code
        parameters : tuple
            parameters for the intent
        name : string
            intent name

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_intent('t test', (10,), name='some score')
        >>> hdr.get_intent()
        ('t test', (10.0,), 'some score')
        >>> hdr.get_intent('code')
        (3, (10.0,), 'some score')
        '''
        hdr = self._header_data
        code = int(hdr['intent_code'])
        recode = self.get_intent_code(code_repr)
        n_params = len(self._intent_codes.parameters[code])
        params = (float(hdr['intent_p%d' % (i+1)]) for i in range(n_params))
        return recode, tuple(params), str(hdr['intent_name'])

    def set_intent(self, code, params=(), name=''):
        ''' Set the intent code, parameters and name

        If parameters are not specified, assumed to be all zero. Each
        intent code has a set number of parameters associated. If you
        specify any parameters, then it will need to be the correct number
        (e.g the "f test" intent requires 2).  However, parameters can
        also be set in the file data, so we also allow not setting any
        parameters (empty parameter tuple).

        Parameters
        ----------
        code : integer or string
            code specifying nifti intent
        params : list, tuple of scalars
            parameters relating to intent (see intent_codes)
            defaults to ().  Unspecified parameters are set to 0.0
        name : string
            intent name (description). Defaults to ''

        Returns
        -------
        None

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_intent(0) # unknown code
        >>> hdr.set_intent('z score')
        >>> hdr.get_intent()
        ('z score', (), '')
        >>> hdr.get_intent('code')
        (5, (), '')
        >>> hdr.set_intent('t test', (10,), name='some score')
        >>> hdr.get_intent()
        ('t test', (10.0,), 'some score')
        >>> hdr.set_intent('f test', (2, 10), name='another score')
        >>> hdr.get_intent()
        ('f test', (2.0, 10.0), 'another score')
        >>> hdr.set_intent('f test')
        >>> hdr.get_intent()
        ('f test', (0.0, 0.0), '')
        '''
        hdr = self._header_data
        icode = intent_codes.code[code]
        p_descr = intent_codes.parameters[code]
        if len(params) and len(params) != len(p_descr):
            raise HeaderDataError('Need params of form %s, or empty' % (p_descr,))
        all_params = [0] * 3
        all_params[:len(params)] = params[:]
        for i, param in enumerate(all_params):
            hdr['intent_p%d' % (i+1)] = param
        hdr['intent_code'] = icode
        hdr['intent_name'] = name

    def get_slice_duration(self):
        ''' Get slice duration

        Returns
        -------
        slice_duration : float
            time to acquire one slice

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_dim_info(slice=2)
        >>> hdr.set_slice_duration(0.3)
        >>> print "%0.1f" % hdr.get_slice_duration()
        0.3

        Notes
        -----
        The Nifti1 spec appears to require the slice dimension to be
        defined for slice_duration to have meaning.
        '''
        _, _, slice_dim = self.get_dim_info()
        if slice_dim is None:
            raise HeaderDataError('Slice dimension must be set '
                                  'for duration to be valid')
        return float(self._header_data['slice_duration'])

    def set_slice_duration(self, duration):
        ''' Set slice duration

        Parameters
        ----------
        duration : scalar
            time to acquire one slice

        Examples
        --------
        See ``get_slice_duration``
        '''
        _, _, slice_dim = self.get_dim_info()
        if slice_dim is None:
            raise HeaderDataError('Slice dimension must be set '
                                  'for duration to be valid')
        self._header_data['slice_duration'] = duration

    def get_slice_code(self, code_repr='label'):
        ''' Return representation of slice order code

        Parameters
        ----------
        code_repr : string
           string giving output form of slice order code representation.
           Default is 'label'; use 'code' for integer representation.

        Returns
        -------
        slice_code : string or integer
            string label for slice ordering code or code

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr['slice_code'] = 4 # alternating decreasing
        >>> hdr.get_slice_code()
        'alternating decreasing'
        '''
        return self._get_code_field(
            code_repr,
            'slice_code',
            self._slice_order_codes)

    def get_slice_times(self):
        ''' Get slice times from slice timing information

        Returns
        -------
        slice_times : tuple
            Times of acquisition of slices, where 0 is the beginning of
            the acquisition, ordered by position in file.  nifti allows
            slices at the top and bottom of the volume to be excluded from
            the standard slice timing specification, and calls these
            "padding slices".  We give padding slices ``None`` as a time
            of acquisition

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_dim_info(slice=2)
        >>> hdr.set_data_shape((1, 1, 7))
        >>> hdr.set_slice_duration(0.1)

        We need a function to print out the Nones and floating point
        values in a predictable way, for the tests below.

        >>> _stringer = lambda val: val is not None and '%2.1f' % val or None
        >>> _print_me = lambda s: map(_stringer, s)

        The following examples are from the nifti1.h documentation.

        >>> hdr['slice_code'] = slice_order_codes['sequential increasing']
        >>> _print_me(hdr.get_slice_times())
        ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6']
        >>> hdr['slice_start'] = 1
        >>> hdr['slice_end'] = 5
        >>> _print_me(hdr.get_slice_times())
        [None, '0.0', '0.1', '0.2', '0.3', '0.4', None]
        >>> hdr['slice_code'] = slice_order_codes['sequential decreasing']
        >>> _print_me(hdr.get_slice_times())
        [None, '0.4', '0.3', '0.2', '0.1', '0.0', None]
        >>> hdr['slice_code'] = slice_order_codes['alternating increasing']
        >>> _print_me(hdr.get_slice_times())
        [None, '0.0', '0.3', '0.1', '0.4', '0.2', None]
        >>> hdr['slice_code'] = slice_order_codes['alternating decreasing']
        >>> _print_me(hdr.get_slice_times())
        [None, '0.2', '0.4', '0.1', '0.3', '0.0', None]
        >>> hdr['slice_code'] = slice_order_codes['alternating increasing 2']
        >>> _print_me(hdr.get_slice_times())
        [None, '0.2', '0.0', '0.3', '0.1', '0.4', None]
        >>> hdr['slice_code'] = slice_order_codes['alternating decreasing 2']
        >>> _print_me(hdr.get_slice_times())
        [None, '0.4', '0.1', '0.3', '0.0', '0.2', None]
        '''
        hdr = self._header_data
        _, _, slice_dim = self.get_dim_info()
        shape = self.get_data_shape()
        slice_len = shape[slice_dim]
        duration = self.get_slice_duration()
        slabel = self.get_slice_code()
        if slabel == 'unknown':
            raise HeaderDataError('Cannot get slice times when '
                                  'Slice code is "unknown"')
        slice_start, slice_end = (int(hdr['slice_start']),
                                  int(hdr['slice_end']))
        if slice_start < 0:
            raise HeaderDataError('slice_start should be >= 0')
        if slice_end == 0:
            slice_end = slice_len-1
        n_timed = slice_end - slice_start + 1
        if n_timed < 1:
            raise HeaderDataError('slice_end should be > slice_start')
        st_order = self._slice_time_order(slabel, n_timed)
        times = st_order * duration
        return ((None,)*slice_start +
                tuple(times) +
                (None,)*(slice_len-slice_end-1))

    def set_slice_times(self, slice_times):
        ''' Set slice times into *hdr*

        Parameters
        ----------
        slice_times : tuple
            tuple of slice times, one value per slice
            tuple can include None to indicate no slice time for that slice

        Examples
        --------
        >>> hdr = Nifti1Header()
        >>> hdr.set_dim_info(slice=2)
        >>> hdr.set_data_shape([1, 1, 7])
        >>> hdr.set_slice_duration(0.1)
        >>> times = [None, 0.2, 0.4, 0.1, 0.3, 0.0, None]
        >>> hdr.set_slice_times(times)
        >>> hdr.get_slice_code()
        'alternating decreasing'
        >>> int(hdr['slice_start'])
        1
        >>> int(hdr['slice_end'])
        5
        '''
        # Check if number of slices matches header
        hdr = self._header_data
        _, _, slice_dim = self.get_dim_info()
        shape = self.get_data_shape()
        slice_len = shape[slice_dim]
        if slice_len != len(slice_times):
            raise HeaderDataError('Number of slice times does not '
                                  'match number of slices')
        # Extract Nones at beginning and end.  Check for others
        for ind, time in enumerate(slice_times):
            if time is not None:
                slice_start = ind
                break
        else:
            raise HeaderDataError('Not all slice times can be None')
        for ind, time in enumerate(slice_times[::-1]):
            if time is not None:
                slice_end = slice_len-ind-1
                break
        timed = slice_times[slice_start:slice_end+1]
        for time in timed:
            if time is None:
                raise HeaderDataError('Cannot have None in middle '
                                      'of slice time vector')
        # Find slice duration, check times are compatible with single
        # duration
        tdiffs = np.diff(np.sort(timed))
        if not np.allclose(np.diff(tdiffs), 0):
            raise HeaderDataError('Slice times not compatible with '
                                  'single slice duration')
        duration = np.mean(tdiffs)
        # To slice time order
        st_order = np.round(np.array(timed) / duration)
        # Check if slice times fit known schemes
        n_timed = len(timed)
        labels = self._slice_order_codes.value_set('label')
        labels.remove('unknown')
        for label in labels:
            if np.all(st_order == self._slice_time_order(
                    label,
                    n_timed)):
                break
        else:
            raise HeaderDataError('slice ordering of %s fits '
                                  'with no known scheme' % st_order)
        # Set values into header
        hdr['slice_start'] = slice_start
        hdr['slice_end'] = slice_end
        hdr['slice_duration'] = duration
        hdr['slice_code'] = slice_order_codes.code[label]

    def for_file_pair(self, is_pair=True):
        ''' Adapt header to separate or same image and header file

        Parameters
        ----------
        is_pair : bool, optional
           True if adapting header to file pair state, False for single

        Returns
        -------
        hdr : Nifti1Header
           copied and possibly modified header

        Examples
        --------
        The header starts off as being for a single file

        >>> hdr = Nifti1Header()
        >>> str(hdr['magic'])
        'n+1'
        >>> hdr.get_data_offset()
        352

        But we can switch it to be for two files (a pair)

        >>> pair_hdr = hdr.for_file_pair()
        >>> str(pair_hdr['magic'])
        'ni1'
        >>> pair_hdr.get_data_offset()
        0

        The original header is not affected (a copy is returned)

        >>> hdr.get_data_offset()
        352

        Back to single again

        >>> unpair_hdr = pair_hdr.for_file_pair(False)
        >>> str(unpair_hdr['magic'])
        'n+1'
        >>> unpair_hdr.get_data_offset()
        352
        '''
        hdr = self.copy()
        if not is_pair:
            # one file version
            if hdr['magic'] == 'n+1':
                if hdr['vox_offset'] < 352:
                    hdr['vox_offset'] = 352
                return hdr
            hdr['magic'] = 'n+1'
            hdr['vox_offset'] = 352
            return hdr
        # two file version
        if hdr['magic'] == 'ni1':
            return hdr
        hdr['magic'] = 'ni1'
        hdr['vox_offset'] = 0
        return hdr

    def _slice_time_order(self, slabel, n_slices):
        ''' Supporting function to give time order of slices from label '''
        if slabel == 'sequential increasing':
            sp_ind_time_order = range(n_slices)
        elif slabel == 'sequential decreasing':
            sp_ind_time_order = range(n_slices)[::-1]
        elif slabel == 'alternating increasing':
            sp_ind_time_order = range(0,n_slices,2) + range(1, n_slices, 2)
        elif slabel == 'alternating decreasing':
            sp_ind_time_order = range(n_slices-1,-1,-2) + range(n_slices-2,-1,-2)
        elif slabel == 'alternating increasing 2':
            sp_ind_time_order = range(1,n_slices,2) + range(0, n_slices, 2)
        elif slabel == 'alternating decreasing 2':
            sp_ind_time_order = range(n_slices-2,-1,-2) + range(n_slices-1,-1,-2)
        else:
            raise HeaderDataError('We do not handle slice ordering "%s"'
                                  % slabel)
        return np.argsort(sp_ind_time_order)

    ''' Checks only below here '''

    @classmethod
    def _get_checks(klass):
        # We need to return our own versions of - e.g. chk_datatype, to
        # pick up the Nifti datatypes from our class
        return (klass._chk_sizeof_hdr,
                klass._chk_datatype,
                klass._chk_bitpix,
                klass._chk_pixdims,
                klass._chk_scale_slope,
                klass._chk_scale_inter,
                klass._chk_qfac,
                klass._chk_magic_offset,
                klass._chk_qform_code,
                klass._chk_sform_code)

    @staticmethod
    def _chk_scale_slope(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        scale = hdr['scl_slope']
        if scale and np.isfinite(scale):
            return ret
        ret.problem_msg = '"scl_slope" is %s; should !=0 and be finite' % scale
        if fix:
            hdr['scl_slope'] = 1
            ret.fix_msg = 'setting "scl_slope" to 1'
        else:
            ret.level = 30
        return ret

    @staticmethod
    def _chk_scale_inter(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        scale = hdr['scl_inter']
        if np.isfinite(scale):
            return ret
        ret.problem_msg = '"scl_inter" is %s; should be finite' % scale
        if fix:
            hdr['scl_inter'] = 0
            ret.fix_msg = 'setting "scl_inter" to 0'
        else:
            ret.level = 30
        return ret

    @staticmethod
    def _chk_qfac(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        if hdr['pixdim'][0] in (-1, 1):
            return ret
        ret.problem_msg = 'pixdim[0] (qfac) should be 1 (default) or -1'
        if fix:
            hdr['pixdim'][0] = 1
            ret.fix_msg = 'setting qfac to 1'
        else:
            ret.level = 20
        return ret

    @staticmethod
    def _chk_magic_offset(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        magic = hdr['magic']
        offset = hdr['vox_offset']
        if magic == 'ni1': # two files
            if offset == 0:
                return ret
            ret.problem_msg = ('vox offset should be 0 (is %s)'
                               'with two-file nifti images' % offset)
            ret.level = 40
            if fix: 
                ret.fix_msg = 'leaving at current value'
        elif magic == 'n+1': # one file
            if offset >= 352:
                if not offset % 16:
                    return ret
                else:
                    # XXX Michael wonders, if this warning really valid? NIfTI
                    # says that each extension's length has to be a multiple of
                    # 16, therefore the test should be (offset-352) % 16 and
                    # not offset % 16, or does SPM have additional artifical
                    # limitations?
                    ret.problem_msg = ('vox offset (=%s) not divisible '
                                       'by 16, not SPM compatible' % offset)
                    ret.level = 30
                    if fix:
                        ret.fix_msg = 'leaving at current value'
                    return ret
            ret.problem_msg = ('vox offset %d too low for '
                               'single file nifti1' % offset)
            if fix:
                hdr['vox_offset'] = 352                
                ret.fix_msg = 'setting to minimum value of 352'
            else:
                ret.level = 50
        else: # unrecognized nii magic string, oh dear
            ret.problem_msg = 'magic string %s is not valid' % magic
            ret.level = 50
            if fix:
                ret.fix_msg = 'leaving as is, but future errors are likely'
        return ret

    @classmethod
    def _chk_qform_code(klass, hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        code = int(hdr['qform_code'])
        if int(hdr['qform_code']) in klass._xform_codes.value_set():
            return ret
        ret.problem_msg = 'qform code %d not valid' % code
        if fix:
            hdr['qform_code'] = 0
            ret.fix_msg = 'setting to 0'
        else:
            ret.level = 30
        return ret

    @classmethod
    def _chk_sform_code(klass, hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        code = int(hdr['sform_code'])
        if int(hdr['sform_code']) in klass._xform_codes.value_set():
            return ret
        ret.problem_msg = 'sform code %d not valid' % code
        if fix:
            hdr['sform_code'] = 0
            ret.fix_msg = 'setting to 0'
        else:
            ret.level = 30
        return ret


class Nifti1Image(analyze.AnalyzeImage):
    _header_maker = Nifti1Header

    def _set_header(self, header=None):
        SpatialImage._set_header(self, header)

    @staticmethod
    def filespec_to_files(filespec):
        ft1 = filetuples.FileTuples(
            (('header', '.nii'), ('image', '.nii')),
            ignored_suffixes=('.gz', '.bz2')
            )
        ft2 = filetuples.FileTuples(
            (('header', '.hdr'), ('image', '.img')),
            ignored_suffixes=('.gz', '.bz2')
            )
        for ftups in (ft1, ft2):
            try:
                ftups.set_filenames(filespec)
            except filetuples.FileTuplesError:
                continue
            break
        else:
            raise ValueError('Filespec "%s" does not '
                             'look like Nifti1' % filespec)
        files = dict(zip(('header', 'image'), ftups.get_filenames()))
        return files

    @classmethod
    def from_files(klass, files):
        fname = files['header']
        fileobj = allopen(fname)
        header = klass._header_maker.from_fileobj(fileobj)
        extra = None

        # handle extensions
        # assume the fileptr is just after header (magic field)
        # determine how much to read when parsing the extensions
        if header['vox_offset'] == 0:
            # read till the end of the header
            extsize = -1
        else:
            extsize = header['vox_offset'] - fileobj.tell()
        extensions = Nifti1Extensions.from_fileobj(fileobj, extsize)
        # XXX maybe always do that?
        if len(extensions):
            extra = {'extensions': extensions}

        affine = header.get_best_affine()
        ret =  klass(None, affine, header=header, extra=extra)
        ret._files = files
        return ret

    def to_files(self, files=None):
        ''' Write image to files passed, or self._files
        '''
        # XXX the whole method is candidate for refactoring, since it started as
        # verbatim copy of AnalyzeImage.to_files()
        if files is None:
            files = self._files
            if files is None:
                raise ValueError('Need files to write data')
        data = self.get_data()
        # Adapt header to possible two<->one file difference
        is_pair = files['header'] != files['image']

        hdr = self.get_header().for_file_pair(is_pair)

        # if any extensions, figure out necessary vox_offset for extensions to
        # fit
        if self.extra.has_key('extensions') and len(self.extra['extensions']):
            hdr['vox_offset'] = len(hdr.binaryblock) \
                                + self.extra['extensions'].get_sizeondisk()

        slope, inter, mn, mx = adapt_header(hdr, data)
        hdrf = allopen(files['header'], 'wb')
        hdr.write_to(hdrf)

        # write all extensions to file
        # assumes that the file ptr is right after the magic string
        if not self.extra.has_key('extensions'):
            # no extensions: be nice and write appropriate flag
            hdrf.write(np.array((0,0,0,0), dtype=np.int8).tostring())
        else:
            self.extra['extensions'].write_to(hdrf)


        if is_pair:
            imgf = allopen(files['image'], 'wb')
        else: # single file for header and image
            imgf = hdrf
        # streams like bz2 do not allow seeks, even forward.  We
            # check where to go, and write zeros up until the data part
            # of the file
            offset = hdr.get_data_offset()
            diff = offset-hdrf.tell()
            if diff > 0:
                hdrf.write('\x00' * diff)
        write_data(hdr, data, imgf, inter, slope, mn, mx)
        self._header = hdr
        self._files = files


    def _update_header(self):
        ''' Harmonize header with image data and affine

        See AnalyzeImage._update_header for more examples

        Examples
        --------
        >>> data = np.zeros((2,3,4))
        >>> affine = np.diag([1.0,2.0,3.0,1.0])
        >>> img = Nifti1Image(data, affine)
        >>> hdr = img.get_header()
        >>> np.all(hdr.get_qform() == affine)
        True
        >>> np.all(hdr.get_sform() == affine)
        True
        '''
        super(Nifti1Image, self)._update_header()
        hdr = self._header
        if not self._affine is None:
            hdr.set_sform(self._affine)
            hdr.set_qform(self._affine)


load = Nifti1Image.load
save = Nifti1Image.save
