import pytest
from avs_utils import rgb_ansi


def test_rgb_ansi_starts_with_escape_character():
    result = rgb_ansi(255, 0, 0)
    assert result.startswith("\x1b")


def test_rgb_ansi_correct_format_for_red():
    assert rgb_ansi(255, 0, 0) == "\033[38;2;255;0;0m"


def test_rgb_ansi_correct_format_for_custom_color():
    assert rgb_ansi(128, 64, 32) == "\033[38;2;128;64;32m"
