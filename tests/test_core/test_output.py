"""Tests for output formatting."""

import json

from agentix.core.exceptions import AgentixError, NotFoundError
from agentix.core.output import OutputFormatter


def test_json_output_dict(capsys):
    fmt = OutputFormatter("json")
    fmt.output({"key": "PROJ-1", "summary": "Test"})
    out = json.loads(capsys.readouterr().out)
    assert out["key"] == "PROJ-1"
    assert out["summary"] == "Test"


def test_json_output_list(capsys):
    fmt = OutputFormatter("json")
    fmt.output([{"a": 1}, {"a": 2}])
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 2
    assert out[0]["a"] == 1


def test_table_output_dict(capsys):
    fmt = OutputFormatter("table")
    fmt.output({"key": "PROJ-1", "status": "Open"})
    out = capsys.readouterr().out
    assert "PROJ-1" in out
    assert "Open" in out


def test_table_output_list(capsys):
    fmt = OutputFormatter("table")
    fmt.output([{"key": "A", "val": 1}, {"key": "B", "val": 2}])
    out = capsys.readouterr().out
    assert "A" in out
    assert "B" in out


def test_table_empty_list(capsys):
    fmt = OutputFormatter("table")
    fmt.output([])
    assert "No results" in capsys.readouterr().out


def test_json_error(capsys):
    fmt = OutputFormatter("json")
    err = NotFoundError("Issue not found", status_code=404)
    fmt.error(err)
    out = json.loads(capsys.readouterr().out)
    assert out["error"] is True
    assert out["error_type"] == "NotFoundError"


def test_table_error(capsys):
    fmt = OutputFormatter("table")
    err = AgentixError("bad thing")
    fmt.error(err)
    assert "bad thing" in capsys.readouterr().err


def test_json_success(capsys):
    fmt = OutputFormatter("json")
    fmt.success("Done", data={"id": 42})
    out = json.loads(capsys.readouterr().out)
    assert out["success"] is True
    assert out["data"]["id"] == 42


def test_table_success(capsys):
    fmt = OutputFormatter("table")
    fmt.success("All good")
    assert "All good" in capsys.readouterr().out
