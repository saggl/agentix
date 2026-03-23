"""Tests for CLI entrypoint error handling."""

import pytest
import click

from agentix import cli as cli_module


def test_main_handles_click_exception(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_notify_update_available", lambda: None)

    def _raise_click_exception(*_args, **_kwargs):
        raise click.ClickException("invalid option")

    monkeypatch.setattr(cli_module, "cli", _raise_click_exception)

    with pytest.raises(SystemExit) as exc:
        cli_module.main()

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "invalid option" in captured.err
