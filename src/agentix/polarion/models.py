"""Response normalization for Polarion API data."""

from typing import Any, Dict, Optional


def _enum_ref(ref: Any) -> Optional[Dict[str, str]]:
    """Normalize an EnumRef dataclass to a dict."""
    if ref is None:
        return None
    return {"id": ref.id, "name": ref.name}


def _user_ref(ref: Any) -> Optional[Dict[str, str]]:
    """Normalize a UserRef dataclass to a dict."""
    if ref is None:
        return None
    return {"id": ref.id, "name": ref.name}


def _link(link: Any) -> Dict[str, str]:
    """Normalize a Link dataclass to a dict."""
    return {
        "role": link.role,
        "target_id": link.target_id,
        "target_uri": link.target_uri,
    }


def _attachment(att: Any) -> Dict[str, Any]:
    """Normalize an AttachmentMeta dataclass to a dict."""
    return {
        "id": att.id,
        "file_name": att.file_name,
        "title": att.title,
        "url": att.url,
    }


def normalize_project(project: Any) -> Dict[str, Any]:
    """Normalize a Project dataclass to a dict."""
    return {
        "id": project.id,
        "name": project.name,
        "tracker_prefix": project.tracker_prefix,
    }


def normalize_workitem_summary(wi: Any) -> Dict[str, Any]:
    """Normalize a WorkitemSummary dataclass to a dict."""
    return {
        "id": wi.id,
        "uri": wi.uri,
        "title": wi.title,
        "type": _enum_ref(wi.type),
        "status": _enum_ref(wi.status),
        "priority": _enum_ref(wi.priority),
    }


def normalize_workitem_detail(wi: Any) -> Dict[str, Any]:
    """Normalize a WorkitemDetail dataclass to a dict."""
    return {
        "id": wi.id,
        "uri": wi.uri,
        "title": wi.title,
        "type": _enum_ref(wi.type),
        "status": _enum_ref(wi.status),
        "priority": _enum_ref(wi.priority),
        "description_html": wi.description_html,
        "author": _user_ref(wi.author),
        "assignees": [_user_ref(a) for a in wi.assignees],
        "approvers": [_user_ref(a) for a in wi.approvers],
        "links": [_link(lnk) for lnk in wi.links],
        "attachments": [_attachment(a) for a in wi.attachments],
        "custom_fields": wi.custom_fields,
        "created_at": str(wi.created_at) if wi.created_at else None,
        "updated_at": str(wi.updated_at) if wi.updated_at else None,
    }


def normalize_document(doc: Any) -> Dict[str, Any]:
    """Normalize a Document dataclass to a dict."""
    return {
        "uri": doc.uri,
        "project_id": doc.project_id,
        "location": doc.location,
        "name": doc.name,
        "title": doc.title,
        "status": _enum_ref(doc.status),
        "type": _enum_ref(doc.type),
    }


def normalize_plan(plan: Any) -> Dict[str, Any]:
    """Normalize a Plan dataclass to a dict."""
    return {
        "id": plan.id,
        "uri": plan.uri,
        "name": plan.name,
        "status": _enum_ref(plan.status),
        "start_date": str(plan.start_date) if plan.start_date else None,
        "due_date": str(plan.due_date) if plan.due_date else None,
    }


def normalize_testrun(tr: Any) -> Dict[str, Any]:
    """Normalize a TestRun dataclass to a dict."""
    return {
        "id": tr.id,
        "uri": tr.uri,
        "title": tr.title,
        "is_template": tr.is_template,
        "status": _enum_ref(tr.status),
        "created_at": str(tr.created_at) if tr.created_at else None,
    }


def normalize_test_record(rec: Any) -> Dict[str, Any]:
    """Normalize a TestRecord dataclass to a dict."""
    return {
        "test_case_id": rec.test_case_id,
        "result": rec.result,
        "duration_ms": rec.duration_ms,
        "comment": rec.comment,
    }


def normalize_user(user: Any) -> Dict[str, Any]:
    """Normalize a User dataclass to a dict."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


def normalize_page(page: Any, normalizer: Any) -> Dict[str, Any]:
    """Normalize a Page result with items + pagination metadata."""
    return {
        "items": [normalizer(item) for item in page.items],
        "total": page.total,
        "offset": page.offset,
        "limit": page.limit,
        "has_more": page.has_more,
    }
