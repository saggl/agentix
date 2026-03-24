"""Response normalization for Polarion API data."""

from typing import Any, Dict, List


def normalize_workitem(wi: Dict[str, Any]) -> Dict[str, Any]:
    return wi


def normalize_workitem_brief(wi: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": wi.get("id", ""),
        "title": wi.get("title", ""),
        "type": wi.get("type", ""),
        "status": wi.get("status", ""),
    }


def normalize_project(project: Dict[str, Any]) -> Dict[str, Any]:
    return project


def normalize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return user


def normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    return doc


def normalize_testrun(tr: Dict[str, Any]) -> Dict[str, Any]:
    return tr


def normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    return plan


def normalize_action(action: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "action_id": action.get("actionId", ""),
        "native_action_id": action.get("nativeActionId", ""),
        "action_name": action.get("actionName", ""),
    }
