"""Response normalization for Jenkins API data."""

from typing import Any, Dict


def normalize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": job.get("name", job.get("displayName", "")),
        "url": job.get("url", ""),
        "color": job.get("color", ""),
        "buildable": job.get("buildable", True),
    }


def normalize_job_detail(job: Dict[str, Any]) -> Dict[str, Any]:
    last_build = job.get("lastBuild") or {}
    last_successful = job.get("lastSuccessfulBuild") or {}
    last_failed = job.get("lastFailedBuild") or {}
    return {
        "name": job.get("name", job.get("displayName", "")),
        "url": job.get("url", ""),
        "color": job.get("color", ""),
        "buildable": job.get("buildable", True),
        "lastBuild": last_build.get("number"),
        "lastSuccessfulBuild": last_successful.get("number"),
        "lastFailedBuild": last_failed.get("number"),
        "inQueue": job.get("inQueue", False),
    }


def normalize_build(build: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "number": build.get("number", ""),
        "result": build.get("result", ""),
        "building": build.get("building", False),
        "displayName": build.get("displayName", ""),
        "duration": build.get("duration", 0),
        "timestamp": build.get("timestamp", 0),
        "url": build.get("url", ""),
    }


def normalize_build_brief(build: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "number": build.get("number", ""),
        "result": build.get("result", ""),
        "displayName": build.get("displayName", ""),
        "duration": build.get("duration", 0),
    }


def normalize_test_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "totalCount": result.get("totalCount", 0),
        "failCount": result.get("failCount", 0),
        "skipCount": result.get("skipCount", 0),
        "passCount": result.get("passCount", 0),
        "duration": result.get("duration", 0),
    }


def normalize_test_case(case: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": case.get("name", ""),
        "className": case.get("className", ""),
        "status": case.get("status", ""),
        "duration": case.get("duration", 0),
        "errorDetails": case.get("errorDetails", ""),
        "errorStackTrace": case.get("errorStackTrace", ""),
    }


def normalize_stage(stage: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": stage.get("id", ""),
        "name": stage.get("name", ""),
        "status": stage.get("status", ""),
        "durationMillis": stage.get("durationMillis", 0),
    }


def normalize_queue_item(item: Dict[str, Any]) -> Dict[str, Any]:
    task = item.get("task", {})
    return {
        "id": item.get("id", ""),
        "task": task.get("name", ""),
        "url": task.get("url", ""),
        "why": item.get("why", ""),
        "inQueueSince": item.get("inQueueSince", 0),
    }


def normalize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": node.get("displayName", ""),
        "offline": node.get("offline", False),
        "temporarilyOffline": node.get("temporarilyOffline", False),
        "idle": node.get("idle", True),
        "numExecutors": node.get("numExecutors", 0),
    }


def normalize_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a Jenkins build artifact."""
    return {
        "fileName": artifact.get("fileName", ""),
        "displayPath": artifact.get("displayPath", ""),
        "relativePath": artifact.get("relativePath", ""),
    }


def normalize_change(change: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a Jenkins build changelog entry."""
    author = change.get("author", {})
    return {
        "id": change.get("commitId", ""),
        "author": author.get("fullName", ""),
        "message": change.get("msg", ""),
        "affectedPaths": change.get("affectedPaths", []),
    }
