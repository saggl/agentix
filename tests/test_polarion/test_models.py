"""Tests for Polarion model normalization."""

from unittest.mock import MagicMock

from agentix.polarion.models import (
    normalize_document,
    normalize_page,
    normalize_plan,
    normalize_project,
    normalize_test_record,
    normalize_testrun,
    normalize_user,
    normalize_workitem_detail,
    normalize_workitem_summary,
)


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


def test_normalize_project():
    proj = MagicMock()
    proj.id = "MY_PROJECT"
    proj.name = "My Project"
    proj.tracker_prefix = "MP"

    result = normalize_project(proj)
    assert result == {"id": "MY_PROJECT", "name": "My Project", "tracker_prefix": "MP"}


def test_normalize_workitem_summary():
    wi = MagicMock()
    wi.id = "MP-123"
    wi.uri = "subterra:data-service:objects:…"
    wi.title = "Test Item"
    wi.type = _make_enum_ref("task", "Task")
    wi.status = _make_enum_ref("open", "Open")
    wi.priority = _make_enum_ref("high", "High")

    result = normalize_workitem_summary(wi)
    assert result["id"] == "MP-123"
    assert result["title"] == "Test Item"
    assert result["type"] == {"id": "task", "name": "Task"}
    assert result["status"] == {"id": "open", "name": "Open"}


def test_normalize_workitem_detail():
    wi = MagicMock()
    wi.id = "MP-456"
    wi.uri = "subterra:…"
    wi.title = "Detail Item"
    wi.type = _make_enum_ref("requirement")
    wi.status = _make_enum_ref("approved")
    wi.priority = None
    wi.description_html = "<p>Hello</p>"
    wi.author = _make_user_ref("admin", "Admin User")
    wi.assignees = [_make_user_ref("dev1")]
    wi.approvers = []
    link = MagicMock()
    link.role = "parent"
    link.target_id = "MP-100"
    link.target_uri = "subterra:…"
    wi.links = [link]
    wi.attachments = []
    wi.custom_fields = {"cf_team": "Alpha"}
    wi.created_at = None
    wi.updated_at = None

    result = normalize_workitem_detail(wi)
    assert result["id"] == "MP-456"
    assert result["description_html"] == "<p>Hello</p>"
    assert result["author"] == {"id": "admin", "name": "Admin User"}
    assert len(result["links"]) == 1
    assert result["links"][0]["role"] == "parent"
    assert result["custom_fields"] == {"cf_team": "Alpha"}


def test_normalize_document():
    doc = MagicMock()
    doc.uri = "subterra:…"
    doc.project_id = "PROJ"
    doc.location = "_default/Specs"
    doc.name = "spec01"
    doc.title = "Spec 01"
    doc.status = _make_enum_ref("draft")
    doc.type = None

    result = normalize_document(doc)
    assert result["project_id"] == "PROJ"
    assert result["name"] == "spec01"
    assert result["type"] is None


def test_normalize_plan():
    plan = MagicMock()
    plan.id = "release-1.0"
    plan.uri = "subterra:…"
    plan.name = "Release 1.0"
    plan.status = _make_enum_ref("open")
    plan.start_date = None
    plan.due_date = None

    result = normalize_plan(plan)
    assert result["id"] == "release-1.0"
    assert result["name"] == "Release 1.0"


def test_normalize_testrun():
    tr = MagicMock()
    tr.id = "TR-001"
    tr.uri = "subterra:…"
    tr.title = "Smoke Test"
    tr.is_template = False
    tr.status = _make_enum_ref("passed")
    tr.created_at = None

    result = normalize_testrun(tr)
    assert result["id"] == "TR-001"
    assert result["is_template"] is False


def test_normalize_test_record():
    rec = MagicMock()
    rec.test_case_id = "TC-001"
    rec.result = "passed"
    rec.duration_ms = 1200
    rec.comment = "All good"

    result = normalize_test_record(rec)
    assert result == {
        "test_case_id": "TC-001",
        "result": "passed",
        "duration_ms": 1200,
        "comment": "All good",
    }


def test_normalize_user():
    user = MagicMock()
    user.id = "jdoe"
    user.name = "John Doe"

    result = normalize_user(user)
    assert result == {"id": "jdoe", "name": "John Doe"}


def test_normalize_page():
    page = MagicMock()
    item1 = MagicMock()
    item1.id = "P1"
    item1.name = "Project 1"
    item1.tracker_prefix = None
    item2 = MagicMock()
    item2.id = "P2"
    item2.name = "Project 2"
    item2.tracker_prefix = "P2"
    page.items = [item1, item2]
    page.total = 2
    page.offset = 0
    page.limit = 100
    page.has_more = False

    result = normalize_page(page, normalize_project)
    assert len(result["items"]) == 2
    assert result["total"] == 2
    assert result["has_more"] is False
