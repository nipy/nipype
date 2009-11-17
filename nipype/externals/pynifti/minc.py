import numpy as np

from nipype.externals.pynifti.spatialimages import SpatialImage
from nipype.externals.pynifti.volumeutils import allopen

_dt_dict = {
    ('b','unsigned'): np.uint8,
    ('b','signed__'): np.int8,
    ('c','unsigned'): 'S1',
    ('h','unsigned'): np.uint16,
    ('h','signed__'): np.int16,
    ('i','unsigned'): np.uint32,
    ('i','signed__'): np.int32,
    }

# See http://www.bic.mni.mcgill.ca/software/minc/minc1_format/node15.html
_default_dir_cos = {
    'xspace': [1,0,0],
    'yspace': [0,1,0],
    'zspace': [0,0,1]}

def get_netcdf_fileobj():
    """Return netcdf fileobj.
    The import of netcdf from scipy.io is slow, so only do it when needed.
    """
    from scipy.io.netcdf import netcdf_file
    class netcdf_fileobj(netcdf_file):
        def __init__(self, fileobj):
            # Older versions of netcdf_file expected filename and mode.
            # Newer versions allow passing of file objects.  We check
            # whether calling netcdf_file raises a TypeError (meaning we
            # have the old version) and deal with it if we do.
            try:
                super(netcdf_fileobj, self).__init__(fileobj)
            except TypeError:
                self._buffer = fileobj
                self._parse()
    return netcdf_fileobj


class MincError(Exception):
    pass


class MincHeader(object):
    def __init__(self, mincfile, endianness=None, check=True):
        self.endianness = '>'
        self._mincfile = mincfile
        self._image = mincfile.variables['image']
        self._dim_names = self._image.dimensions
        # The code below will error with vector_dimensions.  See:
        # http://www.bic.mni.mcgill.ca/software/minc/minc1_format/node3.html
        # http://www.bic.mni.mcgill.ca/software/minc/prog_guide/node11.html
        self._dims = [self._mincfile.variables[s]
                      for s in self._dim_names]
        self._spatial_dims = [name for name in self._dim_names
                             if name.endswith('space')]
        if check:
            self.check_fix()

    def __getitem__(self, name):
        """
        Get a field's value from the MINC file.

        It first checks in variables, then attributes
        and finally the dimensions of the MINC file.

        """
        mnc = self._mincfile
        for dict_like in (mnc.variables, mnc.attributes, mnc.dimensions):
            try:
                return dict_like[name]
            except KeyError:
                pass
        raise KeyError('"%s" not found in variables, '
                       'attributes or dimensions of MINC file')

    def __iter__(self):
        return iter(self.keys())

    def keys(self):
        return list(self._mincfile.variables.keys() +
                    self._mincfile.attributes.keys() +
                    self._mincfile.dimensions.keys())

    def values(self):
        return [self[key] for key in self]

    def items(self):
        return zip(self.keys(), self.values())

    @classmethod
    def from_fileobj(klass, fileobj, endianness=None, check=True):
        netcdf_fileobj = get_netcdf_fileobj()
        ncdf_obj = netcdf_fileobj(fileobj)
        return klass(ncdf_obj, endianness, check)

    def check_fix(self):
        # We don't currently support irregular spacing
        # http://www.bic.mni.mcgill.ca/software/minc/minc1_format/node15.html
        for dim in self._dims:
            if dim.spacing != 'regular__':
                raise ValueError('Irregular spacing not supported')

    def get_data_shape(self):
        return self._image.shape
        
    def get_data_dtype(self):
        typecode = self._image.typecode()
        if typecode == 'f':
            dtt = np.dtype(np.float32)
        elif typecode == 'd':
            dtt = np.dtype(np.float64)
        else:
            signtype = self._image.signtype
            dtt = _dt_dict[(typecode, signtype)]
        return np.dtype(dtt).newbyteorder('>')

    def get_zooms(self):
        return tuple(
            [float(dim.step) for dim in self._dims])

    def get_best_affine(self):
        nspatial = len(self._spatial_dims)
        rot_mat = np.eye(nspatial)
        steps = np.zeros((nspatial,))
        starts = np.zeros((nspatial,))
        dim_names = list(self._dim_names) # for indexing in loop
        for i, name in enumerate(self._spatial_dims):
            dim = self._dims[dim_names.index(name)]
            try:
                dir_cos = dim.direction_cosines
            except AttributeError:
                dir_cos = _default_dir_cos[name]
            rot_mat[:,i] = dir_cos
            steps[i] = dim.step
            starts[i] = dim.start
        origin = np.dot(rot_mat, starts)
        aff = np.eye(nspatial+1)
        aff[:nspatial,:nspatial] = rot_mat * steps
        aff[:nspatial,nspatial] = origin
        return aff

    def get_unscaled_data(self):
        dtype = self.get_data_dtype()
        return np.asarray(self._image).view(dtype)

    def _get_valid_range(self):
        ''' Return valid range for image data

        The valid range can come from the image 'valid_range' or
        image 'valid_min' and 'valid_max', or, failing that, from the
        data type range
        '''
        ddt = self.get_data_dtype()
        info = np.iinfo(ddt.type)
        try:
            valid_range = self._image.valid_range
        except AttributeError:
            try:
                valid_range = [self._image.valid_min,
                               self._image.valid_max]
            except AttributeError:
                valid_range = [info.min, info.max]
        if valid_range[0] < info.min or valid_range[1] > info.max:
            raise ValueError('Valid range outside input '
                             'data type range')
        return np.asarray(valid_range, dtype=np.float)

    def _normalize(self, data):
        """

        http://www.bic.mni.mcgill.ca/software/minc/prog_guide/node13.html
        
        MINC normalization uses "image-min" and "image-max" variables to
        map the data from the valid range of the image to the range
        specified by "image-min" and "image-max".

        The "image-max" and "image-min" are variables that describe the
        "max" and "min" of image over some dimensions of "image".

        The usual case is that "image" has dimensions ["zspace",
        "yspace", "xspace"] and "image-max" has dimensions
        ["zspace"]. 
        """
        ddt = self.get_data_dtype()
        if ddt.type in np.sctypes['float']:
            return data
        # the MINC standard appears to allow the following variables to
        # be undefined.
        # http://www.bic.mni.mcgill.ca/software/minc/minc1_format/node16.html
        # It wasn't immediately obvious what the defaults were.
        image_max = self._mincfile.variables['image-max']
        image_min = self._mincfile.variables['image-min']
        if image_max.dimensions != image_min.dimensions:
            raise MincError('"image-max" and "image-min" do not '
                             'have the same dimensions')
        nscales = len(image_max.dimensions)
        if image_max.dimensions != self._dim_names[:nscales]:
            raise MincError('image-max and image dimensions '
                            'do not match')
        dmin, dmax = self._get_valid_range()

        if nscales == 0:
            imax = np.asarray(image_max)
            imin = np.asarray(image_min)
            sc = (imax-imin) / (dmax-dmin)
            return np.clip(data, dmin, dmax) * sc + (imin - dmin * sc)
            
        out_data = np.empty(data.shape, np.float)

        def _norm_slice(sdef):
            imax = image_max[sdef]
            imin = image_min[sdef]
            in_data = np.clip(data[sdef], dmin, dmax)
            sc = (imax-imin) / (dmax-dmin)
            return in_data * sc + (imin - dmin * sc)

        if nscales == 1:
            for i in range(data.shape[0]):
                out_data[i] = _norm_slice(i)
        elif nscales == 2:
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    out_data[i,j] = _norm_slice((i,j))
        else:
            raise MincError('More than two scaling dimensions')
        return out_data

    def get_scaled_data(self):
        return self._normalize(self.get_unscaled_data())
    

class MincImage(SpatialImage):
    _header_maker = MincHeader
    
    def _set_header(self, header):
        self._header = header

    def get_affine(self):
        ''' Get affine, correcting for spatial dims '''
        aff = self._header.get_best_affine()
        if aff.shape != (4,4):
            raise MincError('Image does not have 3 spatial dimensions')
        return aff
        
    def get_data(self):
        ''' Lazy load of data '''
        if not self._data is None:
            return self._data
        self._data = self._header.get_scaled_data()
        return self._data

    def get_shape(self):
        if not self._data is None:
            return self._data.shape
        return self._header.get_data_shape()
    
    def get_data_dtype(self):
        return self._header.get_data_dtype()
    
    @classmethod
    def from_filespec(klass, filespec):
        files = klass.filespec_to_files(filespec)
        return klass.from_files(files)
    
    @classmethod
    def from_files(klass, files):
        fname = files['image']
        header = klass._header_maker.from_fileobj(allopen(fname))
        affine = header.get_best_affine()
        ret =  klass(None, affine, header)
        ret._files = files
        return ret
    
    @classmethod
    def from_image(klass, img):
        return klass(img.get_data(),
                     img.get_affine(),
                     img.get_header(),
                     img.extra)
    
    @staticmethod
    def filespec_to_files(filespec):
        return {'image':filespec}
        
    @classmethod
    def load(klass, filespec):
        return klass.from_filespec(filespec)


load = MincImage.load
