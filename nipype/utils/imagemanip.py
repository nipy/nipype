"""Image manipulation utilities (mostly, NiBabel manipulations)."""
import nibabel as nb


def copy_header(header_file, in_file, keep_dtype=True):
    """Copy header from a reference image onto another image."""
    hdr_img = nb.load(header_file)
    out_img = nb.load(in_file, mmap=False)
    hdr = hdr_img.header.copy()
    if keep_dtype:
        hdr.set_data_dtype(out_img.get_data_dtype())

    new_img = out_img.__class__(out_img.dataobj, None, hdr)
    if not keep_dtype:
        new_img.set_data_dtype(hdr_img.get_data_dtype())

    new_img.to_filename(in_file)
    return in_file
