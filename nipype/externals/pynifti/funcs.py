# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
''' Processor functions for images '''
import numpy as np

def squeeze_image(img):
    ''' Return image, remove axes length 1 at end of image shape

    For example, an image may have shape (10,20,30,1,1).  In this case
    squeeze will result in an image with shape (10,20,30).  See doctests
    for further description of behavior.

    Parameters
    ----------
    img : ``SpatialImage``

    Returns
    -------
    squeezed_img : ``SpatialImage``
       Copy of img, such that data, and data shape have been squeezed,
       for dimensions > 3rd, and at the end of the shape list

    Examples
    --------
    >>> import nipype.externals.pynifti as nf
    >>> shape = (10,20,30,1,1)
    >>> data = np.arange(np.prod(shape)).reshape(shape)
    >>> affine = np.eye(4)
    >>> img = nf.Nifti1Image(data, affine)
    >>> img.get_shape()
    (10, 20, 30, 1, 1)
    >>> img2 = squeeze_image(img)
    >>> img2.get_shape()
    (10, 20, 30)

    If the data are 3D then last dimensions of 1 are ignored

    >>> shape = (10,1,1)
    >>> data = np.arange(np.prod(shape)).reshape(shape)
    >>> img = nf.ni1.Nifti1Image(data, affine)
    >>> img.get_shape()
    (10, 1, 1)
    >>> img2 = squeeze_image(img)
    >>> img2.get_shape()
    (10, 1, 1)

    Only *final* dimensions of 1 are squeezed

    >>> shape = (1, 1, 5, 1, 2, 1, 1)
    >>> data = data.reshape(shape)
    >>> img = nf.ni1.Nifti1Image(data, affine)
    >>> img.get_shape()
    (1, 1, 5, 1, 2, 1, 1)
    >>> img2 = squeeze_image(img)
    >>> img2.get_shape()
    (1, 1, 5, 1, 2)
    '''
    klass = img.__class__
    shape = img.get_shape()
    slen = len(shape)
    if slen < 4:
        return klass.from_image(img)
    for bdim in shape[3::][::-1]:
        if bdim == 1:
           slen-=1
        else:
            break
    if slen == len(shape):
        return klass.from_image(img)
    shape = shape[:slen]
    data = img.get_data()
    data = data.reshape(shape)
    return klass(data,
                 img.get_affine(),
                 img.get_header(),
                 img.extra)


def concat_images(images):
    ''' Concatenate images in list to single image, along last dimension '''
    n_imgs = len(images)
    img0 = images[0]
    i0shape = img0.get_shape()
    affine = img0.get_affine()
    header = img0.get_header()
    out_shape = (n_imgs, ) + i0shape
    out_data = np.empty(out_shape)
    for i, img in enumerate(images):
        if not np.all(img.get_affine() == affine):
            raise ValueError('Affines do not match')
        out_data[i] = img.get_data()
    out_data = np.rollaxis(out_data, 0, len(i0shape)+1)
    klass = img0.__class__
    return klass(out_data, affine, header)

