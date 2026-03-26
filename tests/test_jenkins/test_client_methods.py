"""Unit tests for Jenkins client method mixins."""

from pathlib import Path

from agentix.jenkins.client_methods import JenkinsMethods


class _Resp:
    def __init__(self, text="", content=b"", json_data=None):
        self.text = text
        self.content = content
        self._json_data = json_data
        self.headers = {}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=8192):
        data = self.content or b""
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]


class _Session:
    def __init__(self):
        self.posts = []

    def post(self, url, data=None, headers=None, timeout=None, allow_redirects=False):
        self.posts.append((url, data, headers, timeout, allow_redirects))
        r = _Resp()
        if "buildWithParameters" in url:
            r.headers = {"Location": "https://jenkins/queue/item/42/"}
        else:
            r.headers = {"Location": "https://jenkins/no-queue/"}
        return r


class _HTTP:
    def __init__(self):
        self.calls = []
        self.timeout = 5
        self.session = _Session()

    def _url(self, p):
        return f"https://jenkins{p}"

    def get(self, path, params=None):
        self.calls.append(("get", path, params))
        if path == "/api/json" or (
            path.endswith("/api/json")
            and isinstance(params, dict)
            and str(params.get("tree", "")).startswith("jobs[")
        ):
            return {"jobs": [{"name": "x"}]}
        if path.startswith("/queue/item/") and path.endswith("/api/json"):
            return {"executable": {"number": 7}}
        if "testReport" in path:
            return {
                "suites": [
                    {"name": "smoke-suite", "cases": [{"status": "FAILED", "name": "a"}, {"status": "PASSED"}]},
                    {"name": "other", "cases": [{"status": "REGRESSION", "name": "b"}]},
                ]
            }
        if path.endswith("/api/json") and "/job/" in path:
            if "lastBuild" in path:
                return {
                    "building": False,
                    "result": "SUCCESS",
                    "changeSets": [{"items": [{"commitId": "abc"}]}],
                    "artifacts": [],
                }
            return {
                "lastSuccessfulBuild": {"number": 3},
                "lastFailedBuild": {"number": 4},
                "building": False,
                "changeSets": [{"items": [{"commitId": "abc"}]}],
                "artifacts": [{"fileName": "a.txt"}],
            }
        if path.endswith("/wfapi/describe") and "/execution/node/" in path:
            return {"stageFlowNodes": [{"id": "child-1"}]}
        if "wfapi/describe" in path:
            return {"stages": [{"id": "s1"}]}
        if path.endswith("/wfapi/log"):
            if "/node/stage-1/" in path:
                return {"text": ""}
            return {"text": "child-log"}
        if path == "/queue/api/json":
            return {"items": [{"id": 1}]}
        if path == "/computer/api/json":
            return {"computer": [{"displayName": "built-in"}]}
        if "/computer/" in path:
            return {"displayName": "built-in"}
        return {}

    def post(self, path, headers=None, **kwargs):
        self.calls.append(("post", path, headers, kwargs))
        return {"ok": True}

    def get_raw(self, url, **kwargs):
        self.calls.append(("get_raw", url, kwargs))
        if url.endswith("config.xml"):
            return _Resp(text="<xml/>")
        if "artifact" in url:
            return _Resp(content=b"artifact")
        return _Resp(text="line1\nline2\nline3")


class _Client(JenkinsMethods):
    def __init__(self):
        self.http = _HTTP()

    def _job_path(self, job_name: str) -> str:
        return f"/job/{job_name}"

    def _get_crumb(self):
        return {"Jenkins-Crumb": "abc"}

    def _post_with_crumb(self, path, **kwargs):
        return self.http.post(path, headers=self._get_crumb(), **kwargs)


def test_jobs_builds_and_queue_helpers(tmp_path: Path):
    c = _Client()

    assert c.get_jobs()
    assert c.get_jobs("folder/sub")
    assert c.get_job("pipe")
    assert c.get_job_config("pipe") == "<xml/>"
    c.enable_job("pipe")
    c.disable_job("pipe")

    assert c.trigger_build("pipe", params={"A": "1"}) == 42
    assert c.trigger_build("pipe") is None

    assert c.get_build("pipe")
    assert c.get_build("pipe", 1)
    assert c.get_build_log("pipe", tail=2) == "line2\nline3"
    assert c.get_builds("pipe", max_results=3) is not None

    c.abort_build("pipe", 1)
    assert c.get_latest_build_by_result("pipe", "success")
    assert c.get_latest_build_by_result("pipe", "failure")
    assert c.get_latest_build_by_result("pipe", "unknown") is None

    assert c.wait_for_build_result("pipe", timeout=1, poll_interval=0)["result"] == "SUCCESS"
    assert c.wait_for_build("pipe", queue_id=42, timeout=1, poll_interval=0)

    assert c.get_build_artifacts("pipe") == []
    assert c.download_artifact("pipe", "a.txt") == b"artifact"

    out = tmp_path / "artifact.bin"
    c.download_artifact_to_file("pipe", "a.txt", str(out), chunk_size=3)
    assert out.read_bytes() == b"artifact"

    assert c.get_queue()
    c.cancel_queue_item(1)


def test_tests_changes_pipeline_and_nodes_helpers():
    c = _Client()

    assert c.get_test_results("pipe")
    failures = c.get_test_failures("pipe", suite_filter="smoke", limit=1)
    assert len(failures) == 1

    assert c.get_build_changes("pipe") == [{"commitId": "abc"}]
    assert c.get_pipeline_stages("pipe") == [{"id": "s1"}]
    assert c.get_stage_log("pipe", "stage-1") == "child-log"

    assert c.get_nodes()
    assert c.get_node("master")["displayName"] == "built-in"
