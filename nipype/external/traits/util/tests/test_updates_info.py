#------------------------------------------------------------------------------
# Copyright (c) 2010, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Travis Oliphant, Enthought, Inc.
#
# Description:
#     Unittest of InfoFile and files2xml
#------------------------------------------------------------------------------
import sys
import os.path
import unittest

from traits.util.updates.tools import InfoFile, files2xml


test_file = """
Some random text in
an aribtrary file
"""
test_file_info = """
html:
<center><p>Test File Info</p></center>
<p>
This is the multiline
test file that
is the only thing we actually
need in an info
file
</p>
<p>It has multilevel levels of <em>embedded</em>&nbsp;HTML
markup and this markup should be preserved
accurately in the XML transcription process.
</p>
"""

class Tests(unittest.TestCase):

    def setUp(self):
        name = 'test_file-1.0.0-1.txt'
        infoname = name + '.info'
        fid = open(name,'w')
        fid.write(test_file)
        fid.close()
        fid = open(infoname, 'w')
        fid.write(test_file_info)
        fid.close()
        self.files = [name]

    def test_files2xml(self):
        print files2xml(self.files)

    def tearDown(self):
        os.unlink(self.files[0])
        os.unlink(self.files[0]+'.info')


if __name__ == "__main__":
    unittest.main()
