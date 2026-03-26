"""Unit tests for Jira client method mixins."""

from pathlib import Path

from agentix.jira.client_methods import JiraMethods


class _Resp:
    def __init__(self, text="", content=b"", json_data=None):
        self.text = text
        self.content = content
        self._json_data = json_data

    def raise_for_status(self):
        return None

    def json(self):
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data


class _HTTP:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(("get", path, params))
        if path.endswith("/transitions"):
            return {"transitions": [{"id": "11", "name": "Done"}]}
        if path.endswith("/comment"):
            return {"comments": [{"id": "1"}]}
        if path.endswith("/editmeta"):
            return {"fields": {"summary": {}}}
        if path.endswith("/createmeta"):
            return {"projects": []}
        if path.endswith("/project"):
            return [{"key": "PROJ"}]
        if "/project/PROJ" in path:
            if path.endswith("/components"):
                return [{"id": "10"}]
            if path.endswith("/versions"):
                return [{"id": "20"}]
            return {"key": "PROJ"}
        if path.endswith("/attachment/42"):
            return {"content": "https://example.test/file.bin"}
        return {"fields": {"attachment": [{"id": "att-1"}]}}

    def post(self, path, json=None, files=None, headers=None, params=None):
        self.calls.append(("post", path, json, files, headers, params))
        if path.endswith("/search"):
            start = (json or {}).get("startAt", 0)
            if start == 0:
                return {"issues": [{"id": "1"}, {"id": "2"}], "total": 3}
            return {"issues": [{"id": "3"}], "total": 3}
        return {"ok": True, "path": path, "json": json}

    def put(self, path, json=None):
        self.calls.append(("put", path, json))
        return {"ok": True}

    def delete(self, path, json=None, params=None):
        self.calls.append(("delete", path, json, params))
        return None

    def get_raw(self, url):
        self.calls.append(("get_raw", url))
        if url.endswith("file.bin"):
            return _Resp(content=b"abc")
        return _Resp(text="line1\nline2\nline3")

    def paginate(self, path, **kwargs):
        self.calls.append(("paginate", path, kwargs))
        if "sprint" in path and path.endswith("/issue"):
            return iter([{"id": "i-1"}, {"id": "i-2"}])
        if path.endswith("/board"):
            return iter([{"id": 1}])
        if path.endswith("/sprint"):
            return iter([{"id": 2}, {"id": 3}])
        return iter([])


class _Client(JiraMethods):
    def __init__(self, cloud=True):
        self.http = _HTTP()
        self._api = "/rest/api/3"
        self._agile = "/rest/agile/1.0"
        self._is_cloud = cloud


def test_text_field_cloud_and_server_modes():
    assert isinstance(_Client(cloud=True)._text_field("hi"), dict)
    assert _Client(cloud=False)._text_field("hi") == "hi"


def test_search_all_and_basic_issue_calls():
    c = _Client()
    issues = list(c.search_issues_all("project = PROJ", max_results=2))
    assert len(issues) == 2

    c.get_issue("PROJ-1", fields=["summary"])
    c.update_issue("PROJ-1", {"summary": "x"})
    c.delete_issue("PROJ-1")
    c.assign_issue("PROJ-1", "acc-1")

    methods = [x[0] for x in c.http.calls]
    assert "get" in methods and "put" in methods and "delete" in methods


def test_issue_create_transition_and_comments():
    c = _Client()

    c.create_issue("PROJ", "s", "Task", description="d", assignee="a", priority="P1", labels=["x"])
    transitions = c.get_transitions("PROJ-1")
    c.transition_issue("PROJ-1", "11", comment="done")
    comments = c.get_comments("PROJ-1")
    c.add_comment("PROJ-1", "hello")
    c.get_comment("PROJ-1", "1")

    assert transitions[0]["name"] == "Done"
    assert comments[0]["id"] == "1"


def test_attachments_and_metadata(tmp_path: Path):
    c = _Client()

    p = tmp_path / "a.txt"
    p.write_text("x", encoding="utf-8")

    c.get_attachments("PROJ-1")
    c.add_attachment("PROJ-1", str(p))
    content = c.get_attachment_content("42")

    assert content == b"abc"
    assert c.get_issue_edit_metadata("PROJ-1")["fields"]
    assert c.get_create_metadata(project_keys=["PROJ"], issue_type_names=["Task"]) is not None


def test_agile_epics_projects_components_versions_helpers():
    c = _Client()

    assert c.get_boards("PROJ")
    assert c.get_board(1) is not None
    assert c.get_sprints(1)
    assert c.get_sprint(2) is not None
    assert c.get_sprint_issues(2, max_results=1)
    assert c.get_active_sprint(1)

    assert isinstance(c.get_epics("PROJ"), list)
    assert isinstance(c.get_epic_issues("PROJ-EPIC", max_results=1), list)

    assert c.get_projects()
    assert c.get_project("PROJ")
    assert c.get_project_components("PROJ")
    c.create_component("PROJ", "Backend", description="d", lead_account_id="u1")
    c.update_component("10", name="Backend2", description="", lead_account_id="u2")
    c.delete_component("10")

    assert c.get_project_versions("PROJ")
    c.create_version("PROJ", "v1", description="d", start_date="2026-01-01", release_date="2026-02-01")
    c.update_version("20", name="v2", released=True, archived=False, release_date="2026-03-01")
    c.archive_version("20")
    c.delete_version("20")
