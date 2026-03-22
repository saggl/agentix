"""Tests for Jenkins model normalization functions."""

from agentix.jenkins.models import (
    normalize_build,
    normalize_build_brief,
    normalize_job,
    normalize_job_detail,
    normalize_node,
    normalize_queue_item,
    normalize_stage,
    normalize_test_case,
    normalize_test_result,
)


def test_normalize_job():
    """Test normalizing job."""
    job = {
        "name": "my-pipeline",
        "url": "https://jenkins.example.com/job/my-pipeline/",
        "color": "blue",
        "buildable": True,
    }
    result = normalize_job(job)
    assert result["name"] == "my-pipeline"
    assert result["url"] == "https://jenkins.example.com/job/my-pipeline/"
    assert result["color"] == "blue"
    assert result["buildable"] is True


def test_normalize_job_with_display_name():
    """Test normalizing job with displayName instead of name."""
    job = {
        "displayName": "My Display Name",
        "url": "https://...",
        "color": "red",
    }
    result = normalize_job(job)
    assert result["name"] == "My Display Name"


def test_normalize_job_missing_fields():
    """Test normalizing job with missing fields."""
    job = {}
    result = normalize_job(job)
    assert result["name"] == ""
    assert result["url"] == ""
    assert result["buildable"] is True  # Default


def test_normalize_job_detail():
    """Test normalizing detailed job info."""
    job = {
        "name": "my-job",
        "url": "https://...",
        "color": "blue",
        "buildable": True,
        "lastBuild": {"number": 123},
        "lastSuccessfulBuild": {"number": 122},
        "lastFailedBuild": {"number": 100},
        "inQueue": False,
    }
    result = normalize_job_detail(job)
    assert result["name"] == "my-job"
    assert result["lastBuild"] == 123
    assert result["lastSuccessfulBuild"] == 122
    assert result["lastFailedBuild"] == 100
    assert result["inQueue"] is False


def test_normalize_job_detail_missing_builds():
    """Test normalizing job detail with missing build info."""
    job = {"name": "job1"}
    result = normalize_job_detail(job)
    assert result["lastBuild"] is None
    assert result["lastSuccessfulBuild"] is None


def test_normalize_build():
    """Test normalizing build."""
    build = {
        "number": 123,
        "result": "SUCCESS",
        "building": False,
        "displayName": "#123",
        "duration": 60000,
        "timestamp": 1700000000000,
        "url": "https://jenkins.example.com/job/my-job/123/",
    }
    result = normalize_build(build)
    assert result["number"] == 123
    assert result["result"] == "SUCCESS"
    assert result["building"] is False
    assert result["duration"] == 60000


def test_normalize_build_missing_fields():
    """Test normalizing build with missing fields."""
    build = {"number": 456}
    result = normalize_build(build)
    assert result["number"] == 456
    assert result["result"] == ""
    assert result["building"] is False  # Default
    assert result["duration"] == 0  # Default


def test_normalize_build_brief():
    """Test normalizing brief build representation."""
    build = {
        "number": 789,
        "result": "FAILURE",
        "displayName": "#789",
        "duration": 30000,
    }
    result = normalize_build_brief(build)
    assert result["number"] == 789
    assert result["result"] == "FAILURE"
    assert result["displayName"] == "#789"
    assert result["duration"] == 30000


def test_normalize_test_result():
    """Test normalizing test results."""
    test_result = {
        "totalCount": 100,
        "failCount": 5,
        "skipCount": 2,
        "passCount": 93,
        "duration": 120.5,
    }
    result = normalize_test_result(test_result)
    assert result["totalCount"] == 100
    assert result["failCount"] == 5
    assert result["skipCount"] == 2
    assert result["passCount"] == 93


def test_normalize_test_result_empty():
    """Test normalizing empty test results."""
    result = normalize_test_result({})
    assert result["totalCount"] == 0
    assert result["failCount"] == 0


def test_normalize_test_case():
    """Test normalizing test case."""
    case = {
        "name": "test_login",
        "className": "com.example.AuthTests",
        "status": "FAILED",
        "duration": 1.5,
        "errorDetails": "AssertionError",
        "errorStackTrace": "at line 42...",
    }
    result = normalize_test_case(case)
    assert result["name"] == "test_login"
    assert result["className"] == "com.example.AuthTests"
    assert result["status"] == "FAILED"
    assert result["errorDetails"] == "AssertionError"


def test_normalize_test_case_passed():
    """Test normalizing passing test case."""
    case = {
        "name": "test_success",
        "className": "Tests",
        "status": "PASSED",
        "duration": 0.5,
    }
    result = normalize_test_case(case)
    assert result["name"] == "test_success"
    assert result["status"] == "PASSED"
    assert result["errorDetails"] == ""  # No error


def test_normalize_stage():
    """Test normalizing pipeline stage."""
    stage = {
        "id": "5",
        "name": "Deploy",
        "status": "SUCCESS",
        "durationMillis": 45000,
    }
    result = normalize_stage(stage)
    assert result["id"] == "5"
    assert result["name"] == "Deploy"
    assert result["status"] == "SUCCESS"
    assert result["durationMillis"] == 45000


def test_normalize_stage_missing_fields():
    """Test normalizing stage with missing fields."""
    stage = {"name": "Build"}
    result = normalize_stage(stage)
    assert result["name"] == "Build"
    assert result["id"] == ""
    assert result["durationMillis"] == 0


def test_normalize_queue_item():
    """Test normalizing queue item."""
    item = {
        "id": 100,
        "task": {
            "name": "my-job",
            "url": "https://jenkins.example.com/job/my-job/",
        },
        "why": "Waiting for executor",
        "inQueueSince": 1700000000000,
    }
    result = normalize_queue_item(item)
    assert result["id"] == 100
    assert result["task"] == "my-job"
    assert result["url"] == "https://jenkins.example.com/job/my-job/"
    assert result["why"] == "Waiting for executor"


def test_normalize_queue_item_missing_task():
    """Test normalizing queue item with missing task."""
    item = {"id": 200, "why": "In queue"}
    result = normalize_queue_item(item)
    assert result["id"] == 200
    assert result["task"] == ""
    assert result["url"] == ""


def test_normalize_node():
    """Test normalizing node."""
    node = {
        "displayName": "built-in",
        "offline": False,
        "temporarilyOffline": False,
        "idle": True,
        "numExecutors": 2,
    }
    result = normalize_node(node)
    assert result["name"] == "built-in"
    assert result["offline"] is False
    assert result["idle"] is True
    assert result["numExecutors"] == 2


def test_normalize_node_missing_fields():
    """Test normalizing node with missing fields."""
    node = {"displayName": "agent-1"}
    result = normalize_node(node)
    assert result["name"] == "agent-1"
    assert result["offline"] is False  # Default
    assert result["idle"] is True  # Default
    assert result["numExecutors"] == 0  # Default
