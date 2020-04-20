from io import StringIO
from pathlib import Path, PurePosixPath

from zeetoo import sdf_to_gjf as sdf

import pytest
from unittest import mock


def test_link0_empty():
    assert sdf.parse_link_zero('') == []


def test_link0_sign_only():
    assert sdf.parse_link_zero('%') == []


def test_link0_one_command():
    assert sdf.parse_link_zero('%nosave') == ["%nosave\n"]


def test_link0_one_command_no_sign():
    assert sdf.parse_link_zero('nosave') == ["%nosave\n"]


def test_link0_two_commansds():
    assert sdf.parse_link_zero('%nosave %bla=7') == ["%nosave\n", "%bla=7\n"]


def test_link0_two_commands_no_sign():
    assert sdf.parse_link_zero('nosave %bla=7') == ["%nosave\n", "%bla=7\n"]


def test_write(tmp_path):
    gjffile = tmp_path.with_name("some.gjf")
    sdf.save_molecule(
        dest=gjffile,
        coords=(("O", 1, 2, 3), ("O", 4, 2, 3)),
        route="opt freq bla/foo",
        comment="No info",
    )
    expected = """# opt freq bla/foo

No info

0 1
 O   1.0000000  2.0000000  3.0000000
 O   4.0000000  2.0000000  3.0000000


"""
    with gjffile.open() as file:
        assert file.read() == expected


def test_write_link0(tmp_path):
    gjffile = tmp_path.with_name("some.gjf")
    sdf.save_molecule(
        dest=gjffile,
        coords=(("O", 1, 2, 3), ("O", 4, 2, 3)),
        route="opt freq bla/foo",
        comment="No info",
        linkzero=["%mem=10GB\n", "%nosave\n"]
    )
    expected = """%mem=10GB
%nosave
# opt freq bla/foo

No info

0 1
 O   1.0000000  2.0000000  3.0000000
 O   4.0000000  2.0000000  3.0000000


"""
    with gjffile.open() as file:
        assert file.read() == expected


def test_write_chk(tmp_path):
    gjffile = tmp_path.with_name("some.gjf")
    sdf.save_molecule(
        dest=gjffile,
        coords=(("O", 1, 2, 3), ("O", 4, 2, 3)),
        route="opt freq bla/foo",
        comment="No info",
        chk_path=PurePosixPath("somewhere/over/therainbow"),
    )
    expected = """%chk=somewhere/over/therainbow/some.chk
# opt freq bla/foo

No info

0 1
 O   1.0000000  2.0000000  3.0000000
 O   4.0000000  2.0000000  3.0000000


"""
    with gjffile.open() as file:
        assert file.read() == expected
