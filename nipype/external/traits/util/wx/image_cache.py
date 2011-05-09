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
""" An image cache. """


# Major package imports.
import wx


class ImageCache:
    """ An image cache. """

    def __init__(self, width, height):
        """ Creates a new image cache. """

        self._width = width
        self._height = height

        # The images in the cache!
        self._images = {} # {filename : bitmap}

        return

    ###########################################################################
    # 'ImageCache' interface.
    ###########################################################################

    def get_image(self, filename):
        """ Returns the specified image (currently as a bitmap). """

        # Try the cache first.
        bmp = self._images.get(filename)
        if bmp is None:
            # Load the image from the file and add it to the list.
            #
            # N.B 'wx.BITMAP_TYPE_ANY' tells wxPython to attempt to autodetect
            # --- the image format.
            image = wx.Image(filename, wx.BITMAP_TYPE_ANY)

            # We force all images in the cache to be the same size.
            self._scale(image)

            # We also force them to be bitmaps!
            bmp = image.ConvertToBitmap()

            # Add the bitmap to the cache!
            self._images[filename] = bmp

        return bmp

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _scale(self, image):
        """ Scales the specified image (if necessary). """

        if image.GetWidth() != self._width or image.GetHeight()!= self._height:
            image.Rescale(self._width, self._height)

        return image

#### EOF ######################################################################
