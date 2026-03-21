"""Response normalization for Jira API data."""

from typing import Any, Dict


def _extract_text(adf_body: Any) -> str:
    """Extract plain text from Atlassian Document Format body."""
    if not adf_body or not isinstance(adf_body, dict):
        return ""
    parts = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []):
                _walk(child)
        elif isinstance(node, list):
            for child in node:
                _walk(child)

    _walk(adf_body)
    return " ".join(parts)


def normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Jira issue into a clean dict."""
    fields = issue.get("fields", {})
    return {
        "key": issue.get("key", ""),
        "id": issue.get("id", ""),
        "summary": fields.get("summary", ""),
        "status": _nested_name(fields, "status"),
        "type": _nested_name(fields, "issuetype"),
        "priority": _nested_name(fields, "priority"),
        "assignee": _nested_display(fields, "assignee"),
        "reporter": _nested_display(fields, "reporter"),
        "labels": fields.get("labels", []),
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
        "description": _extract_text(fields.get("description")),
    }


def normalize_issue_brief(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal issue representation for lists."""
    fields = issue.get("fields", {})
    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "status": _nested_name(fields, "status"),
        "type": _nested_name(fields, "issuetype"),
        "priority": _nested_name(fields, "priority"),
        "assignee": _nested_display(fields, "assignee"),
    }


def normalize_comment(comment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": comment.get("id", ""),
        "author": _nested_display_direct(comment, "author"),
        "body": _extract_text(comment.get("body")),
        "created": comment.get("created", ""),
        "updated": comment.get("updated", ""),
    }


def normalize_attachment(att: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": att.get("id", ""),
        "filename": att.get("filename", ""),
        "size": att.get("size", 0),
        "mimeType": att.get("mimeType", ""),
        "author": _nested_display_direct(att, "author"),
        "created": att.get("created", ""),
    }


def normalize_sprint(sprint: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": sprint.get("id", ""),
        "name": sprint.get("name", ""),
        "state": sprint.get("state", ""),
        "startDate": sprint.get("startDate", ""),
        "endDate": sprint.get("endDate", ""),
        "goal": sprint.get("goal", ""),
    }


def normalize_board(board: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": board.get("id", ""),
        "name": board.get("name", ""),
        "type": board.get("type", ""),
    }


def normalize_project(project: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "key": project.get("key", ""),
        "name": project.get("name", ""),
        "id": project.get("id", ""),
        "style": project.get("style", ""),
    }


def normalize_transition(t: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": t.get("id", ""),
        "name": t.get("name", ""),
        "to": t.get("to", {}).get("name", ""),
    }


def _nested_name(fields: Dict, key: str) -> str:
    val = fields.get(key)
    if isinstance(val, dict):
        return val.get("name", "")
    return str(val) if val else ""


def _nested_display(fields: Dict, key: str) -> str:
    val = fields.get(key)
    if isinstance(val, dict):
        return val.get("displayName", val.get("name", ""))
    return str(val) if val else ""


def _nested_display_direct(data: Dict, key: str) -> str:
    val = data.get(key)
    if isinstance(val, dict):
        return val.get("displayName", val.get("name", ""))
    return str(val) if val else ""
