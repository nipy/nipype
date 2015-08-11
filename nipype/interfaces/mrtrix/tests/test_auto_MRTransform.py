from __future__ import unicode_literals
# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from nipype.testing import assert_equal
from nipype.interfaces.mrtrix.preprocess import MRTransform

def test_MRTransform_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    debug=dict(argstr='-debug',
    position=1,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    flip_x=dict(argstr='-flipx',
    position=1,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_files=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    invert=dict(argstr='-inverse',
    position=1,
    ),
    out_filename=dict(argstr='%s',
    genfile=True,
    position=-1,
    ),
    quiet=dict(argstr='-quiet',
    position=1,
    ),
    reference_image=dict(argstr='-reference %s',
    position=1,
    ),
    replace_transform=dict(argstr='-replace',
    position=1,
    ),
    template_image=dict(argstr='-template %s',
    position=1,
    ),
    terminal_output=dict(nohash=True,
    ),
    transformation_file=dict(argstr='-transform %s',
    position=1,
    ),
    )
    inputs = MRTransform.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(inputs.traits()[key], metakey), value

def test_MRTransform_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = MRTransform.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            yield assert_equal, getattr(outputs.traits()[key], metakey), value

