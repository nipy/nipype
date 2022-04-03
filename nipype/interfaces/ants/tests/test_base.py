from nipype.interfaces.ants.base import Info

import pytest

# fmt: off
ANTS_VERSIONS = [("""\
ANTs Version: 2.3.3.dev168-g29bdf
Compiled: Jun  9 2020 03:44:55

""", "2.3.3"), ("""\
ANTs Version: v2.3.5.post76-g28dd25c
Compiled: Nov 16 2021 14:57:48

""", "2.3.5"), ("""\
ANTs Version: v2.1.0.post789-g0740f
Compiled: I don't still have this so not going to pretend

""", "2.2.0"),
]
# fmt: on


@pytest.mark.parametrize("raw_info, version", ANTS_VERSIONS)
def test_version_parser(raw_info, version):
    assert Info.parse_version(raw_info) == version
