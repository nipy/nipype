''' Utility functions for analyze-like formats '''

import sys

import numpy as np

sys_is_le = sys.byteorder == 'little'
native_code = sys_is_le and '<' or '>'
swapped_code = sys_is_le and '>' or '<'

endian_codes = (# numpy code, aliases
    ('<', 'little', 'l', 'le', 'L', 'LE'),
    ('>', 'big', 'BIG', 'b', 'be', 'B', 'BE'),
    (native_code, 'native', 'n', 'N', '=', '|', 'i', 'I'),
    (swapped_code, 'swapped', 's', 'S', '!'))
# We'll put these into the Recoder class after we define it

#: default compression level when writing gz and bz2 files
default_compresslevel = 1

#: convenience variables for numpy types
floating_point_types = (np.sctypes['complex'] +
                        np.sctypes['float'])
integer_types = (np.sctypes['int'] + np.sctypes['uint'])
numeric_types = floating_point_types + integer_types


class Recoder(object):
    ''' class to return canonical code(s) from code or aliases

    The concept is a lot easier to read in the implementation and
    tests than it is to explain, so...

    >>> # If you have some codes, and several aliases, like this:
    >>> code1 = 1; aliases1=['one', 'first']
    >>> code2 = 2; aliases2=['two', 'second']
    >>> # You might want to do this:
    >>> codes = [[code1]+aliases1,[code2]+aliases2]
    >>> recodes = Recoder(codes)
    >>> recodes.code['one']
    1
    >>> recodes.code['second']
    2
    >>> recodes.code[2]
    2
    >>> # Or maybe you have a code, a label and some aliases
    >>> codes=((1,'label1','one', 'first'),(2,'label2','two'))
    >>> # you might want to get back the code or the label
    >>> recodes = Recoder(codes, fields=('code','label'))
    >>> recodes.code['first']
    1
    >>> recodes.code['label1']
    1
    >>> recodes.label[2]
    'label2'
    >>> # For convenience, you can get the first entered name by
    >>> # indexing the object directly
    >>> recodes[2]
    2
    '''
    def __init__(self, codes, fields=('code',)):
        ''' Create recoder object

	``codes`` give a sequence of code, alias sequences
	``fields`` are names by which the entries in these sequences can be
	accessed.

	By default ``fields`` gives the first column the name
	"code".  The first column is the vector of first entries
	in each of the sequences found in ``codes``.  Thence you can
	get the equivalent first column value with ob.code[value],
	where value can be a first column value, or a value in any of
	the other columns in that sequence. 

	You can give other columns names too, and access them in the
	same way - see the examples in the class docstring. 

        Parameters
        ----------
        codes : seqence of sequences
            Each sequence defines values (codes) that are equivalent
        fields : {('code',) string sequence}, optional
            names by which elements in sequences can be accesssed

        '''
        self.fields = fields
        self.field1 = {} # a placeholder for the check below
        for name in fields:
            if name in self.__dict__:
                raise KeyError('Input name %s already in object dict'
                               % name)
            self.__dict__[name] = {}
        self.field1 = self.__dict__[fields[0]]
        self.add_codes(codes)
        
    def add_codes(self, codes):
        ''' Add codes to object

	>>> codes = ((1, 'one'), (2, 'two'))
	>>> rc = Recoder(codes)
        >>> rc.value_set() == set((1,2))
        True
        >>> rc.add_codes(((3, 'three'), (1, 'first')))
        >>> rc.value_set() == set((1,2,3))
        True
        '''
        for vals in codes:
            for val in vals:
                for ind, name in enumerate(self.fields):
                    self.__dict__[name][val] = vals[ind]
        
        
    def __getitem__(self, key):
        ''' Return value from field1 dictionary (first column of values)

	Returns same value as ``obj.field1[key]`` and, with the
        default initializing ``fields`` argument of fields=('code',),
        this will return the same as ``obj.code[key]``

	>>> codes = ((1, 'one'), (2, 'two'))
	>>> Recoder(codes)['two']
	2
        '''
        return self.field1[key]

    def keys(self):
    	''' Return all available code and alias values 

	Returns same value as ``obj.field1.keys()`` and, with the
        default initializing ``fields`` argument of fields=('code',),
        this will return the same as ``obj.code.keys()``

	>>> codes = ((1, 'one'), (2, 'two'), (1, 'repeat value'))
	>>> k = Recoder(codes).keys()
	>>> k.sort() # Just to guarantee order for doctest output
	>>> k
	[1, 2, 'one', 'repeat value', 'two']
	'''
        return self.field1.keys()

    def value_set(self, name=None):
        ''' Return set of possible returned values for column

        By default, the column is the first column.

	Returns same values as ``set(obj.field1.values())`` and,
        with the default initializing``fields`` argument of
        fields=('code',), this will return the same as
        ``set(obj.code.values())``

        Parameters
        ----------
        name : {None, string}
            Where default of none gives result for first column

        >>> codes = ((1, 'one'), (2, 'two'), (1, 'repeat value'))
        >>> vs = Recoder(codes).value_set()
        >>> vs == set([1, 2]) # Sets are not ordered, hence this test
        True
        >>> rc = Recoder(codes, fields=('code', 'label'))
        >>> rc.value_set('label') == set(('one', 'two', 'repeat value'))
        True
        
        '''
        if name is None:
            d = self.field1
        else:
            d = self.__dict__[name]
        return set(d.values())

    
# Endian code aliases
endian_codes = Recoder(endian_codes)


def pretty_mapping(mapping, getterfunc=None):
    ''' Make pretty string from mapping 

    Adjusts text column to print values on basis of longest key.
    Probably only sensible if keys are mainly strings.

    You can pass in a callable that does clever things to get the values
    out of the mapping, given the names.  By default, we just use
    ``__getitem__``

    Parameters
    ----------
    mapping : mapping
       implementing iterator returning keys and .items()
    getterfunc : None or callable
       callable taking two arguments, ``obj`` and ``key`` where ``obj``
       is the passed mapping.  If None, just use ``lambda obj, key:
       obj[key]``
    
    Returns
    -------
    str : string

    Examples
    --------
    >>> d = {'a key': 'a value'}
    >>> print pretty_mapping(d)
    a key  : a value
    >>> class C(object): # to control ordering, show get_ method
    ...     def __iter__(self):
    ...         return iter(('short_field','longer_field'))
    ...     def __getitem__(self, key):
    ...         if key == 'short_field':
    ...             return 0
    ...         if key == 'longer_field':
    ...             return 'str'
    ...     def get_longer_field(self):
    ...         return 'method string'
    >>> def getter(obj, key):
    ...     # Look for any 'get_<name>' methods
    ...     try:
    ...         return obj.__getattribute__('get_' + key)()
    ...     except AttributeError:
    ...         return obj[key]
    >>> print pretty_mapping(C(), getter)
    short_field   : 0
    longer_field  : method string
    '''
    if getterfunc is None:
        getterfunc = lambda obj, key: obj[key]
    lens = [len(str(name)) for name in mapping]
    mxlen = np.max(lens)
    fmt = '%%-%ds  : %%s' % mxlen
    out = []
    for name in mapping:
        value = getterfunc(mapping, name)
        out.append(fmt % (name, value))
    return '\n'.join(out)


def hdr_getterfunc(obj, key):
    ''' Getter function for keys or methods of form 'get_<key'
    '''
    # Look for any 'get_<name>' methods
    try:
        return obj.__getattribute__('get_' + key)()
    except (AttributeError, HeaderDataError):
        return obj[key]


def make_dt_codes(codes):
    ''' Create full dt codes object from datatype codes '''
    dt_codes = [list(vals) + [np.dtype(vals[-1])] for vals in codes]
    return Recoder(dt_codes, fields=('code', 'label', 'type', 'dtype'))


def can_cast(in_type, out_type, has_intercept=False, has_slope=False):
    ''' Return True if we can safely cast ``in_type`` to ``out_type``

    Parameters
    ----------
    in_type : numpy type
       type of data we will case from
    out_dtype : numpy type
       type that we want to cast to
    has_intercept : bool, optional
       Whether we can subtract a constant from the data (before scaling)
       before casting to ``out_dtype``.  Default is False
    has_slope : bool, optional
       Whether we can use a scaling factor to adjust slope of
       relationship of data to data in cast array.  Default is False

    Returns
    -------
    tf : bool
       True if we can safely cast, False otherwise

    Examples
    --------
    >>> can_cast(np.float64, np.float32)
    True
    >>> can_cast(np.complex128, np.float32)
    False
    >>> can_cast(np.int64, np.float32)
    True
    >>> can_cast(np.float32, np.int16)
    False
    >>> can_cast(np.float32, np.int16, False, True)
    True
    >>> can_cast(np.int16, np.uint8)
    False
    >>> can_cast(np.int16, np.uint8, False, True)
    False
    >>> can_cast(np.int16, np.uint8, True, True)
    True
    '''
    if np.can_cast(in_type, out_type):
        return True
    if in_type not in numeric_types or out_type not in numeric_types:
        return False
    if out_type in np.sctypes['complex']:
        return True
    if in_type in np.sctypes['complex']:
        return False
    if out_type in np.sctypes['float']:
        return True
    # now we have larger (u)int or float to smaller (u)int
    if not has_slope:
        return False
    if out_type in np.sctypes['uint']:
        if in_type not in np.sctypes['uint']:
            return has_intercept
    return True


def array_from_file(shape, dtype, infile, offset=0, order='F'):
    ''' Get array from file with specified shape, dtype and file offset

    Parameters
    ----------
    shape : sequence
        sequence specifying output array shape
    dtype : numpy dtype
        fully specified numpy dtype, including correct endianness
    infile : file-like
        open file-like object implementing at least read() and seek()
    offset : int, optional 
        offset in bytes into infile to start reading array
	data. Default is 0
    order : {'F', 'C'} string
        order in which to write data.  Default is 'F' (fortran order).

    Returns
    -------
    arr : array-like
        array like object that can be sliced, containing data

    Examples
    --------
    >>> import StringIO
    >>> str_io = StringIO.StringIO()
    >>> arr = np.arange(6).reshape(1,2,3)
    >>> str_io.write(arr.tostring('F'))
    >>> arr2 = array_from_file((1,2,3), arr.dtype, str_io)
    >>> np.all(arr == arr2)
    True
    >>> str_io = StringIO.StringIO()
    >>> str_io.write(' ' * 10)
    >>> str_io.write(arr.tostring('F'))
    >>> arr2 = array_from_file((1,2,3), arr.dtype, str_io, 10)
    >>> np.all(arr == arr2)
    True
    '''
    try: # Try memmapping file on disk
        arr = np.memmap(infile,
                        dtype,
                        mode='r',
                        shape=shape,
                        order=order,
                        offset=offset)
        # The error raised by memmap, for different file types, has
        # changed in different incarnations of the numpy routine
    except (AttributeError, TypeError, ValueError): # then read data
        infile.seek(offset)
        if len(shape) == 0:
            return np.array([])
        datasize = int(np.prod(shape) * dtype.itemsize)
        if datasize == 0:
            return np.array([])
        data_str = infile.read(datasize)
        if len(data_str) != datasize:
            msg = 'Expected %s bytes, got %s bytes from file' \
                  % (datasize, len(data_str))
            raise ValueError(msg)
        arr = np.ndarray(shape,
                         dtype,
                         buffer=data_str,
                         order=order)
    return arr


def array_to_file(data, out_dtype, fileobj, 
                  intercept=0.0, divslope=1.0, 
                  mn=None, mx=None, order='F', nan2zero=True):
    ''' Helper function for writing possibly scaled arrays to disk

    Parameters
    ----------
    data : array
       array to write
    out_dtype : dtype
       dtype to write array as
    fileobj : file-like
       file-like object implementing ``write`` method.  The fileobj
       should be initialized to start writing at the correct location
    intercept : scalar, optional
       scalar to subtract from data, before dividing by ``divslope``.
       Default is 0.0
    divslope : scalar, optional
       scalefactor to *divide* data by before writing.  Default
       is 1.0.
    mn : scalar, optional
       minimum threshold in (unscaled) data, such that all data below
       this value are set to this value. Default is None (no threshold)
    mx : scalar, optional
       maximum threshold in (unscaled) data, such that all data above
       this value are set to this value. Default is None (no threshold)
    order : {'F', 'C'}, optional
       memory order to write array.  Default is 'F'
    nan2zero : {True, False}, optional
       Whether to set NaN values to 0 when writing integer output.
       Defaults to True.  If False, NaNs will be represented as numpy
       does when casting, and this can be odd (often the lowest
       available integer value)

    Examples
    --------
    >>> from StringIO import StringIO
    >>> sio = StringIO()
    >>> data = np.arange(10, dtype=np.float)
    >>> array_to_file(data, np.float, sio)
    >>> sio.getvalue() == data.tostring('F')
    True
    >>> sio.truncate(0)
    >>> array_to_file(data, np.int16, sio)
    >>> sio.getvalue() == data.astype(np.int16).tostring()
    True
    >>> sio.truncate(0)
    >>> array_to_file(data.byteswap(), np.float, sio)
    >>> sio.getvalue() == data.byteswap().tostring('F')
    True
    >>> sio.truncate(0)
    >>> array_to_file(data, np.float, sio, order='C')
    >>> sio.getvalue() == data.tostring('C')
    True
    '''
    out_dtype = np.dtype(out_dtype)
    nan2zero = (nan2zero and
                data.dtype in floating_point_types and
                out_dtype not in floating_point_types)
    needs_copy = nan2zero or mx or mn or intercept or divslope !=1.0
    in_dtype = data.dtype
    if data.ndim < 2: # a little hack to allow 1D arrays in loop below
        data = [data]
    elif order == 'F':
        data = data.T
    elif order != 'C':
        raise ValueError('Order should be one of F or C')
    for dslice in data: # cycle over largest dimension to save memory
        if needs_copy:
            dslice = dslice.copy()
        if nan2zero:
            dslice[np.isnan(dslice)] = 0
        if mx:
            dslice[dslice > mx] = mx
        if mn:
            dslice[dslice < mn] = mn
        if intercept:
            dslice -= intercept
        if divslope != 1.0:
            dslice /= divslope
        if in_dtype == out_dtype:
            fileobj.write(dslice.tostring())
        elif in_dtype == out_dtype.newbyteorder('S'): # just byte swapped
            out_arr = dslice.byteswap()
            fileobj.write(out_arr.tostring())
        else:
            fileobj.write(dslice.astype(out_dtype).tostring())


def calculate_scale(data, out_dtype, allow_intercept):
    ''' Calculate scaling and optional intercept for data

    Parameters
    ----------
    data : array
    out_dtype : dtype
       output data type
    allow_intercept : bool
       If True allow non-zero intercept

    Returns
    -------
    scaling : None or float
       scalefactor to divide into data.  None if no valid data
    intercept : None or float
       intercept to subtract from data.  None if no valid data    
    mn : None or float
       minimum of finite value in data or None if this will not
       be used to threshold data
    mx : None or float
       minimum of finite value in data, or None if this will not
       be used to threshold data

    '''
    default_ret = (1.0, 0.0, None, None)
    in_dtype = data.dtype
    if np.can_cast(in_dtype, out_dtype):
        return default_ret
    in_type = in_dtype.type
    out_type = out_dtype.type
    if out_type in floating_point_types:
        return default_ret
    mn, mx = finite_range(data)
    if mn == np.inf: # No valid data
        return None, None, None, None
    info = np.iinfo(out_type)
    type_min = info.min
    type_max = info.max
    if in_type in integer_types:
        # scaling a big int type into a smaller one
        if mx <= type_max and mn >= type_min: # lucky; already in range
            return default_ret
        scaling, intercept = scale_min_max(mn, mx,
                                           out_type,
                                           allow_intercept)
        return scaling, intercept, None, None
    # should now be scaling a fp type to an int type
    if not in_type in np.sctypes['float']:
        raise TypeError('Unexpected input dtype %s' % in_dtype)
    scaling, intercept = scale_min_max(mn, mx, out_type,
                                        allow_intercept)
    return scaling, intercept, mn, mx


def scale_min_max(mn, mx, out_type, allow_intercept):
    ''' Return scaling and intercept min, max of data, given output type

    Returns ``scalefactor`` and ``intercept`` to best fit data with
    given ``mn`` and ``mx`` min and max values into range of data type
    with ``type_min`` and ``type_max`` min and max values for type.

    The calculated scaling is therefore::

        scaled_data = (data-intercept) / scalefactor

    Parameters
    ----------
    mn : scalar
       data minimum value
    mx : scalar
       data maximum value
    out_type : numpy type
       numpy type of output
    allow_intercept : bool
       If true, allow calculation of non-zero intercept.  Otherwise,
       returned intercept is always 0.0

    Returns
    -------
    scalefactor : numpy scalar, dtype=np.maximum_sctype(np.float)
       scalefactor by which to divide data after subtracting intercept
    intercept : numpy scalar, dtype=np.maximum_sctype(np.float)
       value to subtract from data before dividing by scalefactor

    >>> scale_min_max(0, 255, np.uint8, False)
    (1.0, 0.0)
    >>> scale_min_max(-128, 127, np.int8, False)
    (1.0, 0.0)
    >>> scale_min_max(0, 127, np.int8, False)
    (1.0, 0.0)
    >>> scaling, intercept = scale_min_max(0, 127, np.int8,  True)
    >>> np.allclose((0 - intercept) / scaling, -128)
    True
    >>> np.allclose((127 - intercept) / scaling, 127)
    True
    >>> scaling, intercept = scale_min_max(-10, -1, np.int8, True)
    >>> np.allclose((-10 - intercept) / scaling, -128)
    True
    >>> np.allclose((-1 - intercept) / scaling, 127)
    True
    >>> scaling, intercept = scale_min_max(1, 10, np.int8, True)
    >>> np.allclose((1 - intercept) / scaling, -128)
    True
    >>> np.allclose((10 - intercept) / scaling, 127)
    True

    Notes
    -----
    The large integers lead to python long types as max / min for type.
    To contain the rounding error, we need to use the maximum numpy
    float types when casting to float.
    
    '''
    if mn > mx:
        raise ValueError('min value > max value')
    try:
        info = np.iinfo(out_type)
    except ValueError:
        info = np.finfo(out_type)
    mn, mx, type_min, type_max = np.array(
        [mn, mx, info.min, info.max], np.maximum_sctype(np.float))
    # with intercept
    if allow_intercept:
        data_range = mx-mn
        if data_range == 0:
            return 1.0, mn
        type_range = type_max - type_min
        scaling = data_range / type_range
        intercept = mn - type_min * scaling
        return scaling, intercept
    # without intercept
    if mx == 0 and mn == 0:
        return 1.0, 0.0
    if type_min == 0: # uint
        if mn < 0 and mx > 0:
            raise ValueError('Cannot scale negative and positive '
                             'numbers to uint without intercept')
        if mx < 0:
            scaling = mn / type_max
        else:
            scaling = mx / type_max
    else: # int
        if abs(mx) >= abs(mn):
            scaling = mx / type_max
        else:
            scaling = mn / type_min
    return scaling, 0.0


def finite_range(arr):
    ''' Return range (min, max) of finite values of ``arr``

    Parameters
    ----------
    arr : array

    Returns
    -------
    mn : scalar
       minimum of values in (flattened) array
    mx : scalar
       maximum of values in (flattened) array
       
    Examples
    --------
    >>> a = np.array([[-1, 0, 1],[np.inf, np.nan, -np.inf]])
    >>> finite_range(a)
    (-1.0, 1.0)
    >>> a = np.array([[np.nan],[np.nan]])
    >>> finite_range(a)
    (inf, -inf)
    >>> a = np.array([[-3, 0, 1],[2,-1,4]], dtype=np.int)
    >>> finite_range(a)
    (-3, 4)
    >>> a = np.array([[1, 0, 1],[2,3,4]], dtype=np.uint)
    >>> finite_range(a)
    (0, 4)
    >>> a = a + 1j
    >>> finite_range(a)
    Traceback (most recent call last):
       ...
    TypeError: Can only handle floats and (u)ints
    '''
    # Resort array to slowest->fastest memory change indices
    stride_order = np.argsort(arr.strides)[::-1]
    sarr = arr.transpose(stride_order)
    typ = sarr.dtype.type
    if typ in integer_types:
        return np.min(sarr), np.max(sarr)
    if typ not in np.sctypes['float']:
        raise TypeError('Can only handle floats and (u)ints')
    # Loop to avoid big isfinite temporary
    mx = -np.inf
    mn = np.inf
    for s in xrange(sarr.shape[0]):
        tmp = sarr[s]
        tmp = tmp[np.isfinite(tmp)]
        if tmp.size:
            mx = max(np.max(tmp), mx)
            mn = min(np.min(tmp), mn)
    return mn, mx


class UnsupportedDataType():
    ''' Class to indicated data type not supported '''
    pass


class HeaderDataError(Exception):
    ''' Class to indicate error in getting or setting header data '''
    pass


class HeaderTypeError(Exception):
    ''' Class to indicate error in parameters into header functions '''
    pass


def allopen(fname, *args, **kwargs):
    ''' Generic file-like object open

    If input ``fname`` already looks like a file, pass through.
    If ``fname`` ends with recognizable compressed types, use python
    libraries to open as file-like objects (read or write)
    Otherwise, use standard ``open``.
    '''
    if hasattr(fname, 'write'):
        return fname
    if args:
        mode = args[0]
    elif 'mode' in kwargs:
        mode = kwargs['mode']
    else:
        mode = 'rb'
    if fname.endswith('.gz'):
        if ('w' in mode and
            len(args) < 2 and
            not 'compresslevel' in kwargs):
            kwargs['compresslevel'] = default_compresslevel
        import gzip
        opener = gzip.open
    elif fname.endswith('.bz2'):
        if ('w' in mode and
            len(args) < 3 and
            not 'compresslevel' in kwargs):
            kwargs['compresslevel'] = default_compresslevel
        import bz2
        opener = bz2.BZ2File
    else:
        opener = open
    return opener(fname, *args, **kwargs)

