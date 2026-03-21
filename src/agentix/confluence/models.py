"""Response normalization for Confluence API data."""

import re
from typing import Any, Dict


def _strip_html(html: str) -> str:
    """Minimal HTML tag stripping for preview text."""
    if not html:
        return ""
    return re.sub(r"<[^>]+>", "", html).strip()


def normalize_page(page: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a Confluence page (v2 API)."""
    body_val = ""
    body = page.get("body", {})
    if isinstance(body, dict):
        storage = body.get("storage", body.get("view", {}))
        if isinstance(storage, dict):
            body_val = storage.get("value", "")

    return {
        "id": page.get("id", ""),
        "title": page.get("title", ""),
        "status": page.get("status", ""),
        "spaceId": page.get("spaceId", ""),
        "version": page.get("version", {}).get("number", ""),
        "body": body_val,
    }


def normalize_page_brief(page: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal page representation for lists."""
    # Handle v1 search results which have different structure
    content = page.get("content", page)
    return {
        "id": content.get("id", page.get("id", "")),
        "title": content.get("title", page.get("title", "")),
        "status": content.get("status", page.get("status", "")),
        "type": content.get("type", page.get("type", "")),
    }


def normalize_space(space: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": space.get("id", ""),
        "key": space.get("key", ""),
        "name": space.get("name", ""),
        "type": space.get("type", ""),
        "status": space.get("status", ""),
    }


def normalize_comment(comment: Dict[str, Any]) -> Dict[str, Any]:
    body_val = ""
    body = comment.get("body", {})
    if isinstance(body, dict):
        storage = body.get("storage", body.get("view", {}))
        if isinstance(storage, dict):
            body_val = storage.get("value", "")

    return {
        "id": comment.get("id", ""),
        "body": _strip_html(body_val),
        "version": comment.get("version", {}).get("number", ""),
        "createdAt": comment.get("createdAt", ""),
    }


def normalize_attachment(att: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": att.get("id", ""),
        "title": att.get("title", ""),
        "mediaType": att.get("mediaType", ""),
        "fileSize": att.get("fileSize", 0),
        "status": att.get("status", ""),
    }
