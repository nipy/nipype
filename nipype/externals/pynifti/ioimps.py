''' IO implementatations '''

def guessed_imp(filespec):
    ''' Return implementation guessed from filespec '''
    raise NotImplementedError

class IOImplementation(object):
    def __init__(self, filespec = None):
        self._filespec = None
        self.set_filespec(filespec)
        
    def get_filespec(self):
        return self._filespec

    def set_filespec(self, filespec):
        self._filespec = filespec

    def to_filespec(self, filespec=None):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError

    def get_affine(self):
        raise NotImplementedError

    def set_affine(self, affine):
        raise NotImplementedError

    def get_output_space(self):
        raise NotImplementedError

    def set_output_space(self, output_space):
        raise NotImplementedError

    def get_data_shape(self):
        raise NotImplementedError

    def set_data_shape(self, shape):
        raise NotImplementedError

    def get_data_dtype(self):
        raise NotImplementedError

    def set_data_dtype(self, dtype):
        raise NotImplementedError

    def write_slice(data, slicedef, outfile = None):
        raise NotImplementedError

    def as_image(self, image_maker):
        raise NotImplementedError

    def save_image(self, image, filespec=None, io=None):
        raise NotImplementedError

    def same_as_image(self, image):
        raise NotImplementedError

    def get_hash(self):
        raise NotImplementedError

default_io = IOImplementation

