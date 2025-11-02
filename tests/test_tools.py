import pytest

from opspilot.tools import ToolError, calculator, run_tool

"""pytest picks this up automatically. Turns off fake latency in tests."""

import opspilot.tools as tools

tools.FAKE_LATENCY_S = 0.0

def test_basic_math():
    assert calculator("(2400 * 18.5) / 100") == "444.0"


def test_blocks_code_execution():
    with pytest.raises(ToolError):
        calculator("__import__('os').system('echo hacked')")


def test_blocks_variables():
    with pytest.raises(ToolError):
        calculator("x + 1")


def test_divide_by_zero_is_readable():
    with pytest.raises(ToolError, match="division by zero"):
        calculator("1 / 0")


def test_weather_converts_to_fahrenheit():
    assert run_tool("get_weather", {"city": "Paris", "unit": "fahrenheit"})[0].startswith("57.2")


def test_unknown_city_lists_known_ones():
    text, is_error = run_tool("get_weather", {"city": "Atlantis"})
    assert is_error is True
    assert "Known cities" in text


def test_unknown_tool_does_not_crash():
    text, is_error = run_tool("delete_everything", {})
    assert is_error is True
    assert "no tool named" in text


def test_made_up_argument_is_readable():
    text, is_error = run_tool("get_weather", {"citee": "Paris"})
    assert is_error is True
    assert "bad arguments" in text


def test_cannot_escape_the_workspace():
    text, is_error = run_tool("read_file", {"name": "../.env"})
    assert is_error is True
    assert "outside the workspace" in text


def test_cannot_use_an_absolute_path():
    text, is_error = run_tool("read_file", {"name": "/etc/passwd"})
    assert is_error is True
    assert "outside the workspace" in text


def test_can_read_a_normal_file():
    run_tool("write_file", {"name": "fixture.txt", "content": "Server 1200."})
    text, is_error = run_tool("read_file", {"name": "fixture.txt"})
    assert is_error is False
    assert "Server 1200" in text


def test_write_then_read_back():
    run_tool("write_file", {"name": "tmp_test.txt", "content": "hello"})
    text, is_error = run_tool("read_file", {"name": "tmp_test.txt"})
    assert is_error is False
    assert text == "hello"


def test_cannot_write_outside_the_workspace():
    text, is_error = run_tool("write_file", {"name": "../stolen.txt", "content": "x"})
    assert is_error is True
    assert "outside the workspace" in text