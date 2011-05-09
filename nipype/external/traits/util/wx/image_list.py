#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought util package component>
#------------------------------------------------------------------------------
""" A cached image list. """


# Major package imports.
import wx


# fixme: rename to 'CachedImageList'?!?
class ImageList(wx.ImageList):
    """ A cached image list. """

    def __init__(self, width, height):
        """ Creates a new cached image list. """

        # Base-class constructor.
        wx.ImageList.__init__(self, width, height)

        self._width = width
        self._height = height

        # Cache of the indexes of the images in the list!
        self._cache = {} # {filename : index}

        return

    ###########################################################################
    # 'ImageList' interface.
    ###########################################################################

    def GetIndex(self, filename):
        """ Returns the index of the specified image.

        The image will be loaded and added to the image list if it is not
        already there.

        """

        # If the icon is a string then it is the filename of some kind of
        # image (e.g 'foo.gif', 'image/foo.png' etc).
        if isinstance(filename, basestring):
            # Try the cache first.
            index = self._cache.get(filename)
            if index is None:
                # Load the image from the file and add it to the list.
                #
                # N.B 'wx.BITMAP_TYPE_ANY' tells wxPython to attempt to
                # ---- autodetect the image format.
                image = wx.Image(filename, wx.BITMAP_TYPE_ANY)

                # We force all images in the cache to be the same size.
                self._scale(image)

                # We also force them to be bitmaps!
                bmp = image.ConvertToBitmap()

                # Add the bitmap to the actual list...
                index = self.Add(bmp)

                # ... and update the cache.
                self._cache[filename] = index

        # Otherwise the icon is *actually* an icon (in our case, probably
        # related to a MIME type).
        else:
            #image = filename
            #self._scale(image)
            #bmp = image.ConvertToBitmap()
            #index = self.Add(bmp)

            #return index

            icon = filename

            # We also force them to be bitmaps!
            bmp = wx.EmptyBitmap(self._width, self._height)
            bmp.CopyFromIcon(icon)
            # We force all images in the cache to be the same size.
            image = wx.ImageFromBitmap(bmp)
            self._scale(image)

            bmp = image.ConvertToBitmap()

            index = self.Add(bmp)

        return index

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _scale(self, image):
        """ Scales the specified image (if necessary). """

        if image.GetWidth() != self._width or image.GetHeight()!= self._height:
            image.Rescale(self._width, self._height)

        return image

#### EOF ######################################################################
