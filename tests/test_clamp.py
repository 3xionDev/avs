import pytest
from avs_utils import clamp


def test_clamp_value_within_range():
    assert clamp(5, 1, 10) == 5


def test_clamp_value_below_min():
    assert clamp(0, 1, 10) == 1


def test_clamp_value_above_max():
    assert clamp(11, 1, 10) == 10
