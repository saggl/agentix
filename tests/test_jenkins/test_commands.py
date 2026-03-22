"""Tests for Jenkins CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_jenkins_client():
    with patch("agentix.jenkins.commands.resolve_auth") as mock_auth, \
         patch("agentix.jenkins.commands.JenkinsClient") as mock_cls:
        mock_auth.return_value = MagicMock(
            base_url="https://jenkins.example.com",
            user="testuser",
            token="test-token",
            auth_type="basic",
        )
        client = MagicMock()
        mock_cls.return_value = client
        yield client


def test_jenkins_job_list(runner, mock_jenkins_client):
    mock_jenkins_client.get_jobs.return_value = [
        {"name": "job1", "url": "https://jenkins.example.com/job/job1/", "color": "blue"},
        {"name": "job2", "url": "https://jenkins.example.com/job/job2/", "color": "red"},
    ]

    result = runner.invoke(cli, ["jenkins", "job", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["name"] == "job1"


def test_jenkins_job_list_in_folder(runner, mock_jenkins_client):
    mock_jenkins_client.get_jobs.return_value = [
        {"name": "nested-job", "url": "https://...", "color": "blue"},
    ]

    result = runner.invoke(cli, ["jenkins", "job", "list", "--folder", "folder1"])
    assert result.exit_code == 0
    mock_jenkins_client.get_jobs.assert_called_once_with(folder="folder1")


def test_jenkins_job_get(runner, mock_jenkins_client):
    mock_jenkins_client.get_job.return_value = {
        "name": "my-pipeline",
        "url": "https://jenkins.example.com/job/my-pipeline/",
        "buildable": True,
        "color": "blue",
        "lastBuild": {"number": 123, "result": "SUCCESS"},
    }

    result = runner.invoke(cli, ["jenkins", "job", "get", "my-pipeline"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "my-pipeline"


def test_jenkins_job_enable(runner, mock_jenkins_client):
    result = runner.invoke(cli, ["jenkins", "job", "enable", "my-job"])
    assert result.exit_code == 0
    mock_jenkins_client.enable_job.assert_called_once_with("my-job")
    data = json.loads(result.output)
    assert data["success"] is True


def test_jenkins_job_disable(runner, mock_jenkins_client):
    result = runner.invoke(cli, ["jenkins", "job", "disable", "my-job"])
    assert result.exit_code == 0
    mock_jenkins_client.disable_job.assert_called_once_with("my-job")
    data = json.loads(result.output)
    assert data["success"] is True


def test_jenkins_build_trigger_no_params(runner, mock_jenkins_client):
    mock_jenkins_client.trigger_build.return_value = 42

    result = runner.invoke(cli, ["jenkins", "build", "trigger", "my-job"])
    assert result.exit_code == 0
    mock_jenkins_client.trigger_build.assert_called_once_with("my-job", params=None)
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["queue_id"] == 42


def test_jenkins_build_trigger_with_params(runner, mock_jenkins_client):
    mock_jenkins_client.trigger_build.return_value = 99

    result = runner.invoke(
        cli,
        [
            "jenkins",
            "build",
            "trigger",
            "my-job",
            "-P",
            "ENVIRONMENT=staging",
            "-P",
            "VERSION=1.2.3",
        ],
    )
    assert result.exit_code == 0
    # Verify params were passed correctly
    call_args = mock_jenkins_client.trigger_build.call_args
    assert call_args[0][0] == "my-job"
    assert call_args[1]["params"]["ENVIRONMENT"] == "staging"
    assert call_args[1]["params"]["VERSION"] == "1.2.3"


def test_jenkins_build_status(runner, mock_jenkins_client):
    mock_jenkins_client.get_build.return_value = {
        "number": 123,
        "result": "SUCCESS",
        "building": False,
        "duration": 60000,
        "timestamp": 1700000000000,
        "url": "https://jenkins.example.com/job/my-job/123/",
    }

    result = runner.invoke(cli, ["jenkins", "build", "status", "my-job"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["number"] == 123
    assert data["result"] == "SUCCESS"


def test_jenkins_build_status_specific_number(runner, mock_jenkins_client):
    mock_jenkins_client.get_build.return_value = {
        "number": 100,
        "result": "FAILURE",
        "building": False,
    }

    result = runner.invoke(cli, ["jenkins", "build", "status", "my-job", "--build-number", "100"])
    assert result.exit_code == 0
    mock_jenkins_client.get_build.assert_called_once_with("my-job", 100)


def test_jenkins_build_log(runner, mock_jenkins_client):
    mock_jenkins_client.get_build_log.return_value = "Build started\nRunning tests\nBuild complete\n"

    result = runner.invoke(cli, ["jenkins", "build", "log", "my-job"])
    assert result.exit_code == 0
    assert "Build started" in result.output
    assert "Build complete" in result.output


def test_jenkins_build_log_tail(runner, mock_jenkins_client):
    mock_jenkins_client.get_build_log.return_value = "Line 96\nLine 97\nLine 98\nLine 99\nLine 100\n"

    result = runner.invoke(cli, ["jenkins", "build", "log", "my-job", "--tail", "5"])
    assert result.exit_code == 0
    mock_jenkins_client.get_build_log.assert_called_once_with("my-job", None, tail=5)


def test_jenkins_build_list(runner, mock_jenkins_client):
    mock_jenkins_client.get_builds.return_value = [
        {"number": 10, "result": "SUCCESS", "timestamp": 1700000000000},
        {"number": 9, "result": "FAILURE", "timestamp": 1699990000000},
    ]

    result = runner.invoke(cli, ["jenkins", "build", "list", "my-job"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_jenkins_build_abort(runner, mock_jenkins_client):
    result = runner.invoke(cli, ["jenkins", "build", "abort", "my-job", "123"])
    assert result.exit_code == 0
    mock_jenkins_client.abort_build.assert_called_once_with("my-job", 123)


def test_jenkins_pipeline_stages(runner, mock_jenkins_client):
    mock_jenkins_client.get_pipeline_stages.return_value = [
        {"id": "1", "name": "Build", "status": "SUCCESS", "durationMillis": 30000},
        {"id": "2", "name": "Test", "status": "SUCCESS", "durationMillis": 120000},
        {"id": "3", "name": "Deploy", "status": "FAILED", "durationMillis": 5000},
    ]

    result = runner.invoke(cli, ["jenkins", "pipeline", "stages", "my-pipeline"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 3
    assert data[0]["name"] == "Build"


def test_jenkins_pipeline_log(runner, mock_jenkins_client):
    mock_jenkins_client.get_stage_log.return_value = "Stage log output here\n"

    result = runner.invoke(
        cli,
        ["jenkins", "pipeline", "log", "my-pipeline", "--stage", "stage-123"],
    )
    assert result.exit_code == 0
    assert "Stage log output" in result.output


def test_jenkins_queue_list(runner, mock_jenkins_client):
    mock_jenkins_client.get_queue.return_value = [
        {"id": 100, "task": {"name": "job1"}, "why": "Waiting for executor"},
        {"id": 101, "task": {"name": "job2"}, "why": "In queue"},
    ]

    result = runner.invoke(cli, ["jenkins", "queue", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_jenkins_queue_cancel(runner, mock_jenkins_client):
    result = runner.invoke(cli, ["jenkins", "queue", "cancel", "100"])
    assert result.exit_code == 0
    mock_jenkins_client.cancel_queue_item.assert_called_once_with(100)


def test_jenkins_node_list(runner, mock_jenkins_client):
    mock_jenkins_client.get_nodes.return_value = [
        {"displayName": "built-in", "offline": False, "idle": True, "numExecutors": 2},
        {"displayName": "agent-1", "offline": False, "idle": False, "numExecutors": 4},
    ]

    result = runner.invoke(cli, ["jenkins", "node", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_jenkins_node_get(runner, mock_jenkins_client):
    mock_jenkins_client.get_node.return_value = {
        "displayName": "agent-1",
        "offline": False,
        "idle": False,
        "numExecutors": 4,
        "monitorData": {},
    }

    result = runner.invoke(cli, ["jenkins", "node", "get", "agent-1"])
    assert result.exit_code == 0
    # Node get normalizes to use "name" instead of "displayName"
    data = json.loads(result.output)
    assert data.get("name") == "agent-1"


def test_jenkins_table_format(runner, mock_jenkins_client):
    mock_jenkins_client.get_jobs.return_value = [
        {"name": "job1", "url": "https://...", "color": "blue"},
    ]

    result = runner.invoke(cli, ["--format", "table", "jenkins", "job", "list"])
    assert result.exit_code == 0
    # Table format should contain headers
    assert "name" in result.output or "Name" in result.output
