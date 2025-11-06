import pytest

from conftest import needs_postgres
from opspilot.tools import REGISTRY, ToolError, calculator, run_tool


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


@needs_postgres
def test_sql_select_works():
    text, is_error = run_tool("sql_query", {"sql": "SELECT count(*) FROM demo.signups"})
    assert is_error is False


@needs_postgres
def test_sql_cannot_delete():
    text, is_error = run_tool("sql_query", {"sql": "DELETE FROM demo.signups"})
    assert is_error is True


@needs_postgres
def test_sql_typo_gets_a_hint():
    text, is_error = run_tool("sql_query", {"sql": "SELECT signup_dt FROM demo.signups LIMIT 1"})
    assert is_error is True
    assert "signup_date" in text

def test_rejects_a_number_above_the_maximum():
    text, is_error = run_tool("search_web", {"query": "x", "limit": 500})
    assert is_error is True
    assert "limit" in text
    assert "less than or equal to 10" in text


def test_rejects_the_wrong_type():
    text, is_error = run_tool("search_web", {"query": "x", "limit": "three"})
    assert is_error is True
    assert "limit" in text
    assert "valid integer" in text


def test_rejects_an_extra_argument():
    text, is_error = run_tool("read_file", {"name": "fixture.txt", "oops": 1})
    assert is_error is True
    assert "oops" in text
    assert "not permitted" in text


def test_rejects_a_missing_argument():
    text, is_error = run_tool("calculator", {})
    assert is_error is True
    assert "expression" in text
    assert "required" in text.lower()


def test_rejects_a_value_outside_the_enum():
    text, is_error = run_tool("get_weather", {"city": "Paris", "unit": "kelvin"})
    assert is_error is True
    assert "celsius" in text


def test_rejects_an_empty_string():
    text, is_error = run_tool("sql_query", {"sql": ""})
    assert is_error is True
    assert "at least 1 character" in text


def test_fills_in_the_default():
    text, is_error = run_tool("search_web", {"query": "wal mode"})
    assert is_error is False
    assert len(text.splitlines()) == 3  # limit defaults to 3


def test_schema_sent_to_claude_carries_the_rules():
    schema = REGISTRY["search_web"]["schema"]["input_schema"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["limit"]["maximum"] == 10
    assert schema["properties"]["limit"]["minimum"] == 1
    assert schema["required"] == ["query"]
    assert "title" not in schema  # stripped, it only costs tokens
    assert "title" not in schema["properties"]["limit"]
