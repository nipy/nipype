


import md5
import os
import re
import warnings
from xml.etree import ElementTree as ET


#========================================================================
# Regex helpers for parsing file names and validating checksums.
#========================================================================

_version_in_name = re.compile("(\S*)[-](\d+\.\d+\.*\d*)\S*")

def _get_filename(filename):
    match = _version_in_name.search(filename)
    if match is None:
        raise ValueError, "Could not find name in filename: " + filename
    return match.group(1)

def _get_version(filename):
    match = _version_in_name.search(filename)
    if match is None:
        raise ValueError, "Could not find version in filename: " + filename
    return match.group(2)

def _get_checksum(filename):
    base, ext = os.path.splitext(filename)
    data = open(base).read()
    return md5.new(data).hexdigest()


filename_re = re.compile('filename: \s*(.*)\n')
version_re = re.compile('version: \s*(.*)\n')
checksum_re = re.compile('checksum: \s*(.*)\n')
desc_re = re.compile('\ndescription:\n')

codedict = {'filename':{'re':filename_re,
                    'get':_get_filename},
            'version': {'re':version_re,
                        'get':_get_version},
            'checksum': {'re':checksum_re,
                         'get':_get_checksum}
            }

class InfoFile:
    """Representation of an .info file, which provides metadata of another
    file (its "target").

    Important methods:

    @classmethod
    from_info_file(filename)

      construct an InfoFile object from a filename --- simple parser

      name: %filename% (if not present extracted from .info filename)
      version: %filename% (if not present it is extracted from name of file)
      checksum: md5hash (if not present it is computed from the basefile)
      html: (everything else in the file from the next line to the end)

    get_xml()
      return a list of xml elements for this file
    """

    # The filename of the update_file. This is not the full path -
    # see **location_root** below.
    filename = ""

    # The version of the target file
    version = None

    # Checksum of the target file
    checksum = None

    # A multi-line HTML document describing the changes between
    # this version and the previous version
    description = ""

    # The reported location of where self.filename can be found.  This gets
    # prepended to self.filename to form the full path.  Typically this will be
    # an HTTP URL, but this can be a URI for a local or LAN directory.
    # This field usually gets set by an external tool, and is not present
    # in the .info format.
    location = "./"

    # A function that takes a string (self.version) and returns something
    # that can be used to compare against the version-parsed version of
    # another VersionInfo object.
    version_parser = None

    #========================================================================
    # Constructors
    #========================================================================

    @classmethod
    def from_info_file(cls, filename):
        """ Construct an InfoFile instance from a .info file on disk.
        """
        str = open(filename).read()
        obj = cls()
        for attr in ['filename', 'version', 'checksum']:
            funcdict = codedict[attr]
            match = funcdict['re'].search(str)
            if match is None:
                value = funcdict['get'](filename)
            else:
                value = match.group(1)
            setattr(obj, attr, value)

        match = desc_re.search(str)
        if match is None:
            warnings.warn("Info file " + filename + " lacks a description: field")
        else:
            beg, end = match.span()
            start = str.find('\n', end)
            obj.description = str[start:]
        return obj

    @classmethod
    def from_target_file(cls, filename):
        """ Construct an InfoFile given the filename of the target file.
        """
        obj = cls(filename=filename)

        # Try to glean a version number from the file name
        try:
            version = _get_version(filename)
            obj.version = version
        except ValueError:
            pass
        return obj

    @classmethod
    def from_xml(cls, bytes):
        """ Returns a new InfoFile instance from a multi-line string of
        XML data
        """
        raise NotImplementedError

    def __init__(self, **kwargs):
        # Do a strict Traits-like construction
        for attr in ("filename", "version", "checksum", "description",
                     "location", "version_parser"):
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
        return

    #========================================================================
    # Public methods
    #========================================================================

    def to_xml(self):
        root = ET.Element("file")
        for attrname in ("version", "filename", "location", "checksum", "description"):
            node = ET.SubElement(root, attrname)
            node.text = getattr(self, attrname)
        return root

    def to_xml_str(self):
        """ Returns a multi-line string of XML representing the information in
        this object.
        """
        return ET.tostring(self.to_xml())

    def to_info_str(self):
        """ Returns a multi-line string in the .info file format
        """
        lines = []
        for attr in ["filename", "version", "checksum"]:
            lines.append(attr + ": " + getattr(self, attr))
        return "\n".join(lines) + "\ndescription:\n" + self.description + "\n"

    def __cmp__(self, other):
        """ Allows for comparing two VersionInfo objects so they can
        be presented in version-sorted order.  This is where we parse
        and interpretation of the **version** string attribute.
        """
        # TODO: Do something more intelligent here, if version parsers are missing
        if self.version_parser is not None:
            self_ver = self.version_parser(self.version)
        else:
            self_ver = self.version
        if other.version_parser is not None:
            other_ver = other.version_parser(other.version)
        else:
            other_ver = other.version
        if self_ver < other_ver:
            return -1
        elif self.ver == other_ver:
            return 0
        else:
            return 1


