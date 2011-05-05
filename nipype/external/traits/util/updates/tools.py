""" A collection of command-line tools for building encoded update.xml
files.
"""

from traits.util.updates.info_file import InfoFile
import os


def files2xml(filenames):
    """ Given a list of filenames, extracts the app version and log
    information from accompanying files produces an output xml string.

    There are no constraints or restrictions on the names or extensions
    of the input files.  They just need to be accompanied by a sidecar
    file named similarly, but with a ".info" extension, that can be
    loaded by the InfoFile class.

    If there is no .info file for a filename or an error occurs while constructing it
    a warning message is printed.
    """

    _xmlheader = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <!-- DO NOT EDIT MANUALLY -->
    <!-- Automatically generated file using traits.util.updates -->
    """

    xmlparts = [_xmlheader]
    for file in filenames:
        #info_file_name = "{0}.info".format(file)
        info_file_name = "%s.info" % (file,)
        if not os.path.exists(info_file_name):
            #print "Warning: {0} was not found.".format(info_file_name)
            print "Warning: %s was not found." % (info_file_name,)
            continue
        try:
            info = InfoFile.from_info_file(info_file_name)
            xml_list = info.get_xml()
        except:
            #print "Warning: Failure in creating XML for {0}".format(info_file_name)
            print "Warning: Failure in creating XML for %s" % (info_file_name,)
            continue
        xmlparts.append('<update_file>')
        xmlparts.extend(xml_list)
        xmlparts.append('</update_file>')

    return "\n".join(xmlparts)




