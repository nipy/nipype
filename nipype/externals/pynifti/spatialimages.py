''' Very simple spatial image class

The image class maintains the association between a 3D (or greater)
array, and an affine transform that maps voxel coordinates to some real
world space.  It also has a ``header`` - some standard set of meta-data
that is specific to the image format - and ``extra`` - a dictionary
container for any other metadata.

It has attributes::

    extra
    filename (read only)
    
and methods::

    .get_data()
    .get_affine()
    .get_header()
    .to_files() # writes image out to passed or
    .get_raw_data()
    .write_data(fileobj)
    .write_raw_data(fileobj)

There are several ways of writing data.
=======================================

There is the usual way, which is the default::

    img.write_data(data, fileobj)

and that is, to take the data array, ``data``, and cast it to the
datatype the header expects, setting any available header scaling
into the header to help the data match.

You can get the data out again with of::

    img.get_data(fileobj)

Less commonly, you might want to fetch out the unscaled array via
the header::

    unscaled_data = img.get_raw_data(fileobj)

then do something with it.  Then put it back again::

    img.write_raw_data(modifed_unscaled_data, fileobj)

Sometimes you might to avoid any loss of precision by making the
data type the same as the input::

    hdr = img.get_header()
    hdr.set_data_dtype(data.dtype)
    img.write_data(data, fileobj)

'''

class SpatialImage(object):
    _header_maker = dict
    ''' Template class for lightweight image '''
    def __init__(self, data, affine, header=None, extra=None):
        if extra is None:
            extra = {}
        self._data = data
        self._affine = affine
        self.extra = extra
        self._set_header(header)
        self._files = {}
        
    def __str__(self):
        shape = self.get_shape()
        affine = self.get_affine()
        return '\n'.join((
                str(self.__class__),
                'data shape %s' % (shape,),
                'affine: ',
                '%s' % affine,
                'metadata:',
                '%s' % self._header))

    def get_data(self):
        return self._data

    def get_shape(self):
        if self._data:
            return self._data.shape

    def get_data_dtype(self):
        raise NotImplementedError

    def set_data_dtype(self, dtype):
        raise NotImplementedError

    def get_affine(self):
        return self._affine

    def get_header(self):
        return self._header

    def _set_header(self, header=None):
        if header is None:
            self._header = self._header_maker()
            return
        # we need to replicate the endianness, for the case where we are
        # creating an image from files, and we have not yet loaded the
        # data.  In that case we need to have the header maintain its
        # endianness to get the correct interpretation of the data
        self._header = self._header_maker(endianness=header.endianness)
        for key, value in header.items():
            if key in self._header:
                self._header[key] = value
            elif key not in self.extra:
                self.extra[key] = value

    @classmethod
    def from_filespec(klass, filespec):
        raise NotImplementedError

    def from_files(klass, files):
        raise NotImplementedError

    def from_image(klass, img):
        raise NotImplementedError

    @staticmethod
    def filespec_to_files(filespec):
        raise NotImplementedError
    
    def to_filespec(self, filespec):
        raise NotImplementedError

    def to_files(self, files=None):
        raise NotImplementedError
