import os
from tempfile import mkstemp

from nipype.testing import assert_equal
from nipype.utils.filemanip import save_json, load_json

def test_json():
    # Simple roundtrip test of json files, just a sanity check.
    adict = dict(a='one', c='three', b='two')
    fd, name = mkstemp(suffix='.json')
    save_json(name, adict) # save_json closes the file
    new_dict = load_json(name)
    os.unlink(name)
    yield assert_equal, sorted(adict.items()), sorted(new_dict.items())
