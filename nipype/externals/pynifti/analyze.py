''' Header and image for the basic Mayo Analyze format

The basic principle of the header object is that it manages and
contains header information.  Each header type may have different
attributes that can be set.  Some headers can contain only subsets of
possible passed values - for example the basic Analyze header can only
encode the zooms in an affine transform - not shears, rotations,
translations.

The attributes and methods of the object guarantee that the set values
will be consistent and valid with the header standard, in some sense.
The object API therefore gives "safe" access to the header.  You can
reach all the named fields in the header directly with the
``header_data`` attribute.  If you futz with these, the object
makes no guarantee that the data in the header are consistent.

Headers do not have filenames, they refer only the block of data in
the header.  The containing object manages the filenames, and
therefore must know how to predict image filenames from header
filenames, whether these are different, and so on.

You can access and set fields of a particular header type using standard __getitem__ / __setitem__ syntax:

    hdr['field'] = 10

Headers also implement general mappingness:

    hdr.keys()
    hdr.items()
    hdr.values()
    
Basic attributes of the header object are::

    .endianness (read only)
    .binaryblock (read only)
    .structarr (read only)

Class attributes are::

    .default_x_flip
    
with methods::
    
    .get/set_data_shape
    .get/set_data_dtype
    .get/set_zooms
    .get_base_affine()
    .get_best_affine()
    .check_fix()
    .as_byteswapped(endianness)
    .write_to(fileobj)
    .__str__
    .__eq__
    .__ne__

and class methods::

    .diagnose_binaryblock(string)
    .from_fileobj(fileobj)
    
More sophisticated headers can add more methods and attributes.

=================
 Header checking
=================

We have a file, and we would like feedback as to whether there are any
problems with this header, and whether they are fixable::

   hdr = AnalyzeHeader.from_fileobj(fileobj, check=False)
   AnalyzeHeader.diagnose_binaryblock(hdr.binaryblock)

This will run all known checks, with no fixes, outputing to stdout

In creating a header object, we might want to check the header data.  If it
passes the error threshold, it goes through::

   hdr = AnalyzeHeader.from_fileobj(good_fileobj)

whereas::

   hdr = AnalyzeHeader.from_fileobj(bad_fileobj)

would raise some error, with output to logging (see below).

We set the error level (the level of problem that the ``check=True``
versions will accept as OK) from global defaults::

   nifti.imageglobals.error_level = 30

The same for logging::

   nifti.logger = logger

'''

import numpy as np

from nipype.externals.pynifti.volumeutils import pretty_mapping, endian_codes, \
     native_code, swapped_code, hdr_getterfunc, \
     make_dt_codes, HeaderDataError, HeaderTypeError, allopen

from nipype.externals.pynifti.header_ufuncs import read_data, write_data, adapt_header

from nipype.externals.pynifti import imageglobals as imageglobals
from nipype.externals.pynifti.spatialimages import SpatialImage
from nipype.externals.pynifti import filetuples # module import

from nipype.externals.pynifti.batteryrunners import BatteryRunner, Report

# Sub-parts of standard analyze header from 
# Mayo dbh.h file
header_key_dtd = [
    ('sizeof_hdr', 'i4'),
    ('data_type', 'S10'),
    ('db_name', 'S18'),
    ('extents', 'i4'),
    ('session_error', 'i2'),
    ('regular', 'S1'),
    ('hkey_un0', 'S1')
    ]
image_dimension_dtd = [
    ('dim', 'i2', 8),
    ('vox_units', 'S4'),
    ('cal_units', 'S8'),
    ('unused1', 'i2'),
    ('datatype', 'i2'),
    ('bitpix', 'i2'),
    ('dim_un0', 'i2'),
    ('pixdim', 'f4', 8),
    ('vox_offset', 'f4'),
    ('funused1', 'f4'),
    ('funused2', 'f4'),
    ('funused3', 'f4'),
    ('cal_max', 'f4'),
    ('cal_min', 'f4'),
    ('compressed', 'i4'),
    ('verified', 'i4'),
    ('glmax', 'i4'),
    ('glmin', 'i4')
    ]
data_history_dtd = [
    ('descrip', 'S80'),
    ('aux_file', 'S24'),
    ('orient', 'S1'),
    ('originator', 'S10'),
    ('generated', 'S10'),
    ('scannum', 'S10'),
    ('patient_id', 'S10'),
    ('exp_date', 'S10'),
    ('exp_time', 'S10'),
    ('hist_un0', 'S3'),
    ('views', 'i4'),
    ('vols_added', 'i4'),
    ('start_field', 'i4'),
    ('field_skip', 'i4'),
    ('omax', 'i4'),
    ('omin', 'i4'),
    ('smax', 'i4'),
    ('smin', 'i4')
    ]

# Full header numpy dtype combined across sub-fields
header_dtype = np.dtype(header_key_dtd + image_dimension_dtd + 
                        data_history_dtd)

_dtdefs = ( # code, conversion function, equivalent dtype, aliases
    (0, 'none', np.void), 
    (1, 'binary', np.void), # 1 bit per voxel, needs thought
    (2, 'uint8', np.uint8),
    (4, 'int16', np.int16),
    (8, 'int32', np.int32),
    (16, 'float32', np.float32),
    (32, 'complex64', np.complex64), # numpy complex format?
    (64, 'float64', np.float64),
    (128, 'RGB', np.dtype([('R','u1'),
                  ('G', 'u1'),
                  ('B', 'u1')])),
    (255, 'all', np.void))

# Make full code alias bank, including dtype column
data_type_codes = make_dt_codes(_dtdefs)


class AnalyzeHeader(object):
    ''' Class for basic analyze header

    Implements zoom-only setting of affine transform, and no image
    scaling
    
    '''
    # Copies of module-level definitions
    _dtype = header_dtype
    _data_type_codes = data_type_codes
    
    # default x flip
    default_x_flip = True

    # data scaling capabilities
    has_data_slope = False
    has_data_intercept = False

    @classmethod
    def from_mapping(klass,
                 field_mapping=None,
                 endianness=None,
                 check=True):
        '''  Initialize header from mapping '''
        obj = klass(obj, endianness=endianness, check=check)
        #self._header_data = self._empty_headerdata(endianness)
        if not field_mapping is None:
            for key, value in field_mapping:
                obj._header_data[key] = value
        #obj.check = check
        if check:
            self.check_fix()
    
    def __init__(self,
                 binaryblock=None,
                 endianness=None,
                 check=True):
        ''' Initialize header from binary data block

        Parameters
        ----------
        binaryblock : {None, string} optional
            binary block to set into header.  By default, None, in
            which case we insert the default empty header block
        endianness : {None, '<','>', other endian code} string, optional
            endianness of the binaryblock.  If None, guess endianness
            from the data.
        check : bool, optional
            Whether to check content of header in initialization.
            Default is True.
            
        Examples
	--------
        >>> hdr1 = AnalyzeHeader() # an empty header
        >>> hdr1.endianness == native_code
        True
        >>> hdr1.get_data_shape()
        (0,)
        >>> hdr1.set_data_shape((1,2,3)) # now with some content
        >>> hdr1.get_data_shape()
        (1, 2, 3)

        We can set the binary block directly via this initialization.
        Here we get it from the header we have just made
        
        >>> binblock2 = hdr1.binaryblock
        >>> hdr2 = AnalyzeHeader(binblock2)
        >>> hdr2.get_data_shape()
        (1, 2, 3)

        Empty headers are native endian by default

        >>> hdr2.endianness == native_code
        True

        You can pass valid opposite endian headers with the
        ``endianness`` parameter. Even empty headers can have
        endianness
        
        >>> hdr3 = AnalyzeHeader(endianness=swapped_code)
        >>> hdr3.endianness == swapped_code
        True

        If you do not pass an endianness, and you pass some data, we
        will try to guess from the passed data.

        >>> binblock3 = hdr3.binaryblock
        >>> hdr4 = AnalyzeHeader(binblock3)
        >>> hdr4.endianness == swapped_code
        True
        '''
        if binaryblock is None:
            self._header_data = self._empty_headerdata(endianness)
            return
        # check size
        if len(binaryblock) != self._dtype.itemsize:
            raise HeaderDataError('Binary block is wrong size')
        hdr = np.ndarray(shape=(),
                         dtype=self._dtype,
                         buffer=binaryblock)
        if endianness is None:
            endianness = self._guessed_endian(hdr)
        else:
            endianness = endian_codes[endianness]
        if endianness != native_code:
            dt = self._dtype.newbyteorder(endianness)
            hdr = np.ndarray(shape=(),
                             dtype=dt,
                             buffer=binaryblock)
        self._header_data = hdr.copy()
        self.check = check
        if check:
            self.check_fix()
        return

    @property
    def binaryblock(self):
        ''' binary block of data as string

        Returns
        -------
        binaryblock : string
            string giving binary data block

        Examples
        --------
        >>> # Make default empty header
        >>> hdr = AnalyzeHeader()
        >>> len(hdr.binaryblock)
        348
        '''
        return self._header_data.tostring()

    @property
    def endianness(self):
        ''' endian code of binary data

        The endianness code gives the current byte order
        interpretation of the binary data.

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> code = hdr.endianness
        >>> code == native_code
        True

        Notes
        -----
        Endianness gives endian interpretation of binary data. It is
        read only because the only common use case is to set the
        endianness on initialization, or occasionally byteswapping the
        data - but this is done via the as_byteswapped method
        '''
        if self._header_data.dtype.isnative:
            return native_code
        return swapped_code

    def copy(self):
        ''' Return copy of header

        >>> hdr = AnalyzeHeader()
        >>> hdr['dim'][0]
        0
        >>> hdr['dim'][0] = 2
        >>> hdr2 = hdr.copy()
        >>> hdr2 is hdr
        False
        >>> hdr['dim'][0] = 3
        >>> hdr2['dim'][0]
        2
        '''
        return self.__class__(
                self.binaryblock,
                self.endianness, check=False)
    
    def __eq__(self, other):
        ''' equality between two headers defined by mapping
        
        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr2 = AnalyzeHeader()
        >>> hdr == hdr2
        True
        >>> hdr3 = AnalyzeHeader(endianness=swapped_code)
        >>> hdr == hdr3
        True
        >>> hdr3.set_data_shape((1,2,3))
        >>> hdr == hdr3
        False
        >>> hdr4 = AnalyzeHeader()
        >>> hdr == hdr4
        True
        '''
        this_end = self.endianness
        this_bb = self.binaryblock
        if this_end == other.endianness:
            return this_bb == other.binaryblock
        other_bb = other._header_data.byteswap().tostring()
        return this_bb == other_bb
        
    def __ne__(self, other):
        ''' equality between two headers defined by ``header_data``

        For examples, see ``__eq__`` method docstring
        '''
        return not self == other

    def __getitem__(self, item):
        ''' Return values from header data

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr['sizeof_hdr'] == 348
        True
        '''
        return self._header_data[item]
    
    def __setitem__(self, item, value):
        ''' Set values in header data

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr['descrip'] = 'description'
        >>> str(hdr['descrip'])
        'description'
        '''
        self._header_data[item] = value

    def __iter__(self):
        return iter(self.keys())
            
    def keys(self):
        ''' Return keys from header data'''
        return list(self._dtype.names)
    
    def values(self):
        ''' Return values from header data'''
        data = self._header_data
        return [data[key] for key in self._dtype.names]

    def items(self):
        ''' Return items from header data'''
        return zip(self.keys(), self.values())

    def check_fix(self,
              logger=imageglobals.logger,
              error_level=imageglobals.error_level):
        ''' Check header data with checks '''
        battrun = BatteryRunner(self.__class__._get_checks())
        self, reports = battrun.check_fix(self)
        for report in reports:
            report.log_raise(logger, error_level)

    @classmethod
    def diagnose_binaryblock(klass, binaryblock, endianness=None):
        ''' Run checks over header binary data, return string '''
        hdr = klass(binaryblock, endianness=endianness, check=False)
        battrun = BatteryRunner(klass._get_checks())
        reports = battrun.check_only(hdr)
        return '\n'.join([report.message
                          for report in reports if report.message])
                                         
    def _guessed_endian(self, hdr):
        ''' Guess intended endianness from mapping-like ``hdr``

        Parameters
        ----------
        hdr : mapping-like
           hdr for which to guess endianness

        Returns
        -------
        endianness : {'<', '>'}
           Guessed endianness of header

        Examples
        --------
        Zeros header, no information, guess native

        >>> hdr = AnalyzeHeader()
        >>> hdr_data = np.zeros((), dtype=header_dtype)
        >>> hdr._guessed_endian(hdr_data) == native_code
        True

        A valid native header is guessed native

        >>> hdr_data = hdr.structarr.copy()
        >>> hdr._guessed_endian(hdr_data) == native_code
        True

        And, when swapped, is guessed as swapped

        >>> sw_hdr_data = hdr_data.byteswap(swapped_code)
        >>> hdr._guessed_endian(sw_hdr_data) == swapped_code
        True

        The algorithm is as follows:

        First, look at the first value in the ``dim`` field; this
        should be between 0 and 7.  If it is between 1 and 7, then
        this must be a native endian header.

        >>> hdr_data = np.zeros((), dtype=header_dtype) # blank binary data
        >>> hdr_data['dim'][0] = 1
        >>> hdr._guessed_endian(hdr_data) == native_code
        True
        >>> hdr_data['dim'][0] = 6
        >>> hdr._guessed_endian(hdr_data) == native_code
        True
        >>> hdr_data['dim'][0] = -1
        >>> hdr._guessed_endian(hdr_data) == swapped_code
        True

        If the first ``dim`` value is zeros, we need a tie breaker.
        In that case we check the ``sizeof_hdr`` field.  This should
        be 348.  If it looks like the byteswapped value of 348,
        assumed swapped.  Otherwise assume native.

        >>> hdr_data = np.zeros((), dtype=header_dtype) # blank binary data
        >>> hdr._guessed_endian(hdr_data) == native_code
        True
        >>> hdr_data['sizeof_hdr'] = 1543569408
        >>> hdr._guessed_endian(hdr_data) == swapped_code
        True
        >>> hdr_data['sizeof_hdr'] = -1
        >>> hdr._guessed_endian(hdr_data) == native_code
        True

        This is overridden by the ``dim``[0] value though:
        
        >>> hdr_data['sizeof_hdr'] = 1543569408
        >>> hdr_data['dim'][0] = 1
        >>> hdr._guessed_endian(hdr_data) == native_code
        True
        '''
        dim0 = int(hdr['dim'][0])
        if dim0 == 0:
            if hdr['sizeof_hdr'] == 1543569408:
                return swapped_code
            return native_code
        elif 1<=dim0<=7:
            return native_code
        return swapped_code

    def _empty_headerdata(self, endianness=None):
        ''' Return header data for empty header with given endianness
        '''
        dt = self._dtype
        if endianness is not None:
            endianness = endian_codes[endianness]
            dt = dt.newbyteorder(endianness)
        hdr_data = np.zeros((), dtype=dt)
        hdr_data['sizeof_hdr'] = 348
        hdr_data['dim'] = 1
        hdr_data['dim'][0] = 0        
        hdr_data['pixdim'] = 1
        hdr_data['datatype'] = 16 # float32
        hdr_data['bitpix'] = 32
        return hdr_data

    @property
    def structarr(self):
        ''' header data, with data fields

        Examples
        --------
        >>> hdr1 = AnalyzeHeader() # an empty header
        >>> sz = hdr1.structarr['sizeof_hdr']
        >>> hdr1.structarr = None
        Traceback (most recent call last):
           ...
        AttributeError: can't set attribute
        '''
        return self._header_data

    @classmethod
    def from_fileobj(klass, fileobj, endianness=None, check=True):
        ''' Return read header with given or guessed endiancode

        Parameters
        ----------
        fileobj : file-like object
           Needs to implement ``read`` method
        endianness : None or endian code, optional
           Code specifying endianness of read data

        Returns
        -------
        hdr : AnalyzeHeader object
           AnalyzeHeader object initialized from data in fileobj
           
        Examples
        --------
        >>> import StringIO
        >>> hdr = AnalyzeHeader()
        >>> fileobj = StringIO.StringIO(hdr.binaryblock)
        >>> fileobj.seek(0)
        >>> hdr2 = AnalyzeHeader.from_fileobj(fileobj)
        >>> hdr2.binaryblock == hdr.binaryblock
        True

        You can write to the resulting object data

        >>> hdr2['dim'][1] = 1
        '''
        raw_str = fileobj.read(klass._dtype.itemsize)
        return klass(raw_str, endianness, check)

    def write_to(self, fileobj):
        ''' Write header to fileobj

        Write starts at fileobj current file position.
        
        Parameters
        ----------
        fileobj : file-like object
           Should implement ``write`` method

        Returns
        -------
        None

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> import StringIO
        >>> str_io = StringIO.StringIO()
        >>> hdr.write_to(str_io)
        >>> hdr.binaryblock == str_io.getvalue()
        True
        '''
        fileobj.write(self.binaryblock)

    def get_data_dtype(self):
        ''' Get numpy dtype for data

        For examples see ``set_data_dtype``
        '''
        code = int(self._header_data['datatype'])
        dtype = self._data_type_codes.dtype[code]
        return dtype.newbyteorder(self.endianness)
    
    def set_data_dtype(self, datatype):
        ''' Set numpy dtype for data from code or dtype or type
        
        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr.set_data_dtype(np.uint8)
        >>> hdr.get_data_dtype()
        dtype('uint8')
        >>> hdr.set_data_dtype(np.dtype(np.uint8))
        >>> hdr.get_data_dtype()
        dtype('uint8')
        >>> hdr.set_data_dtype('implausible')
        Traceback (most recent call last):
           ...
        HeaderDataError: data dtype "implausible" not recognized
        >>> hdr.set_data_dtype('none')
        Traceback (most recent call last):
           ...
        HeaderDataError: data dtype "none" known but not supported
        >>> hdr.set_data_dtype(np.void)
        Traceback (most recent call last):
           ...
        HeaderDataError: data dtype "<type 'numpy.void'>" known but not supported
        '''
        try:
            code = self._data_type_codes[datatype]
        except KeyError:
            raise HeaderDataError(
                'data dtype "%s" not recognized' % datatype)
        dtype = self._data_type_codes.dtype[code]
        # test for void, being careful of user-defined types
        if dtype.type is np.void and not dtype.fields:
            raise HeaderDataError(
                'data dtype "%s" known but not supported' % datatype)
        self._header_data['datatype'] = code
        self._header_data['bitpix'] = dtype.itemsize * 8

    def get_data_shape(self):
        ''' Get shape of data

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr.get_data_shape()
        (0,)
        >>> hdr.set_data_shape((1,2,3))
        >>> hdr.get_data_shape()
        (1, 2, 3)

        Expanding number of dimensions gets default zooms

        >>> hdr.get_zooms()
        (1.0, 1.0, 1.0)
        '''
        dims = self._header_data['dim']
        ndims = dims[0]
        if ndims == 0:
            return 0,
        return tuple(int(d) for d in dims[1:ndims+1])

    def set_data_shape(self, shape):
        ''' Set shape of data '''
        dims = self._header_data['dim']
        prev_ndims = dims[0]
        ndims = len(shape)
        dims[:] = 1
        dims[0] = ndims        
        dims[1:ndims+1] = shape
        
    def as_byteswapped(self, endianness=None):
        ''' return new byteswapped header object with given ``endianness``

        Guaranteed to make a copy even if endianness is the same as
        the current endianness.

        Parameters
        ----------
        endianness : None or string, optional
           endian code to which to swap.  None means swap from current
           endianness, and is the default

        Returns
        -------
        hdr : header object
           hdr object with given endianness

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr.endianness == native_code
        True
        >>> bs_hdr = hdr.as_byteswapped()
        >>> bs_hdr.endianness == swapped_code
        True
        >>> bs_hdr = hdr.as_byteswapped(swapped_code)
        >>> bs_hdr.endianness == swapped_code
        True
        >>> bs_hdr is hdr
        False
        >>> bs_hdr == hdr
        True
        
        If you write to the resulting byteswapped data, it does not
        change the original.

        >>> bs_hdr['dim'][1] = 2
        >>> bs_hdr == hdr
        False

        If you swap to the same endianness, it returns a copy

        >>> nbs_hdr = hdr.as_byteswapped(native_code)
        >>> nbs_hdr.endianness == native_code
        True
        >>> nbs_hdr is hdr
        False
        '''
        current = self.endianness
        if endianness is None:
            if current == native_code:
                endianness = swapped_code
            else:
                endianness = native_code
        else:
            endianness = endian_codes[endianness]
        if endianness == current:
            return self.copy()
        hdr_data = self._header_data.byteswap()
        return self.__class__(hdr_data.tostring(),
                              endianness,
                              check=False)

    def __str__(self):
        ''' Return string representation for printing '''
        summary = "%s object, endian='%s'" % (self.__class__,
                                              self.endianness)
        return '\n'.join(
            [summary,
             pretty_mapping(self, hdr_getterfunc)])

    def get_base_affine(self):
        ''' Get affine from basic (shared) header fields

        Note that we get the translations from the center of the
        image.

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr.set_data_shape((3, 5, 7))
        >>> hdr.set_zooms((3, 2, 1))
        >>> hdr.default_x_flip
        True
        >>> hdr.get_base_affine() # from center of image
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -3.],
               [ 0.,  0.,  0.,  1.]])
        >>> hdr.set_data_shape((3, 5))
        >>> hdr.get_base_affine()
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -0.],
               [ 0.,  0.,  0.,  1.]])
        >>> hdr.set_data_shape((3, 5, 7))
        >>> hdr.get_base_affine() # from center of image
        array([[-3.,  0.,  0.,  3.],
               [ 0.,  2.,  0., -4.],
               [ 0.,  0.,  1., -3.],
               [ 0.,  0.,  0.,  1.]])
        '''
        hdr = self._header_data
        zooms = (hdr['pixdim'][1:4].copy())
        if self.default_x_flip:
            zooms[0] *= -1
        # Get translations from center of image
        origin = (hdr['dim'][1:4]-1) / 2.0
        aff = np.eye(4)
        aff[:3,:3] = np.diag(zooms)
        aff[:3,-1] = -origin * zooms
        return aff

    get_best_affine = get_base_affine
    
    def get_zooms(self):
        ''' Get zooms from header

        Returns
        -------
        z : tuple
           tuple of header zoom values

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr.get_zooms()
        ()
        >>> hdr.set_data_shape((1,2))
        >>> hdr.get_zooms()
        (1.0, 1.0)
        >>> hdr.set_zooms((3, 4))
        >>> hdr.get_zooms()
        (3.0, 4.0)
        '''
        hdr = self._header_data
        dims = hdr['dim']
        ndim = dims[0]
        if ndim == 0:
            return ()
        pixdims = hdr['pixdim']
        return tuple(pixdims[1:ndim+1])
    
    def set_zooms(self, zooms):
        ''' Set zooms into header fields

        See docstring for ``get_zooms`` for examples
        '''
        hdr = self._header_data
        dims = hdr['dim']
        ndim = dims[0]
        zooms = np.asarray(zooms)
        if len(zooms) != ndim:
            raise HeaderDataError('Expecting %d zoom values for ndim %d'
                                  % (ndim, ndim))
        if np.any(zooms < 0):
            raise HeaderDataError('zooms must be positive')
        pixdims = hdr['pixdim']
        pixdims[1:ndim+1] = zooms[:]
        
    def get_datatype(self, code_repr='label'):
        ''' Return representation of datatype code

        This method returns the datatype code, or a string label for the
        code.  Usually you are more interested in the data dtype.  To do
        that more useful thing, use ``get_data_dtype``
        
        Parameters
        ----------
        code_repr : string
           string giving output form of datatype code representation.
           Default is 'label'; use 'code' for integer representation.

        Returns
        -------
        datatype_code : string or integer
            string label for datatype code or code

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr['datatype'] = 4 # int16
        >>> hdr.get_datatype()
        'int16'
        '''
        return self._get_code_field(
            code_repr,
            'datatype',
            self._data_type_codes)

    def get_data_offset(self):
        ''' Return offset into data file to read data

        Examples
        --------
        >>> hdr = AnalyzeHeader()
        >>> hdr.get_data_offset()
        0
        >>> hdr['vox_offset'] = 12
        >>> hdr.get_data_offset()
        12
        '''
        return int(self._header_data['vox_offset'])

    def get_slope_inter(self):
        ''' Get scalefactor and intercept

        These are not implemented for basic Analyze
        '''
        return 1.0, 0.0

    def set_slope_inter(self, slope, inter):
        ''' Set raises error for Analyze header '''
        if slope != 1.0 or inter:
            raise HeaderTypeError('Cannot set slope or intercept '
                                  'for Analyze headers')

    def for_file_pair(self, is_pair=True):
        ''' Adapt header to separate or same image and header file

        This is a rare and exotic case for Analyze files, common for
        Nifti1.  For Analyze, we only need to check that, if the file is
        single, then the data offset is large enough to leave room for
        the header.
        
        Parameters
        ----------
        is_pair : bool, optional
           True if adapting header to file pair state, False for single

        Returns
        -------
        hdr : header
           copied and possibly modified header
        
        Examples
        --------
        The header starts off as being for two files
        
        >>> hdr = AnalyzeHeader()
        >>> hdr.get_data_offset()
        0

        This is the same as the default behavior for this method
        
        >>> pair_hdr = hdr.for_file_pair()
        >>> pair_hdr.get_data_offset()
        0

        But we can switch it to be for one
        
        >>> unpair_hdr = hdr.for_file_pair(False)
        >>> unpair_hdr.get_data_offset()
        352

        The original header is not affected (a copy is returned)
        
        >>> hdr.get_data_offset()
        0
        '''
        hdr = self.__class__(self.binaryblock, self.endianness)
        if not is_pair:
            if hdr['vox_offset'] < 352:
                hdr['vox_offset'] = 352
            return hdr
        # two file version
        hdr['vox_offset'] = 0
        return hdr

    def _get_code_field(self, code_repr, fieldname, recoder):
        ''' Returns representation of field given recoder and code_repr
        '''
        code = int(self._header_data[fieldname])
        if code_repr == 'code':
            return code
        if code_repr == 'label':
            return recoder.label[code]
        raise TypeError('code_repr should be "label" or "code"')
        
    @classmethod
    def _get_checks(klass):
        ''' Return sequence of check functions for this class '''
        return (klass._chk_sizeof_hdr,
                klass._chk_datatype,
                klass._chk_bitpix,
                klass._chk_pixdims)

    ''' Check functions in format expected by BatteryRunner class '''
    
    @staticmethod
    def _chk_sizeof_hdr(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        if hdr['sizeof_hdr'] == 348:
            return ret
        ret.problem_msg = 'sizeof_hdr should be 348'
        if fix:
            hdr['sizeof_hdr'] = 348
            ret.fix_msg = 'set sizeof_hdr to 348'
        else:
            ret.level = 30
        return ret

    @classmethod
    def _chk_datatype(klass, hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        code = int(hdr['datatype'])
        try:
            dtype = klass._data_type_codes.dtype[code]
        except KeyError:
            ret.level = 40
            ret.problem_msg = 'data code %d not recognized' % code
        else:
            if dtype.type is np.void:
                ret.level = 40
                ret.problem_msg = 'data code %d not supported' % code
        if fix:
            ret.fix_problem_msg = 'not attempting fix'
        return ret

    @classmethod
    def _chk_bitpix(klass, hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        code = int(hdr['datatype'])
        try:
            dt = klass._data_type_codes.dtype[code]
        except KeyError:
            ret.level = 10
            ret.problem_msg = 'no valid datatype to fix bitpix'
            if fix:
                ret.fix_msg = 'no way to fix bitpix'
            return ret
        bitpix = dt.itemsize * 8
        ret = Report(hdr)
        if bitpix == hdr['bitpix']:
            return ret
        ret.problem_msg = 'bitpix does not match datatype'
        if fix:
            hdr['bitpix'] = bitpix # inplace modification
            ret.fix_msg = 'setting bitpix to match datatype'
        else:
            ret.level = 10
        return ret

    @staticmethod
    def _chk_pixdims(hdr, fix=True):
        ret = Report(hdr, HeaderDataError)
        if not np.any(hdr['pixdim'][1:4] < 0):
            return ret
        ret.problem_msg = 'pixdim[1,2,3] should be positive'
        if fix:
            hdr['pixdim'][1:4] = np.abs(hdr['pixdim'][1:4])
            ret.fix_msg = 'setting to abs of pixdim values'
        else:
            ret.level = 40
        return ret


class AnalyzeImage(SpatialImage):
    _header_maker = AnalyzeHeader

    def get_data(self):
        ''' Lazy load of data '''
        if not self._data is None:
            return self._data
        if not self._files:
            return None
        try:
            fname = self._files['image']
        except KeyError:
            return None
        self._data = read_data(self._header, allopen(fname))
        return self._data

    def get_header(self):
        ''' Return header

        Update header to match data, affine etc in object
        '''
        self._update_header()
        return self._header

    def _set_header(self, header=None):
        # Pick up case of nifti image -> analyze
        try:
            header = header.for_file_pair()
        except AttributeError:
            pass
        super(AnalyzeImage, self)._set_header(header)

    def get_shape(self):
        if not self._data is None:
            return self._data.shape
        return self._header.get_data_shape()
    
    def get_data_dtype(self):
        return self._header.get_data_dtype()
    
    def set_data_dtype(self, dtype):
        self._header.set_data_dtype(dtype)
    
    @classmethod
    def from_filespec(klass, filespec):
        files = klass.filespec_to_files(filespec)
        return klass.from_files(files)
    
    @classmethod
    def from_files(klass, files):
        fname = files['header']
        header = klass._header_maker.from_fileobj(allopen(fname))
        affine = header.get_best_affine()
        ret =  klass(None, affine, header)
        ret._files = files
        return ret
    
    @classmethod
    def from_image(klass, img):
        orig_hdr = img.get_header()
        return klass(img.get_data(),
                     img.get_affine(),
                     img.get_header(),
                     img.extra)
    
    @staticmethod
    def filespec_to_files(filespec):
        ftups = filetuples.FileTuples(
            (('header', '.hdr'),('image', '.img')),
            ignored_suffixes = ('.gz', '.bz2'))
        try:
            ftups.set_filenames(filespec)
        except filetuples.FileTuplesError:
            raise ValueError('Filespec "%s" does not look like '
                             'Analyze ' % filespec)
        files = dict(zip(('header', 'image'), ftups.get_filenames()))
        return files

    def to_filespec(self, filespec):
        ''' Write image to files given by filespec
        '''
        files = self.filespec_to_files(filespec)
        self.to_files(files)

    def to_files(self, files=None):
        ''' Write image to files passed, or self._files
        '''
        if files is None:
            files = self._files
            if files is None:
                raise ValueError('Need files to write data')
        data = self.get_data()
        # Adapt header to possible two<->one file difference
        is_pair = files['header'] != files['image']
        hdr = self.get_header().for_file_pair(is_pair)
        slope, inter, mn, mx = adapt_header(hdr, data)
        hdrf = allopen(files['header'], 'wb')
        hdr.write_to(hdrf)
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

        >>> data = np.zeros((2,3,4))
        >>> affine = np.diag([1.0,2.0,3.0,1.0])
        >>> img = AnalyzeImage(data, affine)
        >>> img.get_shape()
        (2, 3, 4)
        >>> hdr = img._header
        >>> hdr.get_data_shape()
        (0,)
        >>> hdr.get_zooms()
        ()
        >>> np.all(hdr.get_best_affine() == np.diag([-1,1,1,1]))
        True
        >>> img._update_header()
        >>> hdr.get_data_shape()
        (2, 3, 4)
        >>> hdr.get_zooms()
        (1.0, 2.0, 3.0)
        '''
        hdr = self._header
        if not self._data is None:
            hdr.set_data_shape(self._data.shape)
        if not self._affine is None:
            RZS = self._affine[:3,:3]
            vox = np.sqrt(np.sum(RZS * RZS, axis=0))
            hdr['pixdim'][1:4] = vox
        
    @classmethod
    def load(klass, filespec):
        return klass.from_filespec(filespec)

    @classmethod
    def save(klass, img, filespec):
        img = klass.from_image(img)
        img.to_filespec(filespec)


load = AnalyzeImage.load
save = AnalyzeImage.save
