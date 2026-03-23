"""Jenkins client method mixins."""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote as urlquote

from agentix.core.exceptions import AgentixError


class JenkinsMethods:
    # -- Jobs --

    def get_jobs(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        if folder:
            path = f"{self._job_path(folder)}/api/json"
        else:
            path = "/api/json"
        data = self.http.get(path, params={"tree": "jobs[name,url,color]"})
        return data.get("jobs", [])

    def get_job(self, job_name: str) -> Dict[str, Any]:
        return self.http.get(f"{self._job_path(job_name)}/api/json")

    def get_job_config(self, job_name: str) -> str:
        """Get job configuration XML."""
        resp = self.http.get_raw(f"{self.http._url(self._job_path(job_name))}/config.xml")
        resp.raise_for_status()
        return resp.text

    def enable_job(self, job_name: str) -> None:
        self._post_with_crumb(f"{self._job_path(job_name)}/enable")

    def disable_job(self, job_name: str) -> None:
        self._post_with_crumb(f"{self._job_path(job_name)}/disable")

    # -- Builds --

    def trigger_build(
        self, job_name: str, params: Optional[Dict[str, str]] = None
    ) -> Optional[int]:
        """Trigger a build. Returns queue item ID if available."""
        if params:
            resp = self.http.session.post(
                self.http._url(f"{self._job_path(job_name)}/buildWithParameters"),
                data=params,
                headers=self._get_crumb(),
                timeout=self.http.timeout,
                allow_redirects=False,
            )
        else:
            resp = self.http.session.post(
                self.http._url(f"{self._job_path(job_name)}/build"),
                headers=self._get_crumb(),
                timeout=self.http.timeout,
                allow_redirects=False,
            )

        # Queue location is in the Location header
        location = resp.headers.get("Location", "")
        if "/queue/item/" in location:
            queue_id = location.rstrip("/").split("/")[-1]
            try:
                return int(queue_id)
            except ValueError:
                pass
        return None

    def get_build(
        self, job_name: str, build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        if build_number:
            path = f"{self._job_path(job_name)}/{build_number}/api/json"
        else:
            path = f"{self._job_path(job_name)}/lastBuild/api/json"
        return self.http.get(path)

    def get_build_log(
        self,
        job_name: str,
        build_number: Optional[int] = None,
        tail: Optional[int] = None,
    ) -> str:
        if build_number:
            path = f"{self._job_path(job_name)}/{build_number}/consoleText"
        else:
            path = f"{self._job_path(job_name)}/lastBuild/consoleText"
        resp = self.http.get_raw(self.http._url(path))
        resp.raise_for_status()
        text = resp.text
        if tail:
            lines = text.splitlines()
            text = "\n".join(lines[-tail:])
        return text

    def get_builds(
        self, job_name: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        data = self.http.get(
            f"{self._job_path(job_name)}/api/json",
            params={"tree": f"builds[number,url,result,timestamp,duration,displayName]{{0,{max_results}}}"},
        )
        return data.get("builds", [])

    def abort_build(self, job_name: str, build_number: int) -> None:
        self._post_with_crumb(
            f"{self._job_path(job_name)}/{build_number}/stop"
        )

    def wait_for_build(
        self,
        job_name: str,
        queue_id: int,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """Wait for a queued build to complete. Returns build info."""
        start = time.time()

        # First wait for queue item to become a build
        build_number = None
        while time.time() - start < timeout:
            try:
                queue_item = self.http.get(f"/queue/item/{queue_id}/api/json")
                executable = queue_item.get("executable")
                if executable:
                    build_number = executable.get("number")
                    break
                if queue_item.get("cancelled"):
                    return {"status": "cancelled", "queue_id": queue_id}
            except AgentixError:
                pass
            time.sleep(poll_interval)

        if build_number is None:
            return {"status": "timeout", "queue_id": queue_id, "message": "Build did not start in time"}

        # Now wait for build to complete
        while time.time() - start < timeout:
            build = self.get_build(job_name, build_number)
            if not build.get("building", True):
                return build
            time.sleep(poll_interval)

        return self.get_build(job_name, build_number)

    def get_build_artifacts(
        self, job_name: str, build_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get list of artifacts for a build."""
        if build_number:
            path = f"{self._job_path(job_name)}/{build_number}/api/json"
        else:
            path = f"{self._job_path(job_name)}/lastBuild/api/json"
        data = self.http.get(path, params={"tree": "artifacts[*]"})
        return data.get("artifacts", [])

    def download_artifact(
        self, job_name: str, artifact_path: str, build_number: Optional[int] = None
    ) -> bytes:
        """Download a build artifact into memory.

        For large artifacts, consider using download_artifact_to_file() instead.
        """
        if build_number:
            url = f"{self._job_path(job_name)}/{build_number}/artifact/{artifact_path}"
        else:
            url = f"{self._job_path(job_name)}/lastBuild/artifact/{artifact_path}"

        # Use raw HTTP get to retrieve binary content
        resp = self.http.get_raw(self.http._url(url))
        resp.raise_for_status()
        return resp.content

    def download_artifact_to_file(
        self,
        job_name: str,
        artifact_path: str,
        output_path: str,
        build_number: Optional[int] = None,
        chunk_size: int = 8192,
    ) -> None:
        """Download a build artifact directly to file using streaming.

        More memory-efficient for large artifacts than download_artifact().
        """
        if build_number:
            url = f"{self._job_path(job_name)}/{build_number}/artifact/{artifact_path}"
        else:
            url = f"{self._job_path(job_name)}/lastBuild/artifact/{artifact_path}"

        # Stream download to avoid loading entire file into memory
        resp = self.http.get_raw(self.http._url(url), stream=True)
        resp.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)

    # -- Test Results --

    def get_test_results(
        self, job_name: str, build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        if build_number:
            path = f"{self._job_path(job_name)}/{build_number}/testReport/api/json"
        else:
            path = f"{self._job_path(job_name)}/lastBuild/testReport/api/json"
        return self.http.get(path)

    def get_test_failures(
        self, job_name: str, build_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        results = self.get_test_results(job_name, build_number)
        failures = []
        for suite in results.get("suites", []):
            for case in suite.get("cases", []):
                if case.get("status") in ("FAILED", "REGRESSION"):
                    failures.append(case)
        return failures

    # -- Pipeline --

    def get_pipeline_stages(
        self, job_name: str, build_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get pipeline stages via workflow API."""
        if build_number:
            path = f"{self._job_path(job_name)}/{build_number}/wfapi/describe"
        else:
            path = f"{self._job_path(job_name)}/lastBuild/wfapi/describe"
        data = self.http.get(path)
        return data.get("stages", [])

    def get_stage_log(
        self,
        job_name: str,
        stage_id: str,
        build_number: Optional[int] = None,
    ) -> str:
        """Get log for a specific pipeline stage."""
        if build_number:
            path = f"{self._job_path(job_name)}/{build_number}/execution/node/{stage_id}/wfapi/log"
        else:
            path = f"{self._job_path(job_name)}/lastBuild/execution/node/{stage_id}/wfapi/log"
        data = self.http.get(path)
        return data.get("text", "")

    # -- Queue --

    def get_queue(self) -> List[Dict[str, Any]]:
        data = self.http.get("/queue/api/json")
        return data.get("items", [])

    def cancel_queue_item(self, queue_id: int) -> None:
        self._post_with_crumb("/queue/cancelItem", data={"id": queue_id})

    # -- Nodes --

    def get_nodes(self) -> List[Dict[str, Any]]:
        data = self.http.get(
            "/computer/api/json",
            params={"tree": "computer[displayName,offline,temporarilyOffline,idle,numExecutors]"},
        )
        return data.get("computer", [])

    def get_node(self, node_name: str) -> Dict[str, Any]:
        name = "(built-in)" if node_name.lower() in ("master", "built-in") else node_name
        return self.http.get(f"/computer/{urlquote(name, safe='')}/api/json")
