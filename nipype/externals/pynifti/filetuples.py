''' Classes for containing filename pairs, triplets etc, with expected extensions '''

import os

class FileTuplesError(Exception):
    pass


class FileTuples(object):
    ''' Class to accept and check filenames for compatibility with
    standard'''
    def __init__(self, types=(),
                 default_type=None, 
                 ignored_suffixes=(),
                 enforce_extensions=True):
        ''' Initialize FileTuples object

        Parameters
        ----------
        types : sequence of sequences, iptional
            sequence of (name, extension) sequences defining types
        default_type : None or string, optional
            string identifying name (above) of default type, when type
            not specified.  If ``None``, use the name of the first
            type
        ignored_suffixes : sequence of strings, optional
            suffixes that should be ignored when looking for
            extensions - e.g ('.gz', '.bz2')
        enforce_extensions : {True, False}, optional
            If True, raise an error when attempting to set value to
            type which has the wrong extension

        Examples
        --------
        >>> fn = FileTuples((('t1', '.ext1'), ('t2', '.ext2')))
        >>> fn.types
        (('t1', '.ext1'), ('t2', '.ext2'))
        >>> fn.get_filenames()
        (None, None)
        >>> fn.default_type
        't1'
        >>> fn = FileTuples((('t1', '.ext1'), ('t2', '.ext2')), default_type='t2')
        >>> fn.default_type
        't2'
        >>> fn = FileTuples((('t1', '.ext1'), ('t2', '.ext2')), ignored_suffixes=('.bz2', '.gz'))
        '''
        self.types = types
        if default_type is None:
            if types:
                default_type = types[0][0]
        self.default_type = default_type
        self.ignored_suffixes = ignored_suffixes
        self.enforce_extensions = enforce_extensions
        self._values = {}
        self._names = []
        for tt in types:
            self._add_type_value(*tt)

    def _add_type_value(self, name, ext=None):
        self._values[name] = {
                'filename':None,
                'file':None,
                'ext':ext}
        self._names.append(name)
        
    def add_type(self, name, extension=None):
        ''' Add a type to the type list

        Parameters
        ----------
        name : string
            name for type
        extension : string
            default extension for this type

	Returns
	-------
	None

	Examples
	--------
	>>> fn = FileTuples()
        >>> fn.types
        ()
        >>> fn.get_file_of_type('all')
        ()
        >>> fn.default_type

        >>> fn.add_type('test', '.tst')
        >>> fn.types
        (('test', '.tst'),)
        >>> fn.get_file_of_type('all')
        (None,)
        >>> fn.default_type
        'test'
        >>> fn.add_type('test2', '.tst2')
        >>> fn.default_type
        'test'
    	'''
        if not self.types and not self.default_type:
            self.default_type = name
        self.types += ((name, extension),)
        self._add_type_value(name, extension)

    def get_filenames(self):
        ''' Get filenames from object

        Parameters
        ----------
        None

        Returns
        -------
        filenames : tuple of string
            tuple of filenames, one element per type
        '''
        filenames = []
        for name in self._names:
            filenames.append(self._values[name]['filename'])
        return tuple(filenames)

    def set_filenames(self, input_filename):
        ''' Set filename(s) from example filename

        Parameters
        ----------
        filename : string
            Example filename.  If ``self.enforce_extensions`` is True,
            then filename must have one of the defined extensions from
            the types list.  If ``self.enforce_extensions`` is False,
            then the other filenames are guessed at by adding
            extensions to the base filename.  Ignored suffixes (from
            ``self.ignored_suffixes``) append themselves to the end of
            all the filenames set here.

        Returns
        -------
        None

        Examples
        --------
        >>> fn = FileTuples(types=(('t1','.ext1'),('t2', '.ext2')))
        >>> fn.enforce_extensions = True
        >>> fn.set_filenames('/path/test.ext1')
        >>> fn.get_filenames()
        ('/path/test.ext1', '/path/test.ext2')
        >>> fn.set_filenames('/path/test.ext2')
        >>> fn.get_filenames()
        ('/path/test.ext1', '/path/test.ext2')
        >>> # bare file roots without extensions get them added
        >>> fn.set_filenames('/path/test')
        >>> fn.get_filenames()
        ('/path/test.ext1', '/path/test.ext2')
        >>> fn.enforce_extensions = False
        >>> fn.set_filenames('/path/test.funny')
        >>> fn.get_filenames()
        ('/path/test.funny', '/path/test.ext2')
        '''
        if not isinstance(input_filename, basestring):
            raise FileTuplesError('Need file name as input to set_filenames')
        if input_filename.endswith('.'):
            input_filename = input_filename[:-1]
        filename, found_ext, ignored, guessed_name = \
                  self._parse_filename(input_filename)
        # Flag cases where we just set the input name directly
        direct_set_name = None
        if self.enforce_extensions:
            if guessed_name is None:
                # no match - maybe there was no extension atall or the
                # wrong extension
                if found_ext:
                    # an extension, but the wrong one
                    expected = [value['ext']
                                for name, value in self._values.items()
                                if value['ext']]
                    raise FileTuplesError(
                        'File extension "%s" was not in expected list: %s'
                        % (found_ext, expected))
                elif ignored: # there was no extension, but an ignored suffix
                    # This is a special case like 'test.gz' (where .gz
                    # is ignored). It's confusing to change
                    # this to test.img.gz, or test.gz.img, so error
                    raise FileTuplesError(
                        'Confusing gnored suffix %s without extension'
                        % ignored)
        else: # not enforcing extensions
            # if there's an extension, we set the filename directly
            # from input.  Also, if there was no extension, but an
            # ignored suffixes ('test.gz' type case), we set the
            # filename directly.  Otherwise (no extension, no ignored
            # suffix), we stay with the default, which is to add the
            # default extensions according to type.
            if found_ext or ignored:
                direct_set_name = self.default_type
        for name, value in self._values.items():
            if name == direct_set_name:
                self.set_file_of_type(name, input_filename)
                continue
            fname = filename
            if value['ext']:
                fname += value['ext']
            if ignored:
                fname += ignored       
            self._values[name]['filename'] = fname
            self._values[name]['file'] = fname

    def get_file_of_type(self, typespec='all'):
        ''' Get files of specified type

        Parameters
        ----------
        typespec : string
            either name in types, or "all"

        Returns
        -------
        files : file, or tuple
            If typespec == "all", return all files
            Otherwise return file matching name in typespec

        Examples
        --------
        >>> fn = FileTuples(types=(('t1',),('t2',)))
        >>> fn.get_file_of_type()
        (None, None)
        >>> fn.get_file_of_type('all')
        (None, None)
        >>> fn.get_file_of_type('t1')

        >>> fn.set_file_of_type('t1', 'test_file')
        >>> fn.get_file_of_type('all')
        ('test_file', None)
        >>> fn.get_file_of_type('t1')
        'test_file'
        '''
        if typespec == 'all':
            files = []
            for name in self._names:
                files.append(self._values[name]['file'])
            return tuple(files)
        try:
            value = self._values[typespec]['file']
        except KeyError:
            raise FileTuplesError('No file type of name "%s"' % typespec)
        return value
    
    def set_file_of_type(self, name, fileobj):
        ''' Set value of file for given type name *name*

        Parameters
        ----------
        name : string
            name identifying type of file to return
        fileobj : string or file-like object
            value to add for this *name*

        Examples
        --------
        >>> fn = FileTuples((('t1', 'ext1'),('t2', 'ext2')))
        >>> fn.enforce_extensions = True
        >>> fn.set_file_of_type('t1', 'test_name.ext1')
        >>> fn.get_file_of_type('t1')
        'test_name.ext1'
        >>> fn.ignored_suffixes = (('.gz',))
        >>> fn.set_file_of_type('t1', 'test_name.ext1.gz')
        >>> fn.get_file_of_type('t1')
        'test_name.ext1.gz'
        '''
        if isinstance(fileobj, basestring):
            # this is a filename
            if self.enforce_extensions:
                self._check_extension(name, fileobj)
            self._values[name]['filename'] = fileobj
            self._values[name]['file'] = fileobj
            return
        # not a filename, assume fileobj
        self._values[name]['filename'] = None
        self._values[name]['file'] = fileobj

    def _parse_filename(self, filename):
        ''' Splits filename into tuple of
        (fileroot, extension, ignored_suffix, guessed_name)

        >>> fn = FileTuples((('t1', 'ext1'),('t2', 'ext2')))
        >>> # (not lack of dots above)
        >>> fn._parse_filename('/path/fname.funny')
        ('/path/fname', '.funny', None, None)
        >>> fn._parse_filename('/path/fnameext2')
        ('/path/fname', 'ext2', None, 't2')
        >>> fn.ignored_suffixes = ('.gz',)
        >>> fn._parse_filename('/path/fnameext2')
        ('/path/fname', 'ext2', None, 't2')
        >>> fn._parse_filename('/path/fnameext2.gz')
        ('/path/fname', 'ext2', '.gz', 't2')
        '''
        ignored = None
        for ext in self.ignored_suffixes:
            if filename.endswith(ext):
                filename = filename[:-(len(ext))]
                ignored = ext
        guessed_name = None
        found_ext = None
        for name, value in self._values.items():
            ext = value['ext']
            if ext and filename.endswith(ext):
                filename = filename[:-(len(ext))]
                guessed_name = name
                found_ext = ext
                break
        else:
            filename, found_ext = os.path.splitext(filename)
        return (filename, found_ext, ignored, guessed_name)
            
    def _check_extension(self, name, filename):
        ''' Check, maybe change filename based on type given in *name*
        '''
        filename, found_ext, ignored, guessed_name = \
                   self._parse_filename(filename)
        good_ext = self._values[name]['ext']
        if good_ext and not found_ext == good_ext:
            raise FileTuplesError('Filename "%s" should have extension %s' %
                                (filename, good_ext)) 
