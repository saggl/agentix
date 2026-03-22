"""Tests for Jenkins client."""

import pytest
import responses

from agentix.jenkins.client import JenkinsClient


@pytest.fixture
def jenkins():
    return JenkinsClient(
        base_url="https://jenkins.example.com",
        username="testuser",
        api_token="test-token",
    )


@pytest.fixture
def jenkins_bearer():
    return JenkinsClient(
        base_url="https://jenkins.example.com",
        username="testuser",
        api_token="bearer-token",
        auth_type="bearer",
    )


@responses.activate
def test_get_jobs(jenkins):
    """Test getting list of jobs."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/api/json",
        json={
            "jobs": [
                {"name": "job1", "url": "https://jenkins.example.com/job/job1/", "color": "blue"},
                {"name": "job2", "url": "https://jenkins.example.com/job/job2/", "color": "red"},
            ]
        },
        status=200,
    )
    jobs = jenkins.get_jobs()
    assert len(jobs) == 2
    assert jobs[0]["name"] == "job1"


@responses.activate
def test_get_jobs_in_folder(jenkins):
    """Test getting jobs in a folder."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/folder1/api/json",
        json={
            "jobs": [
                {"name": "nested-job", "url": "https://...", "color": "blue"},
            ]
        },
        status=200,
    )
    jobs = jenkins.get_jobs(folder="folder1")
    assert len(jobs) == 1
    assert jobs[0]["name"] == "nested-job"


@responses.activate
def test_get_job(jenkins):
    """Test getting single job details."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-pipeline/api/json",
        json={
            "name": "my-pipeline",
            "url": "https://jenkins.example.com/job/my-pipeline/",
            "buildable": True,
            "color": "blue",
        },
        status=200,
    )
    job = jenkins.get_job("my-pipeline")
    assert job["name"] == "my-pipeline"
    assert job["buildable"] is True


@responses.activate
def test_get_crumb(jenkins):
    """Test CSRF crumb fetching."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/crumbIssuer/api/json",
        json={
            "crumbRequestField": "Jenkins-Crumb",
            "crumb": "abc123def456",
        },
        status=200,
    )
    crumb = jenkins._get_crumb()
    assert crumb == {"Jenkins-Crumb": "abc123def456"}

    # Test caching - should not make another request
    crumb2 = jenkins._get_crumb()
    assert crumb2 == crumb
    assert len(responses.calls) == 1  # Only one HTTP call


@responses.activate
def test_get_crumb_failure(jenkins):
    """Test crumb handling when endpoint fails."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/crumbIssuer/api/json",
        status=404,
    )
    crumb = jenkins._get_crumb()
    assert crumb == {}  # Returns empty dict on failure


@responses.activate
def test_trigger_build_no_params(jenkins):
    """Test triggering a build without parameters."""
    # Mock crumb
    responses.add(
        responses.GET,
        "https://jenkins.example.com/crumbIssuer/api/json",
        json={"crumbRequestField": "Jenkins-Crumb", "crumb": "test123"},
        status=200,
    )
    # Mock build trigger
    responses.add(
        responses.POST,
        "https://jenkins.example.com/job/my-job/build",
        headers={"Location": "https://jenkins.example.com/queue/item/42/"},
        status=201,
    )

    queue_id = jenkins.trigger_build("my-job")
    assert queue_id == 42


@responses.activate
def test_trigger_build_with_params(jenkins):
    """Test triggering a parameterized build."""
    # Mock crumb
    responses.add(
        responses.GET,
        "https://jenkins.example.com/crumbIssuer/api/json",
        json={"crumbRequestField": "Jenkins-Crumb", "crumb": "test123"},
        status=200,
    )
    # Mock build trigger
    responses.add(
        responses.POST,
        "https://jenkins.example.com/job/my-job/buildWithParameters",
        headers={"Location": "https://jenkins.example.com/queue/item/99/"},
        status=201,
    )

    queue_id = jenkins.trigger_build("my-job", params={"ENVIRONMENT": "staging", "VERSION": "1.2.3"})
    assert queue_id == 99


@responses.activate
def test_get_build(jenkins):
    """Test getting build details."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-job/123/api/json",
        json={
            "number": 123,
            "result": "SUCCESS",
            "building": False,
            "duration": 60000,
            "timestamp": 1700000000000,
        },
        status=200,
    )
    build = jenkins.get_build("my-job", 123)
    assert build["number"] == 123
    assert build["result"] == "SUCCESS"
    assert build["building"] is False


@responses.activate
def test_get_build_last(jenkins):
    """Test getting last build."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-job/lastBuild/api/json",
        json={
            "number": 456,
            "result": "FAILURE",
            "building": False,
        },
        status=200,
    )
    build = jenkins.get_build("my-job")
    assert build["number"] == 456
    assert build["result"] == "FAILURE"


@responses.activate
def test_get_builds(jenkins):
    """Test getting build list."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-job/api/json",
        json={
            "builds": [
                {"number": 10, "result": "SUCCESS", "timestamp": 1700000000000},
                {"number": 9, "result": "FAILURE", "timestamp": 1699990000000},
                {"number": 8, "result": "SUCCESS", "timestamp": 1699980000000},
            ]
        },
        status=200,
    )
    builds = jenkins.get_builds("my-job", max_results=10)
    assert len(builds) == 3
    assert builds[0]["number"] == 10


@responses.activate
def test_get_build_log(jenkins):
    """Test getting build console log."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-job/123/consoleText",
        body="Build started\nRunning tests\nBuild complete\n",
        status=200,
    )
    log = jenkins.get_build_log("my-job", 123)
    assert "Build started" in log
    assert "Build complete" in log


@responses.activate
def test_get_build_log_tail(jenkins):
    """Test getting last N lines of build log."""
    full_log = "\n".join([f"Line {i}" for i in range(1, 101)])
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-job/lastBuild/consoleText",
        body=full_log,
        status=200,
    )
    log = jenkins.get_build_log("my-job", tail=5)
    lines = log.splitlines()
    assert len(lines) == 5
    assert lines[-1] == "Line 100"


@responses.activate
def test_get_pipeline_stages(jenkins):
    """Test getting pipeline stages."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-pipeline/123/wfapi/describe",
        json={
            "stages": [
                {"id": "1", "name": "Build", "status": "SUCCESS", "durationMillis": 30000},
                {"id": "2", "name": "Test", "status": "SUCCESS", "durationMillis": 120000},
                {"id": "3", "name": "Deploy", "status": "FAILED", "durationMillis": 5000},
            ]
        },
        status=200,
    )
    stages = jenkins.get_pipeline_stages("my-pipeline", 123)
    assert len(stages) == 3
    assert stages[0]["name"] == "Build"
    assert stages[2]["status"] == "FAILED"


@responses.activate
def test_get_stage_log(jenkins):
    """Test getting stage-specific log."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/job/my-pipeline/123/execution/node/5/wfapi/log",
        json={"text": "Stage log content here\nMore log lines\n"},
        status=200,
    )
    log = jenkins.get_stage_log("my-pipeline", "5", 123)
    assert "Stage log content" in log


@responses.activate
def test_get_queue(jenkins):
    """Test getting build queue."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/queue/api/json",
        json={
            "items": [
                {"id": 100, "task": {"name": "job1"}, "why": "Waiting for executor"},
                {"id": 101, "task": {"name": "job2"}, "why": "In queue"},
            ]
        },
        status=200,
    )
    queue = jenkins.get_queue()
    assert len(queue) == 2
    assert queue[0]["id"] == 100


@responses.activate
def test_enable_job(jenkins):
    """Test enabling a job."""
    # Mock crumb
    responses.add(
        responses.GET,
        "https://jenkins.example.com/crumbIssuer/api/json",
        json={"crumbRequestField": "Jenkins-Crumb", "crumb": "test123"},
        status=200,
    )
    # Mock enable
    responses.add(
        responses.POST,
        "https://jenkins.example.com/job/my-job/enable",
        status=200,
    )
    jenkins.enable_job("my-job")
    assert len([c for c in responses.calls if "enable" in c.request.url]) == 1


@responses.activate
def test_disable_job(jenkins):
    """Test disabling a job."""
    # Mock crumb
    responses.add(
        responses.GET,
        "https://jenkins.example.com/crumbIssuer/api/json",
        json={"crumbRequestField": "Jenkins-Crumb", "crumb": "test123"},
        status=200,
    )
    # Mock disable
    responses.add(
        responses.POST,
        "https://jenkins.example.com/job/my-job/disable",
        status=200,
    )
    jenkins.disable_job("my-job")
    assert len([c for c in responses.calls if "disable" in c.request.url]) == 1


@responses.activate
def test_job_path_with_folders(jenkins):
    """Test job path conversion with folders."""
    path = jenkins._job_path("folder1/folder2/my-job")
    assert path == "job/folder1/job/folder2/job/my-job"


@responses.activate
def test_get_nodes(jenkins):
    """Test getting node list."""
    responses.add(
        responses.GET,
        "https://jenkins.example.com/computer/api/json",
        json={
            "computer": [
                {"displayName": "built-in", "offline": False, "idle": True, "numExecutors": 2},
                {"displayName": "agent-1", "offline": False, "idle": False, "numExecutors": 4},
            ]
        },
        status=200,
    )
    nodes = jenkins.get_nodes()
    assert len(nodes) == 2
    assert nodes[0]["displayName"] == "built-in"


@responses.activate
def test_bearer_auth_initialization(jenkins_bearer):
    """Test that bearer auth client can make requests."""
    # Just verify it initializes without error and can make a request
    responses.add(
        responses.GET,
        "https://jenkins.example.com/api/json",
        json={"jobs": []},
        status=200,
    )
    jobs = jenkins_bearer.get_jobs()
    assert jobs == []
