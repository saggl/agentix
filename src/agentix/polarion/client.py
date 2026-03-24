"""Polarion SOAP API client wrapper."""

from typing import Any, Dict, List, Optional

from polarion import Polarion


class PolarionClient:
    """Wrapper around polarion-api that returns plain dicts."""

    def __init__(self, base_url: str, username: str, token: str, auth_type: str = "token"):
        kwargs: Dict[str, Any] = {}
        if auth_type == "password":
            kwargs["password"] = token
        else:
            kwargs["token"] = token

        self._polarion = Polarion(base_url, username, **kwargs)

    def close(self) -> None:
        self._polarion.close()

    # -- Projects --

    def get_project(self, project_id: str) -> Dict[str, Any]:
        project = self._polarion.get_project(project_id)
        return {
            "id": project.id,
            "name": project.name,
            "tracker_prefix": project.tracker_prefix,
        }

    def get_project_users(self, project_id: str) -> List[Dict[str, Any]]:
        project = self._polarion.get_project(project_id)
        users = project.get_users()
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": getattr(u, "email", ""),
            }
            for u in users
        ]

    # -- Work Items --

    def get_workitem(self, project_id: str, workitem_id: str) -> Dict[str, Any]:
        project = self._polarion.get_project(project_id)
        wi = project.get_workitem(workitem_id)
        return self._workitem_to_dict(wi)

    def search_workitems(
        self,
        project_id: str,
        query: str = "",
        order: str = "Created",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        project = self._polarion.get_project(project_id)
        workitems = project.search_workitems_full(query, order, limit)
        return [self._workitem_to_dict(wi) for wi in workitems]

    def create_workitem(
        self,
        project_id: str,
        workitem_type: str,
        fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        project = self._polarion.get_project(project_id)
        wi = project.create_workitem(workitem_type, fields)
        return self._workitem_to_dict(wi)

    def delete_workitem(self, project_id: str, workitem_id: str) -> None:
        project = self._polarion.get_project(project_id)
        wi = project.get_workitem(workitem_id)
        wi.delete()

    def get_workitem_actions(self, project_id: str, workitem_id: str) -> List[Dict[str, Any]]:
        project = self._polarion.get_project(project_id)
        wi = project.get_workitem(workitem_id)
        return wi.get_available_actions_details()

    def perform_workitem_action(self, project_id: str, workitem_id: str, action_name: str) -> None:
        project = self._polarion.get_project(project_id)
        wi = project.get_workitem(workitem_id)
        wi.perform_action(action_name)

    # -- Documents --

    def get_document(self, project_id: str, location: str) -> Dict[str, Any]:
        project = self._polarion.get_project(project_id)
        doc = project.get_document(location)
        return self._document_to_dict(doc)

    def get_document_spaces(self, project_id: str) -> List[str]:
        project = self._polarion.get_project(project_id)
        return project.get_document_spaces()

    def get_documents_in_space(self, project_id: str, space: str) -> List[Dict[str, Any]]:
        project = self._polarion.get_project(project_id)
        docs = project.get_documents_in_space(space)
        return [self._document_to_dict(d) for d in docs]

    # -- Test Runs --

    def get_testrun(self, project_id: str, testrun_id: str) -> Dict[str, Any]:
        project = self._polarion.get_project(project_id)
        tr = project.get_test_run(testrun_id)
        return self._testrun_to_dict(tr)

    def search_testruns(
        self,
        project_id: str,
        query: str = "",
        order: str = "Created",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        project = self._polarion.get_project(project_id)
        testruns = project.search_test_runs(query, order, limit)
        return [self._testrun_to_dict(tr) for tr in testruns]

    # -- Plans --

    def get_plan(self, project_id: str, plan_id: str) -> Dict[str, Any]:
        project = self._polarion.get_project(project_id)
        plan = project.get_plan(plan_id)
        return self._plan_to_dict(plan)

    def search_plans(
        self,
        project_id: str,
        query: str = "",
        order: str = "Created",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        project = self._polarion.get_project(project_id)
        plans = project.search_plans_full(query, order, limit)
        return [self._plan_to_dict(p) for p in plans]

    # -- Enums --

    def get_enum(self, project_id: str, enum_name: str) -> List[str]:
        project = self._polarion.get_project(project_id)
        return project.get_enum(enum_name)

    # -- Helpers --

    @staticmethod
    def _extract_id(val: Any) -> str:
        if isinstance(val, dict):
            return val.get("id", "")
        return str(val) if val else ""

    @classmethod
    def _workitem_to_dict(cls, wi: Any) -> Dict[str, Any]:
        return {
            "id": wi._id,
            "title": wi.title or "",
            "type": cls._extract_id(wi.type),
            "status": cls._extract_id(wi.status),
            "priority": cls._extract_id(wi.priority),
            "severity": cls._extract_id(wi.severity),
            "created": str(wi.created) if wi.created else "",
            "updated": str(wi.updated) if wi.updated else "",
            "description": wi.get_description() or "",
        }

    @staticmethod
    def _document_to_dict(doc: Any) -> Dict[str, Any]:
        return {
            "title": doc.title or "",
            "module_name": doc.moduleName or "",
            "module_folder": doc.moduleFolder or "",
        }

    @staticmethod
    def _testrun_to_dict(tr: Any) -> Dict[str, Any]:
        return {
            "id": tr.id or "",
            "title": tr.title or "",
            "created": str(tr.created) if tr.created else "",
            "is_template": tr.isTemplate if tr.isTemplate is not None else False,
        }

    @staticmethod
    def _plan_to_dict(plan: Any) -> Dict[str, Any]:
        return {
            "id": plan.id or "",
            "name": plan.name or "",
            "start_date": str(plan.startDate) if plan.startDate else "",
            "due_date": str(plan.dueDate) if plan.dueDate else "",
        }
