"""Tests for Polarion CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def _make_enum_ref(id_, name=None):
    ref = MagicMock()
    ref.id = id_
    ref.name = name
    return ref


def _make_user_ref(id_, name=None):
    ref = MagicMock()
    ref.id = id_
    ref.name = name
    return ref


def _make_page(items, total=None, offset=0, limit=100, has_more=False):
    page = MagicMock()
    page.items = items
    page.total = total if total is not None else len(items)
    page.offset = offset
    page.limit = limit
    page.has_more = has_more
    return page


def _make_project(id_, name, tracker_prefix=None):
    proj = MagicMock()
    proj.id = id_
    proj.name = name
    proj.tracker_prefix = tracker_prefix
    return proj


def _make_workitem_summary(id_, title, type_id="task", status_id="open"):
    wi = MagicMock()
    wi.id = id_
    wi.uri = f"subterra:…:{id_}"
    wi.title = title
    wi.type = _make_enum_ref(type_id)
    wi.status = _make_enum_ref(status_id)
    wi.priority = None
    return wi


def _make_workitem_detail(id_, title):
    wi = MagicMock()
    wi.id = id_
    wi.uri = f"subterra:…:{id_}"
    wi.title = title
    wi.type = _make_enum_ref("task")
    wi.status = _make_enum_ref("open")
    wi.priority = None
    wi.description_html = "<p>desc</p>"
    wi.author = _make_user_ref("admin")
    wi.assignees = []
    wi.approvers = []
    wi.links = []
    wi.attachments = []
    wi.custom_fields = {}
    wi.created_at = None
    wi.updated_at = None
    return wi


def _make_document(uri, project_id, location, name, title):
    doc = MagicMock()
    doc.uri = uri
    doc.project_id = project_id
    doc.location = location
    doc.name = name
    doc.title = title
    doc.status = None
    doc.type = None
    return doc


def _make_plan(id_, name):
    plan = MagicMock()
    plan.id = id_
    plan.uri = f"subterra:…:{id_}"
    plan.name = name
    plan.status = _make_enum_ref("open")
    plan.start_date = None
    plan.due_date = None
    return plan


def _make_testrun(id_, title, is_template=False):
    tr = MagicMock()
    tr.id = id_
    tr.uri = f"subterra:…:{id_}"
    tr.title = title
    tr.is_template = is_template
    tr.status = _make_enum_ref("not_run")
    tr.created_at = None
    return tr


def _make_test_record(test_case_id, result="passed"):
    rec = MagicMock()
    rec.test_case_id = test_case_id
    rec.result = result
    rec.duration_ms = 100
    rec.comment = None
    return rec


@pytest.fixture
def mock_polarion_client():
    with patch("agentix.polarion.commands.resolve_auth") as mock_auth, \
         patch("agentix.polarion.commands.create_polarion_client") as mock_create:
        mock_auth.return_value = MagicMock(
            base_url="https://polarion.example.com/polarion",
            user="test-user",
            token="test-token",
            auth_type="token",
        )
        client = MagicMock()
        mock_create.return_value = client
        yield client


# -- Project tests --


def test_project_list(runner, mock_polarion_client):
    projects = [_make_project("PROJ1", "Project 1"), _make_project("PROJ2", "Project 2")]
    mock_polarion_client.projects.list.return_value = _make_page(projects)

    result = runner.invoke(cli, ["polarion", "project", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == "PROJ1"


def test_project_get(runner, mock_polarion_client):
    mock_polarion_client.projects.get.return_value = _make_project("PROJ", "My Project", "MP")

    result = runner.invoke(cli, ["polarion", "project", "get", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "PROJ"
    assert data["name"] == "My Project"


def test_project_users(runner, mock_polarion_client):
    user1 = MagicMock()
    user1.id = "admin"
    user1.name = "Admin"
    user1.email = "admin@example.com"
    user2 = MagicMock()
    user2.id = "dev"
    user2.name = "Developer"
    user2.email = "dev@example.com"
    mock_polarion_client.projects.users.return_value = _make_page([user1, user2])

    result = runner.invoke(cli, ["polarion", "project", "users", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2


# -- Workitem tests --


def test_workitem_get(runner, mock_polarion_client):
    mock_polarion_client.workitems.get.return_value = _make_workitem_detail("MP-123", "Test Item")

    result = runner.invoke(cli, ["polarion", "workitem", "get", "PROJ", "MP-123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "MP-123"
    assert data["title"] == "Test Item"


def test_workitem_search(runner, mock_polarion_client):
    items = [_make_workitem_summary("MP-1", "Item 1"), _make_workitem_summary("MP-2", "Item 2")]
    mock_polarion_client.workitems.search.return_value = _make_page(items)

    result = runner.invoke(cli, ["polarion", "workitem", "search", "PROJ", "--query", "type:task"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2


def test_workitem_create(runner, mock_polarion_client):
    mock_polarion_client.workitems.create.return_value = _make_workitem_detail("MP-999", "New Item")

    result = runner.invoke(cli, [
        "polarion", "workitem", "create", "PROJ",
        "--type", "task",
        "--title", "New Item",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["id"] == "MP-999"


def test_workitem_update(runner, mock_polarion_client):
    mock_polarion_client.workitems.update.return_value = _make_workitem_detail("MP-123", "Updated Title")

    result = runner.invoke(cli, [
        "polarion", "workitem", "update", "PROJ", "MP-123",
        "--title", "Updated Title",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["title"] == "Updated Title"


def test_workitem_delete(runner, mock_polarion_client):
    mock_polarion_client.workitems.delete.return_value = None

    result = runner.invoke(cli, ["polarion", "workitem", "delete", "PROJ", "MP-123", "--yes"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_workitem_actions(runner, mock_polarion_client):
    mock_polarion_client.workitems.available_actions.return_value = ["start", "close", "reject"]

    result = runner.invoke(cli, ["polarion", "workitem", "actions", "PROJ", "MP-123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == ["start", "close", "reject"]


def test_workitem_links(runner, mock_polarion_client):
    link = MagicMock()
    link.role = "parent"
    link.target_id = "MP-100"
    link.target_uri = "subterra:…"
    mock_polarion_client.workitems.links.return_value = [link]

    result = runner.invoke(cli, ["polarion", "workitem", "links", "PROJ", "MP-123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["role"] == "parent"


# -- Document tests --


def test_document_get_by_uri(runner, mock_polarion_client):
    mock_polarion_client.documents.get.return_value = _make_document(
        "subterra:…", "PROJ", "_default/Specs", "spec01", "Spec 01"
    )

    result = runner.invoke(cli, ["polarion", "document", "get", "PROJ", "--uri", "subterra:…"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "spec01"


def test_document_get_by_location(runner, mock_polarion_client):
    mock_polarion_client.documents.get.return_value = _make_document(
        "subterra:…", "PROJ", "_default/Specs", "spec01", "Spec 01"
    )

    result = runner.invoke(cli, ["polarion", "document", "get", "PROJ", "--location", "_default/Specs/spec01"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["title"] == "Spec 01"


def test_document_get_missing_args(runner, mock_polarion_client):
    result = runner.invoke(cli, ["polarion", "document", "get", "PROJ"])
    assert result.exit_code != 0


def test_document_spaces(runner, mock_polarion_client):
    mock_polarion_client.documents.list_spaces.return_value = ["_default", "Design"]

    result = runner.invoke(cli, ["polarion", "document", "spaces", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == ["_default", "Design"]


def test_document_list(runner, mock_polarion_client):
    docs = [
        _make_document("u1", "PROJ", "_default", "doc1", "Doc 1"),
        _make_document("u2", "PROJ", "_default", "doc2", "Doc 2"),
    ]
    mock_polarion_client.documents.list_in_space.return_value = _make_page(docs)

    result = runner.invoke(cli, ["polarion", "document", "list", "PROJ", "_default"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2


def test_document_workitems(runner, mock_polarion_client):
    items = [_make_workitem_summary("MP-1", "WI in Doc")]
    mock_polarion_client.documents.workitems.return_value = _make_page(items)

    result = runner.invoke(cli, ["polarion", "document", "workitems", "PROJ", "--uri", "subterra:…"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 1


# -- Plan tests --


def test_plan_get(runner, mock_polarion_client):
    mock_polarion_client.plans.get.return_value = _make_plan("release-1", "Release 1.0")

    result = runner.invoke(cli, ["polarion", "plan", "get", "PROJ", "release-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "release-1"
    assert data["name"] == "Release 1.0"


def test_plan_search(runner, mock_polarion_client):
    plans = [_make_plan("r1", "Release 1"), _make_plan("r2", "Release 2")]
    mock_polarion_client.plans.search.return_value = _make_page(plans)

    result = runner.invoke(cli, ["polarion", "plan", "search", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2


def test_plan_workitems(runner, mock_polarion_client):
    items = [_make_workitem_summary("MP-10", "Plan WI")]
    mock_polarion_client.plans.workitems.return_value = _make_page(items)

    result = runner.invoke(cli, ["polarion", "plan", "workitems", "PROJ", "release-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 1


# -- Test run tests --


def test_testrun_get(runner, mock_polarion_client):
    mock_polarion_client.testruns.get.return_value = _make_testrun("TR-001", "Smoke Test")

    result = runner.invoke(cli, ["polarion", "testrun", "get", "PROJ", "TR-001"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "TR-001"
    assert data["title"] == "Smoke Test"


def test_testrun_search(runner, mock_polarion_client):
    runs = [_make_testrun("TR-1", "Run 1"), _make_testrun("TR-2", "Run 2")]
    mock_polarion_client.testruns.search.return_value = _make_page(runs)

    result = runner.invoke(cli, ["polarion", "testrun", "search", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2


def test_testrun_records(runner, mock_polarion_client):
    tr = _make_testrun("TR-001", "Smoke Test")
    mock_polarion_client.testruns.get.return_value = tr
    records = [_make_test_record("TC-1"), _make_test_record("TC-2", "failed")]
    mock_polarion_client.testruns.records.return_value = _make_page(records)

    result = runner.invoke(cli, ["polarion", "testrun", "records", "PROJ", "TR-001"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["items"]) == 2
    assert data["items"][0]["test_case_id"] == "TC-1"


# -- Health tests --


def test_health_check(runner, mock_polarion_client):
    mock_polarion_client.healthcheck.return_value = {
        "ok": True,
        "checks": {"session": True},
        "error": None,
    }

    result = runner.invoke(cli, ["polarion", "health", "check"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True


def test_health_capabilities(runner, mock_polarion_client):
    mock_polarion_client.capabilities.return_value = {
        "services": {"Project": {"getProject": True}},
    }

    result = runner.invoke(cli, ["polarion", "health", "capabilities"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "services" in data
