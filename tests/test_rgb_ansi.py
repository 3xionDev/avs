import pytest
from avs_utils import rgb_ansi


def test_rgb_ansi_starts_with_escape_character() -> None:
    result = rgb_ansi(255, 0, 0)
    assert result.startswith("\x1b")


def test_rgb_ansi_correct_format_for_red() -> None:
    assert rgb_ansi(255, 0, 0) == "\033[38;2;255;0;0m"


def test_rgb_ansi_correct_format_for_custom_color() -> None:
    assert rgb_ansi(128, 64, 32) == "\033[38;2;128;64;32m"
