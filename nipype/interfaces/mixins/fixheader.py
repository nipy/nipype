from ..base import BaseInterface, BaseInterfaceInputSpec, traits
from ...utils.imagemanip import copy_header as _copy_header


class CopyHeaderInputSpec(BaseInterfaceInputSpec):
    copy_header = traits.Bool(
        desc="Copy headers of the input image into the output image"
    )


class CopyHeaderInterface(BaseInterface):
    """Copy headers if the copy_header input is ``True``

    This interface mixin adds a post-run hook that allows for copying
    an input header to an output file.
    The subclass should specify a ``_copy_header_map`` that maps the **output**
    image to the **input** image whose header should be copied.

    This feature is intended for tools that are intended to adjust voxel data without
    modifying the header, but for some reason do not reliably preserve the header.

    Here we show an example interface that takes advantage of the mixin by simply
    setting the data block:

    >>> import os
    >>> import numpy as np
    >>> import nibabel as nb
    >>> from nipype.interfaces.base import SimpleInterface, TraitedSpec, File
    >>> from nipype.interfaces.mixins import CopyHeaderInputSpec, CopyHeaderInterface

    >>> class ZerofileInputSpec(CopyHeaderInputSpec):
    ...     in_file = File(mandatory=True, exists=True)

    >>> class ZerofileOutputSpec(TraitedSpec):
    ...     out_file = File()

    >>> class ZerofileInterface(SimpleInterface, CopyHeaderInterface):
    ...     input_spec = ZerofileInputSpec
    ...     output_spec = ZerofileOutputSpec
    ...     _copy_header_map = {'out_file': 'in_file'}
    ...
    ...     def _run_interface(self, runtime):
    ...         img = nb.load(self.inputs.in_file)
    ...         # Just set the data. Let the CopyHeaderInterface mixin fix the affine and header.
    ...         nb.Nifti1Image(np.zeros(img.shape, dtype=np.uint8), None).to_filename('out.nii')
    ...         self._results = {'out_file':  os.path.abspath('out.nii')}
    ...         return runtime

    Consider a file of all ones and a non-trivial affine:

    >>> in_file = 'test.nii'
    >>> nb.Nifti1Image(np.ones((5,5,5), dtype=np.int16),
    ...                affine=np.diag((4, 3, 2, 1))).to_filename(in_file)

    The default behavior would produce a file with similar data:

    >>> res = ZerofileInterface(in_file=in_file).run()
    >>> out_img = nb.load(res.outputs.out_file)
    >>> out_img.shape
    (5, 5, 5)
    >>> np.all(out_img.get_fdata() == 0)
    True

    An updated data type:

    >>> out_img.get_data_dtype()
    dtype('uint8')

    But a different affine:

    >>> np.array_equal(out_img.affine, np.diag((4, 3, 2, 1)))
    False

    With ``copy_header=True``, then the affine is also equal:

    >>> res = ZerofileInterface(in_file=in_file, copy_header=True).run()
    >>> out_img = nb.load(res.outputs.out_file)
    >>> np.array_equal(out_img.affine, np.diag((4, 3, 2, 1)))
    True

    The data properties remain as expected:

    >>> out_img.shape
    (5, 5, 5)
    >>> out_img.get_data_dtype()
    dtype('uint8')
    >>> np.all(out_img.get_fdata() == 0)
    True

    By default, the data type of the output file is permitted to vary from the
    inputs. That is, the data type is preserved.
    If the data type of the original file is preferred, the ``_copy_header_map``
    can indicate the output data type should **not** be preserved by providing a
    tuple of the input and ``False``.

    >>> ZerofileInterface._copy_header_map['out_file'] = ('in_file', False)

    >>> res = ZerofileInterface(in_file=in_file, copy_header=True).run()
    >>> out_img = nb.load(res.outputs.out_file)
    >>> out_img.get_data_dtype()
    dtype('<i2')

    Again, the affine is updated.

    >>> np.array_equal(out_img.affine, np.diag((4, 3, 2, 1)))
    True
    >>> out_img.shape
    (5, 5, 5)
    >>> np.all(out_img.get_fdata() == 0)
    True

    Providing a tuple where the second value is ``True`` is also permissible to
    achieve the default behavior.

    """

    _copy_header_map = None

    def _post_run_hook(self, runtime):
        """Copy headers for outputs, if required."""
        runtime = super()._post_run_hook(runtime)

        if self._copy_header_map is None or not self.inputs.copy_header:
            return runtime

        inputs = self.inputs.get_traitsfree()
        outputs = self.aggregate_outputs(runtime=runtime).get_traitsfree()
        defined_outputs = set(outputs.keys()).intersection(self._copy_header_map.keys())
        for out in defined_outputs:
            inp = self._copy_header_map[out]
            keep_dtype = True
            if isinstance(inp, tuple):
                inp, keep_dtype = inp
            _copy_header(inputs[inp], outputs[out], keep_dtype=keep_dtype)

        return runtime
