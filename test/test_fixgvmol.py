import pytest
from zeetoo.fixgvmol import fix_cont


@pytest.fixture
def expected():
    return """

Created by GaussView 5.0.8
  5  4  0  0  0  0  0  0  0  0  0 V2000
    0.7531    0.9467    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098   -0.0622    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511    0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511   -0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.3169    0.9467    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
  1  4  1  0  0  0  0
  1  5  1  0  0  0  0
M END
"""


def test_missing_both(expected):
    cont = """

Created by GaussView 5.0.8
  5  4  0  0  0  0  0  0  0  0  0    0
    0.7531    0.9467    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098   -0.0622    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511    0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511   -0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.3169    0.9467    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
  1  4  1  0  0  0  0
  1  5  1  0  0  0  0
"""
    assert fix_cont(cont) == expected


def test_missing_version(expected):
    cont = """

Created by GaussView 5.0.8
  5  4  0  0  0  0  0  0  0  0  0    0
    0.7531    0.9467    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098   -0.0622    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511    0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511   -0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.3169    0.9467    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
  1  4  1  0  0  0  0
  1  5  1  0  0  0  0
M END
"""
    assert fix_cont(cont) == expected


def test_missing_end(expected):
    cont = """

Created by GaussView 5.0.8
  5  4  0  0  0  0  0  0  0  0  0 V2000
    0.7531    0.9467    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098   -0.0622    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511    0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
    1.1098    1.4511   -0.8737 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.3169    0.9467    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
  1  4  1  0  0  0  0
  1  5  1  0  0  0  0
"""
    assert fix_cont(cont) == expected


def test_input_ok(expected):
    assert fix_cont(expected) == expected
